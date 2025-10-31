import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import tempfile
import shutil

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.chains import ConversationalRetrievalChain


class DevOpsKnowledgeBase:
    def __init__(self, knowledge_base_path: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.embedding_model_name = embedding_model
        self.embedding_model = None
        self.vectorstore = None
        self.documents = []
        self.chunks = []
        self.temp_db_dir = None
        self.indices = {}
        self.structure = {}

    def _parse_structured_content(self, content: str, file_path: Path) -> dict:
        metadata = {}

        try:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                import yaml
                data = yaml.safe_load(content)
                if isinstance(data, dict):
                    metadata['kind'] = data.get('kind')
                    metadata['api_version'] = data.get('apiVersion')

                    if 'metadata' in data and isinstance(data['metadata'], dict):
                        for key, value in data['metadata'].items():
                            if isinstance(value, (str, int, float, bool)):
                                metadata[f'meta_{key}'] = value
                            elif isinstance(value, dict):
                                for k, v in value.items():
                                    if isinstance(v, (str, int, float, bool)):
                                        metadata[f'meta_{key}_{k}'] = v

                    if 'spec' in data and isinstance(data['spec'], dict):
                        if 'project' in data['spec']:
                            metadata['project'] = data['spec']['project']
                        if 'destination' in data['spec'] and isinstance(data['spec']['destination'], dict):
                            if 'namespace' in data['spec']['destination']:
                                metadata['namespace'] = data['spec']['destination']['namespace']

            elif file_path.suffix.lower() == '.json':
                data = json.loads(content)
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, (str, int, float, bool)):
                            metadata[f'json_{key}'] = value

            elif file_path.suffix.lower() in ['.tf', '.hcl']:
                metadata['is_terraform'] = True
                resources = re.findall(r'resource\s+"([^"]+)"\s+"([^"]+)"', content)
                if resources:
                    metadata['terraform_resources'] = [r[0] for r in resources]
                    metadata['resource_count'] = len(resources)

                modules = re.findall(r'module\s+"([^"]+)"', content)
                if modules:
                    metadata['terraform_modules'] = modules
                    metadata['module_count'] = len(modules)

            elif file_path.suffix.lower() == '.py':
                metadata['is_code'] = True
                metadata['language'] = 'python'

                imports = re.findall(r'^(?:from|import)\s+(\S+)', content, re.MULTILINE)
                classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
                functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)

                if imports:
                    metadata['imports'] = imports[:10]
                if classes:
                    metadata['classes'] = classes
                    metadata['class_count'] = len(classes)
                if functions:
                    metadata['functions'] = functions[:20]
                    metadata['function_count'] = len(functions)

            elif file_path.suffix.lower() in ['.js', '.ts']:
                metadata['is_code'] = True
                metadata['language'] = 'javascript' if file_path.suffix == '.js' else 'typescript'

                imports = re.findall(r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]', content)
                functions = re.findall(r'(?:function|const|let|var)\s+(\w+)\s*=?\s*(?:async\s*)?\(', content)
                classes = re.findall(r'class\s+(\w+)', content)

                if imports:
                    metadata['imports'] = imports[:10]
                if classes:
                    metadata['classes'] = classes
                    metadata['class_count'] = len(classes)
                if functions:
                    metadata['function_count'] = len(functions)

            elif file_path.suffix.lower() in ['.go']:
                metadata['is_code'] = True
                metadata['language'] = 'go'

                packages = re.findall(r'package\s+(\w+)', content)
                if packages:
                    metadata['package'] = packages[0]

                imports = re.findall(r'import\s+[\'"]([^\'"]+)[\'"]', content)
                if imports:
                    metadata['imports'] = imports[:10]

        except Exception as e:
            pass

        return metadata

    def _extract_content_patterns(self, content: str) -> dict:
        metadata = {}
        content_lower = content.lower()

        urls = re.findall(r'https?://[^\s<>"]+', content)
        if urls:
            metadata['has_urls'] = True
            metadata['url_count'] = len(urls)
            domains = []
            for url in urls:
                domain_match = re.findall(r'https?://([^/]+)', url)
                if domain_match:
                    domains.append(domain_match[0])
            if domains:
                metadata['domains'] = list(set(domains))[:5]

        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', content)
        if ips:
            metadata['has_ips'] = True
            metadata['ip_count'] = len(set(ips))

        versions = re.findall(r'\bv?\d+\.\d+(?:\.\d+)?(?:-[\w.]+)?\b', content)
        if versions:
            metadata['has_versions'] = True

        patterns = {
            'has_secrets': any(keyword in content_lower for keyword in ['password', 'secret', 'token', 'api_key', 'apikey']),
            'has_monitoring': any(keyword in content_lower for keyword in ['prometheus', 'grafana', 'metrics', 'alert']),
            'has_networking': any(keyword in content_lower for keyword in ['ingress', 'service', 'loadbalancer', 'route']),
            'has_storage': any(keyword in content_lower for keyword in ['volume', 'pvc', 'storage', 'disk']),
            'has_database': any(keyword in content_lower for keyword in ['postgres', 'mysql', 'redis', 'mongodb', 'database']),
            'has_deployment': any(keyword in content_lower for keyword in ['deployment', 'statefulset', 'daemonset', 'replica']),
        }

        metadata.update({k: v for k, v in patterns.items() if v})

        quoted_strings = re.findall(r'"([^"]{3,30})"', content)
        if quoted_strings:
            metadata['quoted_strings'] = list(set(quoted_strings))[:10]

        return metadata

    def load_documents(self) -> List[Document]:
        self.documents = []

        if not self.knowledge_base_path.exists():
            raise ValueError(f"Knowledge base path does not exist: {self.knowledge_base_path}")

        supported_extensions = {'.yaml', '.yml', '.md', '.txt', '.json', '.tf', '.hcl', '.py', '.js', '.ts', '.go', '.sh', '.rst'}

        print(f"Loading documents from {self.knowledge_base_path}...")

        for file_path in self.knowledge_base_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().strip()

                    if content and len(content) > 50:
                        relative_path = file_path.relative_to(self.knowledge_base_path)
                        parts = relative_path.parts

                        metadata = {
                            "source": str(relative_path),
                            "file_type": file_path.suffix.lower(),
                            "path": str(file_path),
                            "filename": file_path.stem,
                            "full_filename": file_path.name,
                            "char_count": len(content),
                            "word_count": len(content.split()),
                            "line_count": len(content.splitlines()),
                            "depth": len(parts) - 1,
                            "parent_dir": parts[-2] if len(parts) > 1 else "root",
                            "path_level_0": parts[0] if len(parts) > 0 else None,
                            "path_level_1": parts[1] if len(parts) > 1 else None,
                            "path_level_2": parts[2] if len(parts) > 2 else None,
                            "path_level_3": parts[3] if len(parts) > 3 else None,
                            "full_path_parts": list(parts),
                        }

                        metadata.update(self._parse_structured_content(content, file_path))
                        metadata.update(self._extract_content_patterns(content))

                        doc = Document(page_content=content, metadata=metadata)
                        self.documents.append(doc)

                except Exception as e:
                    print(f"Skipped {file_path.name}: {str(e)}")

        print(f"Loaded {len(self.documents)} documents")
        return self.documents

    def discover_structure(self) -> dict:
        print("\nAuto-discovering repository structure...")

        structure = {
            'total_files': len(self.documents),
            'by_file_type': {},
            'by_depth': {},
            'by_parent_dir': {},
            'hierarchy': {},
            'patterns': {}
        }

        for doc in self.documents:
            file_type = doc.metadata.get('file_type', 'unknown')
            structure['by_file_type'][file_type] = structure['by_file_type'].get(file_type, 0) + 1

            depth = doc.metadata.get('depth', 0)
            structure['by_depth'][depth] = structure['by_depth'].get(depth, 0) + 1

            parent = doc.metadata.get('parent_dir', 'unknown')
            structure['by_parent_dir'][parent] = structure['by_parent_dir'].get(parent, 0) + 1

            path_parts = doc.metadata.get('full_path_parts', [])
            current_level = structure['hierarchy']
            for part in path_parts[:-1]:
                if part not in current_level:
                    current_level[part] = {'_count': 0, '_children': {}}
                current_level[part]['_count'] += 1
                current_level = current_level[part]['_children']

        structure['patterns'] = self._detect_patterns()

        print(f"\nDiscovered Structure:")
        print(f"  Total files: {structure['total_files']}")
        print(f"\n  By file type:")
        for ftype, count in sorted(structure['by_file_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"    {ftype}: {count}")

        print(f"\n  By depth:")
        for depth, count in sorted(structure['by_depth'].items()):
            print(f"    Level {depth}: {count} files")

        print(f"\n  Top-level directories:")
        for dir_name, data in structure['hierarchy'].items():
            print(f"    {dir_name}/: {data['_count']} files")

        if structure['patterns']:
            print(f"\n  Detected patterns:")
            for pattern, count in structure['patterns'].items():
                print(f"    {pattern}: {count} files")

        self.structure = structure
        return structure

    def _detect_patterns(self) -> dict:
        patterns = {
            'kubernetes_manifests': 0,
            'terraform_files': 0,
            'python_code': 0,
            'javascript_code': 0,
            'documentation': 0,
            'configuration': 0,
        }

        for doc in self.documents:
            if doc.metadata.get('kind') or doc.metadata.get('api_version'):
                patterns['kubernetes_manifests'] += 1
            if doc.metadata.get('is_terraform'):
                patterns['terraform_files'] += 1
            if doc.metadata.get('language') == 'python':
                patterns['python_code'] += 1
            if doc.metadata.get('language') in ['javascript', 'typescript']:
                patterns['javascript_code'] += 1
            if doc.metadata.get('file_type') in ['.md', '.rst', '.txt']:
                patterns['documentation'] += 1
            if doc.metadata.get('file_type') in ['.yaml', '.yml', '.json', '.toml']:
                patterns['configuration'] += 1

        return {k: v for k, v in patterns.items() if v > 0}

    def create_dynamic_indices(self) -> dict:
        print("\nCreating dynamic indices...")

        indices = {
            'by_path_level_0': {},
            'by_path_level_1': {},
            'by_path_level_2': {},
            'by_path_level_3': {},
            'by_file_type': {},
            'by_kind': {},
            'by_language': {},
            'by_parent_dir': {},
            'by_project': {},
            'by_namespace': {},
            'statistics': {
                'total_documents': len(self.documents),
                'total_chars': sum(d.metadata.get('char_count', 0) for d in self.documents),
                'total_lines': sum(d.metadata.get('line_count', 0) for d in self.documents),
            }
        }

        for doc in self.documents:
            source = doc.metadata.get('source')

            for level in range(4):
                level_key = f'path_level_{level}'
                index_key = f'by_{level_key}'
                if level_value := doc.metadata.get(level_key):
                    if level_value not in indices[index_key]:
                        indices[index_key][level_value] = []
                    indices[index_key][level_value].append(source)

            if file_type := doc.metadata.get('file_type'):
                if file_type not in indices['by_file_type']:
                    indices['by_file_type'][file_type] = []
                indices['by_file_type'][file_type].append(source)

            if kind := doc.metadata.get('kind'):
                if kind not in indices['by_kind']:
                    indices['by_kind'][kind] = []
                indices['by_kind'][kind].append(source)

            if language := doc.metadata.get('language'):
                if language not in indices['by_language']:
                    indices['by_language'][language] = []
                indices['by_language'][language].append(source)

            if parent := doc.metadata.get('parent_dir'):
                if parent not in indices['by_parent_dir']:
                    indices['by_parent_dir'][parent] = []
                indices['by_parent_dir'][parent].append(source)

            if project := doc.metadata.get('project'):
                if project not in indices['by_project']:
                    indices['by_project'][project] = []
                indices['by_project'][project].append(source)

            if namespace := doc.metadata.get('namespace'):
                if namespace not in indices['by_namespace']:
                    indices['by_namespace'][namespace] = []
                indices['by_namespace'][namespace].append(source)

        self.indices = indices

        print(f"\nIndices Created:")
        print(f"  Total documents indexed: {indices['statistics']['total_documents']}")
        print(f"  Top-level paths: {len(indices['by_path_level_0'])}")
        print(f"  File types: {len(indices['by_file_type'])}")
        if indices['by_kind']:
            print(f"  Kubernetes kinds: {len(indices['by_kind'])}")
        if indices['by_language']:
            print(f"  Programming languages: {len(indices['by_language'])}")

        return indices

    def chunk_documents_adaptive(self, documents: List[Document]) -> List[Document]:
        print("\nAdaptive chunking based on file characteristics...")

        all_chunks = []

        strategies = {
            'small_structured': [],
            'large_structured': [],
            'code_files': [],
            'documentation': [],
            'default': []
        }

        for doc in documents:
            char_count = doc.metadata.get('char_count', 0)
            file_type = doc.metadata.get('file_type', '')

            if file_type in ['.yaml', '.yml', '.json', '.toml']:
                if char_count < 2000:
                    strategies['small_structured'].append(doc)
                else:
                    strategies['large_structured'].append(doc)
            elif file_type in ['.py', '.js', '.go', '.java', '.ts', '.rs', '.sh']:
                strategies['code_files'].append(doc)
            elif file_type in ['.md', '.rst', '.txt']:
                strategies['documentation'].append(doc)
            else:
                strategies['default'].append(doc)

        chunk_configs = {
            'small_structured': {'chunk_size': 2000, 'chunk_overlap': 100},
            'large_structured': {'chunk_size': 1500, 'chunk_overlap': 200},
            'code_files': {'chunk_size': 1200, 'chunk_overlap': 150},
            'documentation': {'chunk_size': 1000, 'chunk_overlap': 200},
            'default': {'chunk_size': 1000, 'chunk_overlap': 200}
        }

        for strategy_name, docs in strategies.items():
            if not docs:
                continue

            config = chunk_configs[strategy_name]
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=config['chunk_size'],
                chunk_overlap=config['chunk_overlap'],
                separators=["\n\n", "\n", " ", ""]
            )

            chunks = splitter.split_documents(docs)

            for i, chunk in enumerate(chunks):
                chunk.metadata['chunk_strategy'] = strategy_name
                chunk.metadata['chunk_id'] = f"{strategy_name}_{i:04d}"

            all_chunks.extend(chunks)
            print(f"  {strategy_name}: {len(docs)} docs → {len(chunks)} chunks")

        self.chunks = all_chunks
        print(f"  Total: {len(all_chunks)} chunks created")
        return all_chunks

    def initialize_embedding_model(self):
        print(f"\nInitializing embedding model: {self.embedding_model_name}...")
        self.embedding_model = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
        print("Embedding model initialized")

    def create_vectorstore(self) -> Chroma:
        if not self.chunks:
            raise ValueError("No chunks available. Call chunk_documents_adaptive() first.")

        if not self.embedding_model:
            raise ValueError("Embedding model not initialized. Call initialize_embedding_model() first.")

        print("\nCreating vector store...")

        if self.temp_db_dir:
            try:
                shutil.rmtree(self.temp_db_dir)
            except:
                pass

        self.temp_db_dir = tempfile.mkdtemp(prefix="devops_kb_v2_")

        for chunk in self.chunks:
            cleaned_metadata = {}
            for key, value in chunk.metadata.items():
                if value is not None and not isinstance(value, (list, dict)):
                    cleaned_metadata[key] = value
                elif isinstance(value, list) and value:
                    cleaned_metadata[key] = str(value)
            chunk.metadata = cleaned_metadata

        self.vectorstore = Chroma.from_documents(
            documents=self.chunks,
            embedding=self.embedding_model,
            persist_directory=self.temp_db_dir
        )

        doc_count = self.vectorstore._collection.count()
        print(f"Vector store created with {doc_count} documents")
        return self.vectorstore

    def initialize(self):
        print("=" * 70)
        print("Initializing DevOps Knowledge Base")
        print("=" * 70)

        self.load_documents()
        self.discover_structure()
        self.create_dynamic_indices()
        self.chunk_documents_adaptive(self.documents)
        self.initialize_embedding_model()
        self.create_vectorstore()

        print("\n" + "=" * 70)
        print("Knowledge base initialized successfully!")
        print("=" * 70)
        return self.vectorstore


class DevOpsAIAssistant:
    def __init__(self, knowledge_base_path: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.knowledge_base = DevOpsKnowledgeBase(knowledge_base_path, embedding_model)
        self.vectorstore = None
        self.conversation_chain = None
        self.memory = None
        self.llm = None

    def setup(self):
        print("\nSetting up DevOps AI Assistant...")

        self.vectorstore = self.knowledge_base.initialize()

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        print("\nInitializing OpenAI LLM...")
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.3,
            api_key=api_key
        )

        print("Setting up conversation memory...")
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key='answer'
        )

        print("Creating conversation chain...")
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 10})

        self.conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory,
            return_source_documents=True,
            verbose=False
        )

        print("\n" + "=" * 70)
        print("DevOps AI Assistant ready!")
        print("=" * 70)
        return self

    def ask(self, question: str) -> dict:
        if not self.conversation_chain:
            raise ValueError("Assistant not initialized. Call setup() first.")

        result = self.conversation_chain.invoke({"question": question})

        response = {
            "answer": result.get('answer', ''),
            "sources": []
        }

        if result.get('source_documents'):
            unique_sources = {}
            for doc in result['source_documents']:
                source = doc.metadata.get('source')
                if source not in unique_sources:
                    path_info = "/".join([
                        doc.metadata.get('path_level_0', ''),
                        doc.metadata.get('path_level_1', ''),
                        doc.metadata.get('path_level_2', '')
                    ]).strip('/')

                    unique_sources[source] = {
                        "content": doc.page_content[:300],
                        "source": source,
                        "file_type": doc.metadata.get('file_type', 'Unknown'),
                        "path_info": path_info,
                        "kind": doc.metadata.get('kind'),
                        "language": doc.metadata.get('language')
                    }

            response["sources"] = list(unique_sources.values())

        return response

    def get_status(self) -> dict:
        if not self.vectorstore:
            return {"status": "not_initialized"}

        doc_count = self.vectorstore._collection.count()

        status = {
            "status": "ready",
            "documents_loaded": len(self.knowledge_base.documents),
            "chunks_created": len(self.knowledge_base.chunks),
            "vectors_in_store": doc_count,
            "knowledge_base_path": str(self.knowledge_base.knowledge_base_path)
        }

        if self.knowledge_base.structure:
            status["structure"] = {
                "total_files": self.knowledge_base.structure['total_files'],
                "file_types": len(self.knowledge_base.structure['by_file_type']),
                "patterns": self.knowledge_base.structure['patterns']
            }

        if self.knowledge_base.indices:
            status["indices"] = {
                "path_levels": len(self.knowledge_base.indices['by_path_level_0']),
                "kinds": len(self.knowledge_base.indices['by_kind']),
                "languages": len(self.knowledge_base.indices['by_language'])
            }

        return status


def create_assistant(knowledge_base_path: str) -> DevOpsAIAssistant:
    assistant = DevOpsAIAssistant(knowledge_base_path)
    assistant.setup()
    return assistant
