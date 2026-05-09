# Personal Knowledge Worker RAG Project

This project implements a **Retrieval-Augmented Generation (RAG)** system for personal knowledge management. It allows users to query a private document repository and receive intelligent answers enhanced by context from their files.  

Key features include:

- **Automatic File Conversion**: Users can add raw files (PDFs, Word documents, Excel, PowerPoint, images) to the `knowledge_base_raw` folder. The system automatically converts these files into Markdown format in `knowledge_base_markdown` for easier processing and embedding.  
- **Document Ingestion & Chunking**: Converted Markdown documents are split into smaller chunks and stored in a vector database (Chroma) with embeddings (HuggingFace or OpenAI) for semantic search.  
- **Vector-Based Retrieval**: Uses embeddings to retrieve the most relevant document chunks for each user query. Supports **history-aware retrieval** to maintain conversational context.  
- **LLM Integration**: Leverages `ChatOpenAI` to generate answers based on retrieved content while following a system prompt that ensures factual, context-aware responses.   
- **Visualization**: 2D and 3D scatter plots of vector embeddings using t-SNE and Plotly for insights into document distribution.  
- **User Interface**:  
  - **Gradio ChatInterface** 

## How to Run the Application

1. **Prepare your files**  
   - Place your raw documents in the appropriate subfolders under `knowledge_base_raw` (e.g., `pdf`, `word`, `excel`, `ppt`, `images`).  

2. **Install dependencies**  
   
   uv add uv add gradio plotly numpy scikit-learn tiktoken python-dotenv langchain langchain-openai langchain-huggingface langchain-chroma langchain-community

## Setup Instructions for the RAG System

3. **Set your OpenAI API key**  
   - Create a `.env` file with the following content:
     
     OPENAI_API_KEY=your_openai_api_key_here
     

4. **Convert raw files to Markdown**  
   - The application automatically converts supported files from `knowledge_base_raw` into Markdown files stored in `knowledge_base_markdown`.

5. **Load the knowledge base**  
   - Documents are loaded, split into chunks, and embedded in Chroma for semantic search.

6. **Launch the Gradio Chat Interface**  
   - You can now ask questions about your knowledge base.  
7. **Explore visualizations (optional)**  
   - 2D and 3D embeddings plots help you understand how your documents are distributed semantically.

---

**Future Improvement: Direct Download Links**

- Currently, all files are converted into Markdown for semantic search. In a future update, the system will provide clickable download links for original raw files, allowing users to access PDFs, Word documents, Excel sheets, images, and other file types directly from the chat interface.

- Integration with Other Tools: Connect with Slack, Teams, or a web dashboard for collaborative querying.

This RAG system allows users to query their private knowledge base efficiently, get accurate answers, and directly access original documents for deeper exploration.