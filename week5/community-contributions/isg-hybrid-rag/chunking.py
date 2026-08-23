"""LLM-based document chunking utilities."""
import json
import re

from tqdm import tqdm
from litellm import completion
from config import MODEL, URL, AVERAGE_CHUNK_SIZE
from models import Chunks


def make_prompt(document):
    """Generate the chunking prompt for a given document."""
    how_many = (len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1
    return f"""
You take a document and you split the document into overlapping chunks for a KnowledgeBase.

The document is from the shared drive of a company called Insurellm.
The document is of type: {document["type"]}
The document has been retrieved from: {document["source"]}

A chatbot will use these chunks to answer questions about the company.
You should divide up the document as you see fit, being sure that the entire document is returned in the chunks - don't leave anything out.
This document should probably be split into {how_many} chunks, but you can have more or less as appropriate.
There should be overlap between the chunks as appropriate; typically about 25% overlap or about 50 words, so you have the same text in multiple chunks for best retrieval results.

For each chunk, you should provide a headline, a summary, and the original text of the chunk.
Together your chunks should represent the entire document with overlap.

Here is the document:

{document["text"]}

Respond with the chunks.
"""


def make_messages(document):
    """Wrap a document into a user message for chunking."""
    return [{"role": "user", "content": make_prompt(document)}]


def parse_chunks(data) -> Chunks:
    """Parse raw LLM response into a Chunks model."""
    if isinstance(data, str):
        data = data.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(data)
    while isinstance(data, dict) and isinstance(data.get("chunks"), str):
        data = json.loads(data["chunks"])
    if isinstance(data, list):  # bare array, which is what you got
        data = {"chunks": data}
    return Chunks.model_validate(data)


def normalize(s: str) -> str:
    """Normalize whitespace in a string."""
    return " ".join(s.split())


def check_verbatim(chunks, document) -> int:
    """Check how many chunks are not verbatim substrings of the original document."""
    source = normalize(document["text"])
    bad = 0
    for c in chunks:
        if normalize(c.original_text) not in source:
            print(f"⚠ not verbatim: {c.headline}")
            bad += 1
    return bad


def extract_json(text: str):
    """Extract the first JSON object or array from an LLM response."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    start = min((i for i in (text.find("{"), text.find("[")) if i != -1), default=-1)
    if start == -1:
        raise ValueError(f"No JSON found in: {text[:200]}")
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(text[start:])  # ignores trailing junk
    return obj


def process_document(document):
    """Process a single document into a list of Result objects."""
    messages = make_messages(document)
    response = completion(
        model=MODEL,
        messages=messages,
        api_base=URL,
        response_format=Chunks,
    )
    reply = response.choices[0].message.content
    reply_clean = extract_json(reply)
    doc_as_chunks = parse_chunks(reply_clean).chunks

    return [chunk.as_result(document) for chunk in doc_as_chunks]


def create_chunks(documents):
    """Create chunks from a list of documents."""
    chunks = []
    for doc in tqdm(documents):
        chunks.extend(process_document(doc))
    return chunks
