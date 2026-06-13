import os
import json
from supabase import create_client
from answer import fetch_context_unranked

SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_INSURLLM_RAG_URL")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load all chunks from DB once
all_rows = supabase.table("semantic_chunked_documents").select("id, content").execute().data

def keyword_in_db(keyword):
    return any(keyword.lower() in row["content"].lower() for row in all_rows)

def keyword_in_retrieved(keyword, chunks):
    return any(keyword.lower() in c.page_content.lower() for c in chunks)

# Run diagnostic
not_in_db = []
in_db_not_retrieved = []

with open("tests.jsonl") as f:
    tests = [json.loads(line) for line in f]

for test in tests[:20]:  # start with first 20
    question = test["question"]
    keywords = test["keywords"]
    chunks = fetch_context_unranked(question)

    for kw in keywords:
        if not keyword_in_db(kw):
            not_in_db.append((question, kw))
        elif not keyword_in_retrieved(kw, chunks):
            in_db_not_retrieved.append((question, kw))

print(f"Keywords missing from DB entirely: {len(not_in_db)}")
print(f"Keywords in DB but not retrieved:  {len(in_db_not_retrieved)}")
print("\nMissing from DB:", not_in_db[:5])
print("\nIn DB but not retrieved:", in_db_not_retrieved[:5])

# What dimension are stored embeddings?
row = supabase.table("semantic_chunked_documents").select("embedding").limit(1).execute()
embedding = json.loads(row.data[0]['embedding'])
print(f"Actual stored dimensions: {len(embedding)}")


with open("tests.jsonl") as f:
    tests = [json.loads(line) for line in f]

for test in tests:
    chunks = fetch_context_unranked(test["question"])
    for kw in test["keywords"]:
        if not keyword_in_retrieved(kw, chunks):
            print(test["question"], kw)