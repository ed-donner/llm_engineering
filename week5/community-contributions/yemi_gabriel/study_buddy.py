import os
from pathlib import Path
import gradio as gr
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pymupdf
import pymupdf4llm

class StudyBuddy:
    def __init__(self, llm, embedding_model, db_name, retrieval_k, system_prompt):
        self.llm = llm
        self.embedding_model = embedding_model
        self.db_name = db_name
        self.retrieval_k = retrieval_k
        self.system_prompt = system_prompt

    def convert_pdf_to_markdown(self, pdf_path):
        return pymupdf4llm.to_markdown(pdf_path, page_chunks=True)

    def process_pdf(self, file):
        if not file.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are allowed.")
        markdown_pages = self.convert_pdf_to_markdown(file)
        return markdown_pages, Path(file).stem

    def documents_to_chunks(self, markdown_pages, file_name):
        docs = [
            Document(
                page_content=page["text"],
                metadata={"page": page["metadata"]["page_number"], "source": file_name}
            )
            for page in markdown_pages
        ]
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=120,
            separators=["\n## ", "\n### ", "\n\n", "\n", " "]
        )
        return text_splitter.split_documents(docs)

    def create_vectorstore(self, documents):
        embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model)
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=self.db_name
        )
        return vectorstore.as_retriever(search_kwargs={"k": self.retrieval_k})

    def upload_pdf_and_prepare(self, file):
        markdown, file_name = self.process_pdf(file)
        chunks = self.documents_to_chunks(markdown, file_name)
        retriever = self.create_vectorstore(chunks)
        return "PDF processed. You can now ask questions.", retriever

    def answer_question(self, question, history, retriever):
        if not retriever:
            return [{"role": "assistant", "content": "Please upload a document first."}]
        docs = retriever.invoke(question)
    
        print("Retrieved docs:", len(docs))
        for d in docs:
            print(d.metadata)

        context = "\n\n".join(
            f"(Page {doc.metadata.get('page', 'unknown')}) {doc.page_content}"
            for doc in docs
        )
        system_prompt = self.system_prompt.format(context=context)
        messages = [SystemMessage(content=system_prompt)]
        for msg in history or []:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=question))
        response = self.llm.invoke(messages)
        answer = response.content
        return (history or []) + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]

    def launch(self):
        with gr.Blocks() as app:
            gr.Markdown("# Study Buddy")
            retriever_state = gr.State()
            upload = gr.File(file_types=[".pdf"], label="Upload PDF Document")
            status = gr.Markdown()
            chatbot = gr.Chatbot(type="messages")
            message = gr.Textbox(label="Ask a question")

            def gr_upload(file):
                try:
                    msg, retriever = self.upload_pdf_and_prepare(file)
                    return msg, retriever
                except Exception as e:
                    return f"Error: {e}", None

            def gr_answer(question, history, retriever):
                return self.answer_question(question, history, retriever)

            upload.change(
                gr_upload,
                inputs=upload,
                outputs=[status, retriever_state],
                show_progress=True
            )

            message.submit(
                gr_answer,
                inputs=[message, chatbot, retriever_state],
                outputs=chatbot
            ).then(lambda: "", None, message)

            app.launch(inbrowser=True)
