import os
import glob
from pathlib import Path
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from datetime import datetime
# from implementation.db import build_sql_db
from db import build_sql_db
import sqlite3
from db import DB_PATH
load_dotenv(override=True)

openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
openrouter_base_url = os.getenv('OPENROUTER_BASE_URL')
openai_api_key = os.getenv('OPENAI_API_KEY')

if not openrouter_api_key:
    raise ValueError("OPENROUTER_API_KEY is not set")
if not openrouter_base_url:
    raise ValueError("OPENROUTER_BASE_URL is not a valid base URL")
if not openrouter_api_key.startswith("sk"):
    raise ValueError("OPENROUTER_API_KEY is not a valid API key")
if not openrouter_base_url.startswith("https://"):
    raise ValueError("OPENROUTER_BASE_URL is not a valid base URL")


embedding_model = "text-embedding-3-large"
DB_NAME = str(Path(__file__).parent.parent / "vector_db")
KNOWLEDGE_BASE = str(Path(__file__).parent.parent / "knowledge-base")


embeddings = OpenAIEmbeddings(model=embedding_model, openai_api_key=openrouter_api_key, openai_api_base=openrouter_base_url)

# DATE PARSING

def parse_date(date_ms: str, readable_date: str = "") -> tuple[str, int]:
    try:
        ms = int(date_ms)
        if readable_date:
            return readable_date, ms
        ts = ms / 1000
        return datetime.fromtimestamp(ts).strftime("%d %b %Y %I:%M %p"), ms
    except:
        return date_ms, 0


def get_year_month(date_ms_int: int) -> tuple[str, str]:
    try:
        dt = datetime.fromtimestamp(date_ms_int / 1000)
        return str(dt.year), dt.strftime("%B %Y")
    except:
        return "", ""


# SMS + MMS PARSING

def parse_sms(folder):
    documents = []
    xml_files = glob.glob(str(Path(folder) / "*.xml"))

    for xml_file in xml_files:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for sms in root.findall('sms'):
            body = sms.get('body', '')
            if not body or body == 'null':
                continue

            contact = sms.get('contact_name', '(Unknown)')
            if contact == '(Unknown)':
                contact = sms.get('address', '')
            address = sms.get('address', '')
            sms_type = sms.get('type', '1')
            date_str, date_ms_int = parse_date(sms.get('date', '0'), sms.get('readable_date', ''))
            direction = "Received" if sms_type == '1' else "Sent"
            role = "Me" if sms_type == '2' else contact
            year, year_month = get_year_month(date_ms_int)

            text = f"""SMS Record
Date: {date_str}
Year: {year}
Month: {year_month}
Contact: {contact}
Number: {address}
Direction: {direction}
Message: {role}: {body}"""

            documents.append(Document(
                page_content=text,
                metadata={
                    "doc_type": "sms", "contact": contact, "address": address,
                    "direction": direction, "date": date_str,
                    "date_ms": date_ms_int, "year": year,
                    "year_month": year_month, "source": xml_file
                }
            ))

        for mms in root.findall('mms'):
            contact = mms.get('contact_name', '(Unknown)')
            address = mms.get('address', '')
            msg_box = mms.get('msg_box', '1')
            date_str, date_ms_int = parse_date(mms.get('date', '0'), mms.get('readable_date', ''))
            direction = "Received" if msg_box == '1' else "Sent"
            role = "Me" if msg_box == '2' else contact
            year, year_month = get_year_month(date_ms_int)

            parts_text = []
            for part in mms.findall('.//part'):
                ct = part.get('ct', '')
                text_content = part.get('text', '')
                if 'text/plain' in ct and text_content and text_content != 'null':
                    parts_text.append(text_content)

            if not parts_text:
                continue

            body = "\n".join(parts_text)
            text = f"""MMS Record
Date: {date_str}
Year: {year}
Month: {year_month}
Contact: {contact}
Number: {address}
Direction: {direction}
Message: {role}: {body}"""

            documents.append(Document(
                page_content=text,
                metadata={
                    "doc_type": "mms", "contact": contact, "address": address,
                    "direction": direction, "date": date_str,
                    "date_ms": date_ms_int, "year": year,
                    "year_month": year_month, "source": xml_file
                }
            ))

    print(f"  Chroma SMS/MMS: loaded {len(documents)} records")
    return documents


# CALL PARSING

CALL_TYPES = {
    '1': 'Incoming', '2': 'Outgoing', '3': 'Missed',
    '4': 'Voicemail', '5': 'Rejected', '6': 'Blocked'
}


def parse_calls(folder):
    documents = []
    xml_files = glob.glob(str(Path(folder) / "*.xml"))

    for xml_file in xml_files:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for call in root.findall('call'):
            contact = call.get('contact_name', '(Unknown)')
            number = call.get('number', '')
            duration_sec = int(call.get('duration', 0))
            call_type = call.get('type', '1')
            date_str, date_ms_int = parse_date(call.get('date', '0'), call.get('readable_date', ''))
            call_type_label = CALL_TYPES.get(call_type, f"Type {call_type}")
            year, year_month = get_year_month(date_ms_int)

            minutes = duration_sec // 60
            seconds = duration_sec % 60
            if duration_sec == 0:
                duration_str = "0 seconds (missed/rejected)"
            elif minutes > 0:
                duration_str = f"{minutes} min {seconds} sec"
            else:
                duration_str = f"{seconds} sec"

            text = f"""Call Record
Date: {date_str}
Year: {year}
Month: {year_month}
Contact: {contact}
Number: {number}
Type: {call_type_label}
Duration: {duration_str}"""

            documents.append(Document(
                page_content=text,
                metadata={
                    "doc_type": "call", "contact": contact, "number": number,
                    "call_type": call_type_label, "duration_seconds": duration_sec,
                    "date": date_str, "date_ms": date_ms_int,
                    "year": year, "year_month": year_month, "source": xml_file
                }
            ))

    print(f"  Chroma Calls: loaded {len(documents)} records")
    return documents


# MAIN PIPELINE

def fetch_documents():
    documents = []
    documents += parse_sms(str(Path(KNOWLEDGE_BASE) / "sms"))
    documents += parse_calls(str(Path(KNOWLEDGE_BASE) / "call"))
    print(f"\nTotal Chroma documents: {len(documents)}")
    return documents


def create_chroma_embeddings(documents):
    if os.path.exists(DB_NAME):
        Chroma(persist_directory=DB_NAME, embedding_function=embeddings).delete_collection()
    vectorstore = Chroma.from_documents(
        documents=documents, embedding=embeddings, persist_directory=DB_NAME
    )
    collection = vectorstore._collection
    count = collection.count()
    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)
    print(f"Chroma: {count:,} vectors with {dimensions:,} dimensions")
    return vectorstore


if __name__ == "__main__":
    # build sql db and vector db
    print("=== Building SQL DB ===")
    build_sql_db()

    print("\n=== Building Chroma Vector Store ===")
    documents = fetch_documents()
    create_chroma_embeddings(documents)

    print("\nIngestion complete")