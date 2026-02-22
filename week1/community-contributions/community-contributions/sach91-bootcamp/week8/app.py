"""
KnowledgeHub - Personal Knowledge Management & Research Assistant
Main Gradio Application
"""
import os
import logging
import json
import gradio as gr
from pathlib import Path
import chromadb
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import utilities and agents
from utils import OllamaClient, EmbeddingModel, DocumentParser
from agents import (
    IngestionAgent, QuestionAgent, SummaryAgent,
    ConnectionAgent, ExportAgent
)
from models import Document

# Constants
VECTORSTORE_PATH = "./vectorstore"
TEMP_UPLOAD_PATH = "./temp_uploads"
DOCUMENTS_METADATA_PATH = "./vectorstore/documents_metadata.json"

# Ensure directories exist
os.makedirs(VECTORSTORE_PATH, exist_ok=True)
os.makedirs(TEMP_UPLOAD_PATH, exist_ok=True)

class KnowledgeHub:
    """Main application class managing all agents"""

    def __init__(self):
        logger.info("Initializing KnowledgeHub...")

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"description": "Personal knowledge management collection"}
        )

        # Initialize embedding model
        self.embedding_model = EmbeddingModel()

        # Initialize shared LLM client
        self.llm_client = OllamaClient(model="llama3.2")

        # Check Ollama connection
        if not self.llm_client.check_connection():
            logger.warning("⚠️ Cannot connect to Ollama. Please ensure Ollama is running.")
            logger.warning("Start Ollama with: ollama serve")
        else:
            logger.info("✓ Connected to Ollama")

        # Initialize agents
        self.ingestion_agent = IngestionAgent(
            collection=self.collection,
            embedding_model=self.embedding_model,
            llm_client=self.llm_client
        )

        self.question_agent = QuestionAgent(
            collection=self.collection,
            embedding_model=self.embedding_model,
            llm_client=self.llm_client
        )

        self.summary_agent = SummaryAgent(
            collection=self.collection,
            llm_client=self.llm_client
        )

        self.connection_agent = ConnectionAgent(
            collection=self.collection,
            embedding_model=self.embedding_model,
            llm_client=self.llm_client
        )

        self.export_agent = ExportAgent(
            llm_client=self.llm_client
        )

        # Track uploaded documents
        self.documents = {}

        # Load existing documents from metadata file
        self._load_documents_metadata()

        logger.info("✓ KnowledgeHub initialized successfully")

    def _save_documents_metadata(self):
        """Save document metadata to JSON file"""
        try:
            metadata = {
                doc_id: doc.to_dict()
                for doc_id, doc in self.documents.items()
            }

            with open(DOCUMENTS_METADATA_PATH, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.debug(f"Saved metadata for {len(metadata)} documents")
        except Exception as e:
            logger.error(f"Error saving document metadata: {e}")

    def _load_documents_metadata(self):
        """Load document metadata from JSON file"""
        try:
            if os.path.exists(DOCUMENTS_METADATA_PATH):
                with open(DOCUMENTS_METADATA_PATH, 'r') as f:
                    metadata = json.load(f)

                # Reconstruct Document objects (simplified - without chunks)
                for doc_id, doc_data in metadata.items():
                    # Create a minimal Document object for UI purposes
                    # Full chunks are still in ChromaDB
                    doc = Document(
                        id=doc_id,
                        filename=doc_data['filename'],
                        filepath=doc_data.get('filepath', ''),
                        content=doc_data.get('content', ''),
                        chunks=[],  # Chunks are in ChromaDB
                        metadata=doc_data.get('metadata', {}),
                        created_at=datetime.fromisoformat(doc_data['created_at'])
                    )
                    self.documents[doc_id] = doc

                logger.info(f"✓ Loaded {len(self.documents)} existing documents from storage")
            else:
                logger.info("No existing documents found (starting fresh)")

        except Exception as e:
            logger.error(f"Error loading document metadata: {e}")
            logger.info("Starting with empty document list")

    def upload_document(self, files, progress=gr.Progress()):
        """Handle document upload - supports single or multiple files with progress tracking"""
        if files is None or len(files) == 0:
            return "⚠️ Please select file(s) to upload", "", []

        # Convert single file to list for consistent handling
        if not isinstance(files, list):
            files = [files]

        results = []
        successful = 0
        failed = 0
        total_chunks = 0

        # Initialize progress tracking
        progress(0, desc="Starting upload...")

        for file_idx, file in enumerate(files, 1):
            # Update progress
            progress_pct = (file_idx - 1) / len(files)
            progress(progress_pct, desc=f"Processing {file_idx}/{len(files)}: {Path(file.name).name}")

            try:
                logger.info(f"Processing file {file_idx}/{len(files)}: {file.name}")

                # Save uploaded file temporarily
                temp_path = os.path.join(TEMP_UPLOAD_PATH, Path(file.name).name)

                # Copy file content
                with open(temp_path, 'wb') as f:
                    f.write(file.read() if hasattr(file, 'read') else open(file.name, 'rb').read())

                # Process document
                document = self.ingestion_agent.process(temp_path)

                # Store document reference
                self.documents[document.id] = document

                # Track stats
                successful += 1
                total_chunks += document.num_chunks

                # Add to results
                results.append({
                    'status': '✅',
                    'filename': document.filename,
                    'chunks': document.num_chunks,
                    'size': f"{document.total_chars:,} chars"
                })

                # Clean up temp file
                os.remove(temp_path)

            except Exception as e:
                logger.error(f"Error processing {file.name}: {e}")
                failed += 1
                results.append({
                    'status': '❌',
                    'filename': Path(file.name).name,
                    'chunks': 0,
                    'size': f"Error: {str(e)[:50]}"
                })

        # Final progress update
        progress(1.0, desc="Upload complete!")

        # Save metadata once after all uploads
        if successful > 0:
            self._save_documents_metadata()

        # Create summary
        summary = f"""## Upload Complete! 🎉

**Total Files:** {len(files)}
**✅ Successful:** {successful}
**❌ Failed:** {failed}
**Total Chunks Created:** {total_chunks:,}

{f"⚠️ **{failed} file(s) failed** - Check results table below for details" if failed > 0 else "All files processed successfully!"}
"""

        # Create detailed results table
        results_table = [[r['status'], r['filename'], r['chunks'], r['size']] for r in results]

        # Create preview of first successful document
        preview = ""
        for doc in self.documents.values():
            if doc.filename in [r['filename'] for r in results if r['status'] == '✅']:
                preview = doc.content[:500] + "..." if len(doc.content) > 500 else doc.content
                break

        return summary, preview, results_table

    def ask_question(self, question, top_k, progress=gr.Progress()):
        """Handle question answering with progress tracking"""
        if not question.strip():
            return "⚠️ Please enter a question", [], ""

        try:
            # Initial status
            progress(0, desc="Processing your question...")
            status = "🔄 **Searching knowledge base...**\n\nRetrieving relevant documents..."

            logger.info(f"Answering question: {question[:100]}")

            # Update progress
            progress(0.3, desc="Finding relevant documents...")

            result = self.question_agent.process(question, top_k=top_k)

            # Update progress
            progress(0.7, desc="Generating answer with LLM...")

            # Format answer
            answer = f"""### Answer\n\n{result['answer']}\n\n"""

            if result['sources']:
                answer += f"**Sources:** {result['num_sources']} documents referenced\n\n"

            # Format sources for display
            sources_data = []
            for i, source in enumerate(result['sources'], 1):
                sources_data.append([
                    i,
                    source['document'],
                    f"{source['score']:.2%}",
                    source['preview']
                ])

            progress(1.0, desc="Answer ready!")

            return answer, sources_data, "✅ Answer generated successfully!"

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"❌ Error: {str(e)}", [], f"❌ Error: {str(e)}"

    def create_summary(self, doc_selector, progress=gr.Progress()):
        """Create document summary with progress tracking"""
        if not doc_selector:
            return "⚠️ Please select a document to summarize", ""

        try:
            # Initial status
            progress(0, desc="Preparing to summarize...")

            logger.info(f'doc_selector : {doc_selector}')
            doc_id = doc_selector.split(" -|- ")[1]
            document = self.documents.get(doc_id)

            if not document:
                return "", "❌ Document not found"

            # Update status
            status_msg = f"🔄 **Generating summary for:** {document.filename}\n\nPlease wait, this may take 10-20 seconds..."
            progress(0.3, desc=f"Analyzing {document.filename}...")

            logger.info(f"Creating summary for: {document.filename}")

            # Generate summary
            summary = self.summary_agent.process(
                document_id=doc_id,
                document_name=document.filename
            )

            progress(1.0, desc="Summary complete!")

            # Format result
            result = f"""## Summary of {summary.document_name}\n\n{summary.summary_text}\n\n"""

            if summary.key_points:
                result += "### Key Points\n\n"
                for point in summary.key_points:
                    result += f"- {point}\n"

            return result, "✅ Summary generated successfully!"

        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            return "", f"❌ Error: {str(e)}"

    def find_connections(self, doc_selector, top_k, progress=gr.Progress()):
        """Find related documents with progress tracking"""
        if not doc_selector:
            return "⚠️ Please select a document", [], ""

        try:
            progress(0, desc="Preparing to find connections...")

            doc_id = doc_selector.split(" -|- ")[1]
            document = self.documents.get(doc_id)

            if not document:
                return "❌ Document not found", [], "❌ Document not found"

            status = f"🔄 **Finding documents related to:** {document.filename}\n\nSearching knowledge base..."
            progress(0.3, desc=f"Analyzing {document.filename}...")

            logger.info(f"Finding connections for: {document.filename}")

            result = self.connection_agent.process(document_id=doc_id, top_k=top_k)

            progress(0.8, desc="Calculating similarity scores...")

            if 'error' in result:
                return f"❌ Error: {result['error']}", [], f"❌ Error: {result['error']}"

            message = f"""## Related Documents\n\n**Source:** {result['source_document']}\n\n"""
            message += f"**Found {result['num_related']} related documents:**\n\n"""

            # Format for table
            table_data = []
            for i, rel in enumerate(result['related'], 1):
                table_data.append([
                    i,
                    rel['document_name'],
                    f"{rel['similarity']:.2%}",
                    rel['preview']
                ])

            progress(1.0, desc="Connections found!")

            return message, table_data, "✅ Related documents found!"

        except Exception as e:
            logger.error(f"Error finding connections: {e}")
            return f"❌ Error: {str(e)}", [], f"❌ Error: {str(e)}"

    def export_knowledge(self, format_choice):
        """Export knowledge base"""
        try:
            logger.info(f"Exporting as {format_choice}")

            # Get statistics
            stats = self.ingestion_agent.get_statistics()

            # Create export content
            content = {
                'title': 'Knowledge Base Export',
                'summary': f"Total documents in knowledge base: {len(self.documents)}",
                'sections': [
                    {
                        'title': 'Documents',
                        'content': '\n'.join([f"- {doc.filename}" for doc in self.documents.values()])
                    },
                    {
                        'title': 'Statistics',
                        'content': f"Total chunks stored: {stats['total_chunks']}"
                    }
                ]
            }

            # Export
            if format_choice == "Markdown":
                output = self.export_agent.process(content, format="markdown")
                filename = f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            elif format_choice == "HTML":
                output = self.export_agent.process(content, format="html")
                filename = f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            else:  # Text
                output = self.export_agent.process(content, format="text")
                filename = f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            # Save file
            export_path = os.path.join(TEMP_UPLOAD_PATH, filename)
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(output)

            return f"✅ Exported as {format_choice}", export_path

        except Exception as e:
            logger.error(f"Error exporting: {e}")
            return f"❌ Error: {str(e)}", None

    def get_statistics(self):
        """Get knowledge base statistics"""
        try:
            stats = self.ingestion_agent.get_statistics()

            total_docs = len(self.documents)
            total_chunks = stats.get('total_chunks', 0)
            total_chars = sum(doc.total_chars for doc in self.documents.values())

            # Check if data is persisted
            persistence_status = "✅ Enabled" if os.path.exists(DOCUMENTS_METADATA_PATH) else "⚠️ Not configured"
            vectorstore_size = self._get_directory_size(VECTORSTORE_PATH)

            stats_text = f"""## Knowledge Base Statistics

**Persistence Status:** {persistence_status}
**Total Documents:** {total_docs}
**Total Chunks:** {total_chunks:,}
**Total Characters:** {total_chars:,}
**Vector Store Size:** {vectorstore_size}

### Storage Locations
- **Vector DB:** `{VECTORSTORE_PATH}/`
- **Metadata:** `{DOCUMENTS_METADATA_PATH}`

**📝 Note:** Your data persists across app restarts!

**Recent Documents:**
{chr(10).join([f"- {doc.filename} ({doc.num_chunks} chunks)" for doc in list(self.documents.values())[-5:]])}
"""
            if self.documents:
                stats_text += "\n".join([f"- {doc.filename} ({doc.num_chunks} chunks, added {doc.created_at.strftime('%Y-%m-%d')})"
                                        for doc in list(self.documents.values())[-10:]])
            else:
                stats_text += "\n*No documents yet. Upload some to get started!*"

            return stats_text

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def _get_directory_size(self, path):
        """Calculate directory size"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)

            # Convert to human readable
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    return f"{total_size:.1f} {unit}"
                total_size /= 1024.0
            return f"{total_size:.1f} TB"
        except:
            return "Unknown"

    def get_document_list(self):
        """Get list of documents for dropdown"""
        new_choices = [f"{doc.filename} -|- {doc.id}" for doc in self.documents.values()]
        return gr.update(choices=new_choices, value=None)


    def delete_document(self, doc_selector):
        """Delete a document from the knowledge base"""
        if not doc_selector:
            return "⚠️ Please select a document to delete", self.get_document_list()

        try:
            doc_id = doc_selector.split(" - ")[0]
            document = self.documents.get(doc_id)

            if not document:
                return "❌ Document not found", self.get_document_list()

            # Delete from ChromaDB
            success = self.ingestion_agent.delete_document(doc_id)

            if success:
                # Remove from documents dict
                filename = document.filename
                del self.documents[doc_id]

                # Save updated metadata
                self._save_documents_metadata()

                return f"✅ Deleted: {filename}", self.get_document_list()
            else:
                return f"❌ Error deleting document", self.get_document_list()

        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return f"❌ Error: {str(e)}", self.get_document_list()

    def clear_all_documents(self):
        """Clear entire knowledge base"""
        try:
            # Delete collection
            self.client.delete_collection("knowledge_base")

            # Recreate empty collection
            self.collection = self.client.create_collection(
                name="knowledge_base",
                metadata={"description": "Personal knowledge management collection"}
            )

            # Update agents with new collection
            self.ingestion_agent.collection = self.collection
            self.question_agent.collection = self.collection
            self.summary_agent.collection = self.collection
            self.connection_agent.collection = self.collection

            # Clear documents
            self.documents = {}
            self._save_documents_metadata()

            return "✅ All documents cleared from knowledge base"

        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return f"❌ Error: {str(e)}"


def create_ui():
    """Create Gradio interface"""

    # Initialize app
    app = KnowledgeHub()

    # Custom CSS
    custom_css = """
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .stat-box {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    """

    with gr.Blocks(title="KnowledgeHub", css=custom_css, theme=gr.themes.Soft()) as interface:

        # Header
        gr.HTML("""
        <div class="main-header">
            <h1>🧠 KnowledgeHub</h1>
            <p>Personal Knowledge Management & Research Assistant</p>
            <p style="font-size: 14px; opacity: 0.9;">
                Powered by Ollama (Llama 3.2) • Fully Local & Private
            </p>
        </div>
        """)

        # Main tabs
        with gr.Tabs():

            # Tab 1: Upload Documents
            with gr.Tab("📤 Upload Documents"):
                gr.Markdown("### Upload your documents to build your knowledge base")
                gr.Markdown("*Supported formats: PDF, DOCX, TXT, MD, HTML, PY*")
                gr.Markdown("*💡 Tip: You can select multiple files at once!*")

                with gr.Row():
                    with gr.Column():
                        file_input = gr.File(
                            label="Select Document(s)",
                            file_types=[".pdf", ".docx", ".txt", ".md", ".html", ".py"],
                            file_count="multiple"  # Enable multiple file selection
                        )
                        upload_btn = gr.Button("📤 Upload & Process", variant="primary")

                    with gr.Column():
                        upload_status = gr.Markdown("Ready to upload documents")

                # Results table for batch uploads
                with gr.Row():
                    upload_results = gr.Dataframe(
                        headers=["Status", "Filename", "Chunks", "Size"],
                        label="Upload Results",
                        wrap=True,
                        visible=True
                    )

                with gr.Row():
                    document_preview = gr.Textbox(
                        label="Document Preview (First Uploaded)",
                        lines=10,
                        max_lines=15
                    )

                upload_btn.click(
                    fn=app.upload_document,
                    inputs=[file_input],
                    outputs=[upload_status, document_preview, upload_results]
                )

            # Tab 2: Ask Questions
            with gr.Tab("❓ Ask Questions"):
                gr.Markdown("### Ask questions about your documents")
                gr.Markdown("*Uses RAG (Retrieval Augmented Generation) to answer based on your knowledge base*")

                with gr.Row():
                    with gr.Column(scale=3):
                        question_input = gr.Textbox(
                            label="Your Question",
                            placeholder="What would you like to know?",
                            lines=3
                        )

                    with gr.Column(scale=1):
                        top_k_slider = gr.Slider(
                            minimum=1,
                            maximum=10,
                            value=5,
                            step=1,
                            label="Number of sources"
                        )
                        ask_btn = gr.Button("🔍 Ask", variant="primary")

                qa_status = gr.Markdown("Ready to answer questions")
                answer_output = gr.Markdown(label="Answer")

                sources_table = gr.Dataframe(
                    headers=["#", "Document", "Relevance", "Preview"],
                    label="Sources",
                    wrap=True
                )

                ask_btn.click(
                    fn=app.ask_question,
                    inputs=[question_input, top_k_slider],
                    outputs=[answer_output, sources_table, qa_status]
                )

            # Tab 3: Summarize
            with gr.Tab("📝 Summarize"):
                gr.Markdown("### Generate summaries and extract key points")

                with gr.Row():
                    with gr.Column():
                        doc_selector = gr.Dropdown(
                            choices=[],
                            label="Select Document",
                            info="Choose a document to summarize",
                            allow_custom_value=True
                        )
                        refresh_btn = gr.Button("🔄 Refresh List")
                        summarize_btn = gr.Button("📝 Generate Summary", variant="primary")
                        summary_status = gr.Markdown("Ready to generate summaries")

                    with gr.Column(scale=2):
                        summary_output = gr.Markdown(label="Summary")

                summarize_btn.click(
                    fn=app.create_summary,
                    inputs=[doc_selector],
                    outputs=[summary_output, summary_status]
                )

                refresh_btn.click(
                    fn=app.get_document_list,
                    outputs=[doc_selector]
                )

            # Tab 4: Find Connections
            with gr.Tab("🔗 Find Connections"):
                gr.Markdown("### Discover relationships between documents")

                with gr.Row():
                    with gr.Column():
                        conn_doc_selector = gr.Dropdown(
                            choices=[],
                            label="Select Document",
                            info="Find documents related to this one",
                            allow_custom_value=True
                        )
                        conn_top_k = gr.Slider(
                            minimum=1,
                            maximum=10,
                            value=5,
                            step=1,
                            label="Number of related documents"
                        )
                        refresh_conn_btn = gr.Button("🔄 Refresh List")
                        find_btn = gr.Button("🔗 Find Connections", variant="primary")
                        connection_status = gr.Markdown("Ready to find connections")

                connection_output = gr.Markdown(label="Connections")

                connections_table = gr.Dataframe(
                    headers=["#", "Document", "Similarity", "Preview"],
                    label="Related Documents",
                    wrap=True
                )

                find_btn.click(
                    fn=app.find_connections,
                    inputs=[conn_doc_selector, conn_top_k],
                    outputs=[connection_output, connections_table, connection_status]
                )

                refresh_conn_btn.click(
                    fn=app.get_document_list,
                    outputs=[conn_doc_selector]
                )

            # Tab 5: Export
            with gr.Tab("💾 Export"):
                gr.Markdown("### Export your knowledge base")

                with gr.Row():
                    with gr.Column():
                        format_choice = gr.Radio(
                            choices=["Markdown", "HTML", "Text"],
                            value="Markdown",
                            label="Export Format"
                        )
                        export_btn = gr.Button("💾 Export", variant="primary")

                    with gr.Column():
                        export_status = gr.Markdown("Ready to export")
                        export_file = gr.File(label="Download Export")

                export_btn.click(
                    fn=app.export_knowledge,
                    inputs=[format_choice],
                    outputs=[export_status, export_file]
                )

            # Tab 6: Manage Documents
            with gr.Tab("🗂️ Manage Documents"):
                gr.Markdown("### Manage your document library")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### Delete Document")
                        delete_doc_selector = gr.Dropdown(
                            choices=[],
                            label="Select Document to Delete",
                            info="Choose a document to remove from knowledge base"
                        )
                        with gr.Row():
                            refresh_delete_btn = gr.Button("🔄 Refresh List")
                            delete_btn = gr.Button("🗑️ Delete Document", variant="stop")
                        delete_status = gr.Markdown("")

                    with gr.Column():
                        gr.Markdown("#### Clear All Documents")
                        gr.Markdown("⚠️ **Warning:** This will delete your entire knowledge base!")
                        clear_confirm = gr.Textbox(
                            label="Type 'DELETE ALL' to confirm",
                            placeholder="DELETE ALL"
                        )
                        clear_all_btn = gr.Button("🗑️ Clear All Documents", variant="stop")
                        clear_status = gr.Markdown("")

                def confirm_and_clear(confirm_text):
                    if confirm_text.strip() == "DELETE ALL":
                        return app.clear_all_documents()
                    else:
                        return "⚠️ Please type 'DELETE ALL' to confirm"

                delete_btn.click(
                    fn=app.delete_document,
                    inputs=[delete_doc_selector],
                    outputs=[delete_status, delete_doc_selector]
                )

                refresh_delete_btn.click(
                    fn=app.get_document_list,
                    outputs=[delete_doc_selector]
                )

                clear_all_btn.click(
                    fn=confirm_and_clear,
                    inputs=[clear_confirm],
                    outputs=[clear_status]
                )

            # Tab 7: Statistics
            with gr.Tab("📊 Statistics"):
                gr.Markdown("### Knowledge Base Overview")
                
                stats_output = gr.Markdown()
                stats_btn = gr.Button("🔄 Refresh Statistics", variant="primary")
                
                stats_btn.click(
                    fn=app.get_statistics,
                    outputs=[stats_output]
                )
                
                # Auto-load stats on tab open
                interface.load(
                    fn=app.get_statistics,
                    outputs=[stats_output]
                )
        
        # Footer
        gr.HTML("""
        <div style="text-align: center; margin-top: 30px; padding: 20px; color: #666;">
            <p>🔒 All processing happens locally on your machine • Your data never leaves your computer</p>
            <p style="font-size: 12px;">Powered by Ollama, ChromaDB, and Sentence Transformers</p>
        </div>
        """)
    
    return interface


if __name__ == "__main__":
    logger.info("Starting KnowledgeHub...")
    
    # Create and launch interface
    interface = create_ui()
    interface.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True
    )
