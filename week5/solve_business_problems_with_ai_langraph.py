# Install required packages
!pip install langgraph langchain-openai chromadb pandas gspread gspread-dataframe sentence-transformers



# Install required packages
!pip install langgraph langchain-openai chromadb pandas gspread gspread-dataframe sentence-transformers

import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import json
import uuid
from typing import Dict, List, Any, TypedDict
from dataclasses import dataclass
from enum import Enum

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode as ToolExecutor
from langgraph.prebuilt import ToolNode

import openai
from openai import OpenAI
import gspread
from gspread_dataframe import set_with_dataframe
from google.colab import auth

# Configure OpenAI client
client = OpenAI(
    base_url='https://47v4us7kyypinfb5lcligtc3x40ygqbs.lambda-url.us-east-1.on.aws/v1/',
    api_key='a0BIj000002KNpKMAW'
)

# Initialize LangChain OpenAI client
llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_base='https://47v4us7kyypinfb5lcligtc3x40ygqbs.lambda-url.us-east-1.on.aws/v1/',
    openai_api_key='a0BIj000002KNpKMAW',
    temperature=0.1
)

# Data models and state definitions
class EmailType(Enum):
    PRODUCT_INQUIRY = "product inquiry"
    ORDER_REQUEST = "order request"

class OrderStatus(Enum):
    CREATED = "created"
    OUT_OF_STOCK = "out of stock"

@dataclass
class Product:
    product_id: str
    name: str
    category: str
    stock: int
    description: str
    price: float
    season: str

@dataclass
class Email:
    email_id: str
    subject: str
    message: str

@dataclass
class OrderItem:
    product_id: str
    product_name: str
    quantity: int
    status: OrderStatus

# LangGraph State
class ProcessingState(TypedDict):
    email: Email
    email_type: str
    order_items: List[Dict]
    relevant_products: List[Dict]
    response: str
    processing_complete: bool
    error: str

# Code example of reading input data
def read_data_frame(document_id, sheet_name):
    export_link = f"https://docs.google.com/spreadsheets/d/{document_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return  pd.read_csv(export_link)

document_id = '14fKHsblfqZfWj3iAaM2oA51TlYfQlFT4WKo52fVaQ9U'
products_df = read_data_frame(document_id, 'products')
emails_df = read_data_frame(document_id, 'emails')

# Display first 3 rows of each DataFrame
print("Products DataFrame:")
print(products_df.head(3))
print("\nEmails DataFrame:")
print(emails_df.head(3))


class ProductVectorStore:
    """ChromaDB-based vector store for scalable product search"""

    def __init__(self, products_df: pd.DataFrame):
        required_columns = ['product_id', 'name', 'category', 'stock', 'description', 'price']
        missing_columns = [col for col in required_columns if col not in products_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        if 'seasons' in products_df.columns:
            products_df = products_df.rename(columns={'seasons': 'season'})
        self.has_season = 'season' in products_df.columns

        self.chroma_client = chromadb.Client()
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection_name = "products"
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
        except:
            pass
        self.collection = self.chroma_client.create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function
        )
        self._populate_vector_store(products_df)
        self.products_dict = {}
        for _, row in products_df.iterrows():
            product_data = {
                'product_id': str(row['product_id']),
                'name': str(row['name']),
                'category': str(row['category']),
                'stock': int(row['stock']),
                'description': str(row['description']),
                'price': float(row['price']),
            }
            if self.has_season:
                product_data['season'] = str(row['season'])
            else:
                product_data['season'] = 'N/A'
            self.products_dict[str(row['product_id'])] = Product(**product_data)

    def _populate_vector_store(self, products_df: pd.DataFrame):
        documents = []
        metadatas = []
        ids = []
        for _, row in products_df.iterrows():
            season_text = str(row['season']) if self.has_season else ''
            searchable_text = f"{row['name']} {row['category']} {row['description']} {season_text}".strip()
            documents.append(searchable_text)
            metadata = {
                'product_id': str(row['product_id']),
                'name': str(row['name']),
                'category': str(row['category']),
                'stock': int(row['stock']),
                'price': float(row['price']),
            }
            if self.has_season:
                metadata['season'] = str(row['season'])
            else:
                metadata['season'] = 'N/A'
            metadatas.append(metadata)
            ids.append(str(row['product_id']))

        batch_size = 1000
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))
            self.collection.add(
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx],
                ids=ids[i:end_idx]
            )
        print(f"Added {len(documents)} products to vector store")

    def search_products(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        relevant_products = []
        if results['metadatas'] and results['metadatas'][0]:
            relevant_products = results['metadatas'][0]
        return relevant_products

    def update_stock(self, product_id: str, quantity: int) -> bool:
        if product_id in self.products_dict and self.products_dict[product_id].stock >= quantity:
            self.products_dict[product_id].stock -= quantity
            print(f"Updated stock for {product_id}. New stock: {self.products_dict[product_id].stock}")
            return True
        return False

vector_store = ProductVectorStore(products_df)

# LangGraph Workflow Nodes

def classify_email_node(state: ProcessingState) -> ProcessingState:
    email = state["email"]
    messages = [
        {"role": "system", "content": """You are an email classifier for a fashion store.
        Classify emails into exactly one of these categories:
        - "order request": Customer wants to purchase items, mentions quantities, shows buying intent, asks about ordering
        - "product inquiry": Customer asks questions, seeks recommendations, requests product information, asks about availability

        Respond with exactly: "order request" or "product inquiry" """},
        {"role": "user", "content": f"Subject: {email.subject}\nBody: {email.message}"}
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.1,
            max_tokens=50
        )
        classification = response.choices[0].message.content.strip().lower()
        if "order request" in classification:
            email_type = EmailType.ORDER_REQUEST.value
        else:
            email_type = EmailType.PRODUCT_INQUIRY.value
        state["email_type"] = email_type
        print(f"Email {email.email_id} classified as: {email_type}")
    except Exception as e:
        state["error"] = f"Classification error: {str(e)}"
        state["email_type"] = EmailType.PRODUCT_INQUIRY.value
    return state

def extract_order_details_node(state: ProcessingState) -> ProcessingState:
    if state["email_type"] != EmailType.ORDER_REQUEST.value:
        state["order_items"] = []
        return state
    email = state["email"]
    sample_products = list(vector_store.products_dict.items())[:20]
    sample_context = "\n".join([
        f"ID: {prod_id}, Name: {product.name}, Category: {product.category}"
        for prod_id, product in sample_products
    ])
    messages = [
        {"role": "system", "content": """You are an order processing assistant. Extract product information from customer emails.
        Return a JSON array with objects containing:
        - "product_name": exact product name or closest match from context
        - "quantity": number requested (default to 1 if not specified)
        If multiple products or categories are mentioned, include all.
        If quantity is "all" or unspecified, use 1."""},
        {"role": "user", "content": f"""
        Sample Products for reference:
        {sample_context}

        Customer Email:
        Subject: {email.subject}
        Body: {email.message}

        Extract order details as JSON array:"""}
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.1,
            max_tokens=800
        )
        content = response.choices[0].message.content.strip()
        import re
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            order_items = json.loads(json_match.group())
            state["order_items"] = order_items
        else:
            state["order_items"] = []
        print(f"Extracted {len(state['order_items'])} order items for email {email.email_id}")
    except Exception as e:
        state["error"] = f"Order extraction error: {str(e)}"
        state["order_items"] = []
    return state

def process_order_node(state: ProcessingState) -> ProcessingState:
    if state["email_type"] != EmailType.ORDER_REQUEST.value:
        return state
    order_results = []
    for item in state["order_items"]:
        product_name = item.get("product_name", "")
        quantity = int(item.get("quantity", 1))
        relevant_products = vector_store.search_products(product_name, n_results=5)
        best_match = None
        if relevant_products:
            best_match = relevant_products[0]
        if best_match and best_match["stock"] >= quantity:
            product_id = best_match["product_id"]
            if vector_store.update_stock(product_id, quantity):
                order_results.append({
                    "product_id": product_id,
                    "product_name": best_match["name"],
                    "quantity": quantity,
                    "status": OrderStatus.CREATED.value
                })
            else:
                order_results.append({
                    "product_id": best_match["product_id"],
                    "product_name": product_name,
                    "quantity": quantity,
                    "status": OrderStatus.OUT_OF_STOCK.value
                })
        else:
            order_results.append({
                "product_id": best_match["product_id"] if best_match else "UNKNOWN",
                "product_name": product_name,
                "quantity": quantity,
                "status": OrderStatus.OUT_OF_STOCK.value
            })
    state["order_items"] = order_results
    print(f"Processed {len(order_results)} order items")
    return state

def search_products_node(state: ProcessingState) -> ProcessingState:
    if state["email_type"] != EmailType.PRODUCT_INQUIRY.value:
        return state
    email = state["email"]
    query = f"{email.subject} {email.message}"
    relevant_products = vector_store.search_products(query, n_results=8)
    state["relevant_products"] = relevant_products
    print(f"Found {len(relevant_products)} relevant products for inquiry")
    return state

def generate_order_response_node(state: ProcessingState) -> ProcessingState:
    if state["email_type"] != EmailType.ORDER_REQUEST.value:
        return state
    order_items = state["order_items"]
    email = state["email"]
    successful_orders = [item for item in order_items if item["status"] == OrderStatus.CREATED.value]
    failed_orders = [item for item in order_items if item["status"] == OrderStatus.OUT_OF_STOCK.value]
    context = {
        "successful_orders": successful_orders,
        "failed_orders": failed_orders,
        "customer_email_subject": email.subject
    }
    messages = [
        {"role": "system", "content": """You are a professional customer service representative.
        Generate a warm, professional email response for order processing results."""},
        {"role": "user", "content": f"""
        Generate an email response for the following order processing results:

        Successful Orders: {successful_orders}
        Out of Stock Items: {failed_orders}
        Original Subject: {email.subject}

        Instructions:
        1. Start with a professional greeting
        2. If successful orders exist, confirm them enthusiastically with product names and quantities
        3. If items are out of stock, apologize and offer alternatives (restock notifications, similar products)
        4. Include next steps and contact information
        5. End professionally
        6. Keep it concise but informative

        Generate only the email body, no subject line.
        """}
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        state["response"] = response.choices[0].message.content.strip()
    except Exception as e:
        state["error"] = f"Response generation error: {str(e)}"
        state["response"] = "Thank you for your order. We are processing your request and will contact you shortly."
    return state

def generate_inquiry_response_node(state: ProcessingState) -> ProcessingState:
    if state["email_type"] != EmailType.PRODUCT_INQUIRY.value:
        return state
    relevant_products = state["relevant_products"]
    email = state["email"]
    product_info = []
    for product in relevant_products[:5]:
        stock_status = "In Stock" if product["stock"] > 0 else "Out of Stock"
        product_info.append(
            f"• {product['name']} ({product['category']}) - ${product['price']:.2f} - {stock_status}\n"
            f"  Season: {product['season']}, Stock: {product['stock']} units"
        )
    products_context = "\n\n".join(product_info) if product_info else "No specific matching products found."
    messages = [
        {"role": "system", "content": """You are a knowledgeable fashion store customer service representative.
        Generate helpful, professional responses to customer inquiries using relevant product information."""},
        {"role": "user", "content": f"""
        Customer Inquiry:
        Subject: {email.subject}
        Message: {email.message}

        Relevant Products from our catalog:
        {products_context}

        Instructions:
        1. Warmly greet the customer
        2. Directly address their inquiry
        3. Recommend relevant products with key details (name, price, availability)
        4. If out of stock, suggest alternatives or restock notifications
        5. Provide helpful styling or usage suggestions where appropriate
        6. Offer additional assistance
        7. Close professionally
        8. Keep tone friendly and knowledgeable

        Generate only the email body, no subject line.
        """}
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1200
        )
        state["response"] = response.choices[0].message.content.strip()
    except Exception as e:
        state["error"] = f"Inquiry response error: {str(e)}"
        state["response"] = "Thank you for your inquiry. Our team will provide detailed product information within 24 hours."
    return state

def finalize_processing_node(state: ProcessingState) -> ProcessingState:
    state["processing_complete"] = True
    return state

# Build LangGraph Workflow
from langgraph.graph import StateGraph, END

def should_process_order(state: ProcessingState) -> str:
    if state["email_type"] == EmailType.ORDER_REQUEST.value:
        return "extract_order_details"
    else:
        return "search_products"

def should_generate_response(state: ProcessingState) -> str:
    if state["email_type"] == EmailType.ORDER_REQUEST.value:
        return "generate_order_response"
    else:
        return "generate_inquiry_response"

workflow = StateGraph(ProcessingState)
workflow.add_node("classify_email", classify_email_node)
workflow.add_node("extract_order_details", extract_order_details_node)
workflow.add_node("process_order", process_order_node)
workflow.add_node("search_products", search_products_node)
workflow.add_node("generate_order_response", generate_order_response_node)
workflow.add_node("generate_inquiry_response", generate_inquiry_response_node)
workflow.add_node("finalize_processing", finalize_processing_node)
workflow.set_entry_point("classify_email")

workflow.add_conditional_edges(
    "classify_email",
    should_process_order,
    {
        "extract_order_details": "extract_order_details",
        "search_products": "search_products"
    }
)
workflow.add_edge("extract_order_details", "process_order")
workflow.add_conditional_edges(
    "process_order",
    should_generate_response,
    {
        "generate_order_response": "generate_order_response"
    }
)
workflow.add_conditional_edges(
    "search_products",
    should_generate_response,
    {
        "generate_inquiry_response": "generate_inquiry_response"
    }
)
workflow.add_edge("generate_order_response", "finalize_processing")
workflow.add_edge("generate_inquiry_response", "finalize_processing")
workflow.add_edge("finalize_processing", END)
app = workflow.compile()

# **EXECUTE THE WORKFLOW FOR ALL EMAILS**
all_results = []
for index, email_row in emails_df.iterrows():
    initial_email = Email(
        email_id=email_row['email_id'],
        subject=email_row['subject'],
        message=email_row['message']
    )
    initial_state = {
        "email": initial_email,
        "email_type": None,
        "order_items": [],
        "relevant_products": [],
        "response": None,
        "processing_complete": False,
        "error": None
    }
    result = app.invoke(initial_state)
    all_results.append(result)
    print(f"--- Processing complete for email_id: {email_row['email_id']} ---")
    print(result)

print("\n--- All emails processed. Final results list contains the state for each email. ---")

# --- Final Code to Fix Output Mismatch and Write to Google Sheets ---

# Google Sheets Authentication

# Process all_results into separate dataframes
email_classification_data = []
order_status_data = []
order_response_data = []
inquiry_response_data = []

for result in all_results:
    email_id = result['email'].email_id
    email_type = result['email_type']
    response = result['response']

    # 1. Email Classification
    email_classification_data.append({'email ID': email_id, 'category': email_type})

    if email_type == EmailType.ORDER_REQUEST.value:
        # 2. Order Status
        for item in result['order_items']:
            order_status_data.append({
                'email ID': email_id,
                'product ID': item.get('product_id'),
                'quantity': item.get('quantity'),
                'status': item.get('status')
            })
        # 2. Order Response
        order_response_data.append({'email ID': email_id, 'response': response})

    elif email_type == EmailType.PRODUCT_INQUIRY.value:
        # 3. Inquiry Response
        inquiry_response_data.append({'email ID': email_id, 'response': response})

# Create DataFrames
email_classification_df = pd.DataFrame(email_classification_data)
order_status_df = pd.DataFrame(order_status_data)
order_response_df = pd.DataFrame(order_response_data)
inquiry_response_df = pd.DataFrame(inquiry_response_data)

print(email_classification_df)
print(order_status_df)
print(order_response_df)
print(inquiry_response_df)



#print("All results have been written to the Google Spreadsheet.")

!pip install gspread pandas gspread-dataframe

from google.colab import auth
auth.authenticate_user()

import gspread
from google.auth import default

creds, _ = default()
gc = gspread.authorize(creds)

import pandas as pd
from gspread_dataframe import set_with_dataframe

# Create a new spreadsheet
spreadsheet = gc.create('Solving Business Problems with AI - Output')
spreadsheet.share('', perm_type='anyone', role='reader')
spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit"


# Create worksheets
email_classification_sheet = spreadsheet.add_worksheet(title='email-classification', rows=100, cols=20)
order_status_sheet = spreadsheet.add_worksheet(title='order-status', rows=100, cols=20)
order_response_sheet = spreadsheet.add_worksheet(title='order-response', rows=100, cols=20)
inquiry_response_sheet = spreadsheet.add_worksheet(title='inquiry-response', rows=100, cols=20)

# Write dataframes to sheets
set_with_dataframe(email_classification_sheet, email_classification_df)
set_with_dataframe(order_status_sheet, order_status_df)
set_with_dataframe(order_response_sheet, order_response_df)
set_with_dataframe(inquiry_response_sheet, inquiry_response_df)
print(f"Shareable link: {spreadsheet_url}")