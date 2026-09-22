from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma

from langgraph.checkpoint.memory import MemorySaver
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_classic.prompts import ChatPromptTemplate, MessagesPlaceholder

SYSTEM_PROMPT = "Use the following pieces of context to answer the user\'s question. If you don\'t know the answer, just say that you don\'t know, don\'t try to make up an answer."
QA_PROMPT = "You are a professional assistant. Answer user questions based on the document content. If you are unable to answer a question, please explain why."

MODEL = 'gpt-4o-mini'


def chat(query: str, vectorStore: Chroma, thread_id: str = "default_thread"):
    # 1.Initial seetting
    llm = ChatOpenAI(temperature=0.7, model_name=MODEL)
    memory = MemorySaver()
    checkpoint = memory.get(config={"configurable": {"thread_id": thread_id}})
    chat_history = (
        checkpoint["channel_values"]["messages"] if checkpoint else []
    )

    base_retriever = vectorStore.as_retriever()

    contextualize_prompt = ChatPromptTemplate.from_messages([
        ("system", f"{SYSTEM_PROMPT}"),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    history_aware_retriever = create_history_aware_retriever(
        retriever=base_retriever,
        llm=llm,
        prompt=contextualize_prompt)

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", f"{QA_PROMPT}"),
        ("system", "文件內容:\n{context}"),
        ("human", "{input}")
    ])
    doc_chain = create_stuff_documents_chain(llm=llm, prompt=qa_prompt)

    retrieval_chain = create_retrieval_chain(
        retriever=history_aware_retriever,
        combine_docs_chain=doc_chain
    )

    # query
    result = retrieval_chain.invoke(
        {"input": query, "chat_history": chat_history})

    chat_history.append({"role": "user", "content": query})
    chat_history.append({"role": "assistant", "content": result["answer"]})
    memory.put(config={"configurable": {"thread_id": thread_id, "checkpoint_ns": thread_id}},
               checkpoint={"id": thread_id,
                           "channel_values": {
                               "messages": chat_history}},
               metadata={},
               new_versions={})

    return result["answer"]
