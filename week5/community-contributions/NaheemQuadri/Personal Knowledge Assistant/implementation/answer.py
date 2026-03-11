import os
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, convert_to_messages
from langchain_core.documents import Document
from dotenv import load_dotenv
from implementation.db import query_sql, format_sql_results

load_dotenv(override=True)

#credentials and config

openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
openrouter_base_url = os.getenv('OPENROUTER_BASE_URL')


if not openrouter_api_key:
    raise ValueError("OPENROUTER_API_KEY is not set")
if not openrouter_base_url:
    raise ValueError("OPENROUTER_BASE_URL is not a valid base URL")
if not openrouter_api_key.startswith("sk"):
    raise ValueError("OPENROUTER_API_KEY is not a valid API key")
if not openrouter_base_url.startswith("https://"):
    raise ValueError("OPENROUTER_BASE_URL is not a valid base URL")


MODEL = "openai/gpt-4.1-nano"
embedding_model = "openai/text-embedding-3-large"
DB_NAME = str(Path(__file__).parent.parent / "vector_db")

embeddings = OpenAIEmbeddings(model=embedding_model, openai_api_key=openrouter_api_key, openai_api_base=openrouter_base_url)
vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)
llm = ChatOpenAI(
    model=MODEL, temperature=0,
    api_key=openrouter_api_key, base_url=openrouter_base_url
)



MONTHS = {
    'january': 1, 'jan': 1, 'february': 2, 'feb': 2,
    'march': 3, 'mar': 3, 'april': 4, 'apr': 4,
    'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
    'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
    'october': 10, 'oct': 10, 'november': 11, 'nov': 11,
    'december': 12, 'dec': 12
}

def to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)

def extract_date_range(question: str) -> tuple[int, int] | None:
    """
    Extract a date range from the question.
    Returns (start_ms, end_ms) or None if no date found.
    Handles: years, month+year, relative terms (today, yesterday, last week, last month)
    """
    now = datetime.now()
    q = question.lower()

    #today
    if 'today' in q:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=0)
        return to_ms(start), to_ms(end)

    #yesterday
    if 'yesterday' in q:
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
        return to_ms(start), to_ms(end)

    #last week
    if 'last week' in q:
        start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        return to_ms(start), to_ms(end)

    #last month
    if 'last month' in q:
        first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_last_month = first_of_this_month - timedelta(seconds=1)
        start_of_last_month = end_of_last_month.replace(day=1, hour=0, minute=0, second=0)
        return to_ms(start_of_last_month), to_ms(end_of_last_month)

    #last N days
    match = re.search(r'last (\d+) days?', q)
    if match:
        days = int(match.group(1))
        start = now - timedelta(days=days)
        return to_ms(start), to_ms(now)

    #this year
    if 'this year' in q:
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(month=12, day=31, hour=23, minute=59, second=59)
        return to_ms(start), to_ms(end)

    #month + year
    pattern = r'\b(' + '|'.join(MONTHS.keys()) + r')\s+(20\d{2})\b'
    match = re.search(pattern, q)
    if match:
        month = MONTHS[match.group(1)]
        year = int(match.group(2))
        start = datetime(year, month, 1, 0, 0, 0)
        if month == 12:
            end = datetime(year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
        else:
            end = datetime(year, month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
        return to_ms(start), to_ms(end)

    #year only
    match = re.search(r'\b(20\d{2})\b', q)
    if match:
        year = int(match.group(1))
        start = datetime(year, 1, 1, 0, 0, 0)
        end = datetime(year, 12, 31, 23, 59, 59)
        return to_ms(start), to_ms(end)

    return None


def has_date_in_question(question: str) -> bool:
    return extract_date_range(question) is not None


#retrival

def fetch_from_sql(question: str, date_range: tuple[int, int]) -> str:
    start_ms, end_ms = date_range
    print(f"  [SQL] Querying from {datetime.fromtimestamp(start_ms/1000)} to {datetime.fromtimestamp(end_ms/1000)}")
    
    # check if question is about calls or sms
    q = question.lower()
    if 'call' in q:
        doc_types = ['calls']
    elif any(w in q for w in ['message', 'sms', 'mms', 'text', 'chat']):
        doc_types = ['sms']
    else:
        doc_types = None  # both

    results = query_sql(start_ms=start_ms, end_ms=end_ms, doc_types=doc_types, limit=100)
    print(f"  [SQL] Found {len(results)} records")
    return format_sql_results(results)


def fetch_from_chroma(question: str, k: int = 30) -> tuple[str, list[Document]]:
    docs = vectorstore.as_retriever(search_kwargs={"k": k}).invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    print(f"  [DEBUG] context={context}")
    return context, docs



def build_system_prompt(context: str) -> str:
    now = datetime.now()
    return f"""
You are a personal knowledge assistant for Naheem Quadri.
You have access to Naheem's personal data including SMS, MMS conversations and call history
spanning from July 2023 to March 2026.

Current date and time: {now.strftime("%A, %d %B %Y %I:%M %p")}
Current day of week: {now.strftime("%A")}
Current month: {now.strftime("%B %Y")}

Use the context below to answer the question. Be concise and specific.
If the context does not contain the answer, say so clearly.

Context:
{context}
"""



def combined_question(question: str, history: list[dict] = []) -> str:
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return (prior + "\n" + question).strip()


def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    # extract date from current question
    date_range = extract_date_range(question)
    docs = []

    if date_range:
        
        context = fetch_from_sql(question, date_range)
    else:
        
        combined = combined_question(question, history)
        context, docs = fetch_from_chroma(combined)

    system_prompt = build_system_prompt(context)
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history))
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)
    return response.content, docs


# for the evaluator to use

def fetch_context(question: str, history: list[dict] = []):
    date_range = extract_date_range(question)

    if date_range:
        context = fetch_from_sql(question, date_range)
        return context, []
    else:
        combined = combined_question(question, history)
        return fetch_from_chroma(combined)

