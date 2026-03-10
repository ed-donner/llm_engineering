import os
from dotenv import load_dotenv
import modal

load_dotenv(override=True)

app = modal.App("football-rag-analyzer")

image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "langchain-community",
    "langchain-text-splitters",
    "langchain-openai",
    "langchain-chroma",
    "beautifulsoup4",
    "requests",
    "tiktoken"
)

@app.function(image=image, secrets=[modal.Secret.from_dict({"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "")})])
def generate_grounded_analogy_remote(tech_concept: str, tactical_style: str = "Total Football") -> str:
    from langchain_community.document_loaders import DirectoryLoader, TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_chroma import Chroma
    import requests
    from bs4 import BeautifulSoup
    import tempfile

    def scrape_wikipedia(title, path):
        url = f"https://en.wikipedia.org/wiki/{title}"
        headers = {"User-Agent": "Mozilla/5.0 (educational project)"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for element in soup(["math", "sup", "style", "script"]):
                element.decompose()
            paragraphs = soup.find_all('p')
            text = '\\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
    
    with tempfile.TemporaryDirectory() as tmpdirname:
        kb_dir = os.path.join(tmpdirname, "knowledge-base")
        os.makedirs(kb_dir, exist_ok=True)
        
        topics = [
            ("Tiki-taka", "tiki_taka.txt"),
            ("Gegenpressing", "gegenpressing.txt"),
            ("Total_Football", "total_football.txt")
        ]
        
        for topic, filename in topics:
            scrape_wikipedia(topic, os.path.join(kb_dir, filename))
            
        loader = DirectoryLoader(kb_dir, glob="**/*.txt", loader_cls=TextLoader)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = Chroma.from_documents(documents=chunks, embedding=embedding_model)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        
        query = f"{tech_concept} vs {tactical_style} football tactics"
        retrieved_docs = retriever.invoke(query)
        context = "\\n\\n".join([doc.page_content for doc in retrieved_docs])
        
        system_prompt = f"""
You are an expert software engineering mentor and an astute football tactician.
Your goal is to explain the tech concept or news article: '{tech_concept}'.
You must explain the concept using a detailed analogy based on the football tactic/style: '{tactical_style}'.

You MUST use the following factual football context retrieved from our knowledge base to ensure your analogy is grounded.
Context:
---
{context}
---

Structure your response as follows:
1. **The Core Concept**: Very briefly explain the tech news/concept in 1 sentence.
2. **The Pitch Analogy**: Introduce the football analogy using the factual context provided.
3. **How It Plays Out**: Map the tech elements to the tactical movements on the pitch.
"""

        response = llm.invoke([{"role": "system", "content": system_prompt}])
        return response.content


class AnalyzerAgent:
    """
    Houses the wrapper to call our Modal function.
    """
    def analyze(self, tech_concept: str) -> str:
        """
        Takes a tech concept, sends it to Modal (which runs the RAG pipeline),
        and returns a grounded football analogy explaining it.
        """
        print(f"Analyzing '{tech_concept[:30]}...' via Modal RAG Pipeline...")
        try:
            with app.run():
                result = generate_grounded_analogy_remote.remote(tech_concept, "Total Football")
            return result
        except Exception as e:
            return f"Error during analysis: {e}"

if __name__ == "__main__":
    analyzer = AnalyzerAgent()
    print(analyzer.analyze("OpenAI's new o1 reasoning model release"))
