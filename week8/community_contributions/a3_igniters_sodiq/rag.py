import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
load_dotenv(override=True)

DB_PATH = "./chroma_db"

def get_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    
    embedding = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    
    collection = client.get_or_create_collection(
        name="support_knowledge_base",
        embedding_function=embedding
    )
    return collection

def populate_knowledge_base():
    collection = get_collection()
    
    if collection.count() > 0:
        return

    documents = [
        "To reset your password, go to Settings > Security > Reset Password. You will receive a reset link via email.",
        "We accept the following payment methods: Visa, MasterCard, American Express, and PayPal.",
        "Refunds are processed within 5-10 business days. To request a refund, contact billing support with your order ID.",
        "Our standard support hours are Monday to Friday, 9 AM to 5 PM EST. Premium support is available 24/7.",
        "To update your billing address, navigate to the Billing section in your account dashboard.",
        "The API documentation can be found at https://api.example.com/docs. API keys are managed in the Developer settings.",
        "Two-factor authentication (2FA) can be enabled in the Security settings for added account protection.",
        "If you encounter a '500 Internal Server Error', please try clearing your browser cache or contact technical support."
    ]
    
    ids = [f"doc_{i}" for i in range(len(documents))]
    
    collection.add(
        documents=documents,
        ids=ids
    )
    print("Knowledge base populated with synthetic data.")

def search_knowledge_base(query, n_results=3):
    populate_knowledge_base()
    
    collection = get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    print(f"RAG search results for query: '{query}'")
    for i, doc in enumerate(results['documents'][0]):
        print(f"{i+1}. {doc}")
    
    if results and results['documents']:
        return results['documents'][0]
    
    return []