from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from chromadb import PersistentClient
from tqdm import tqdm
from litellm import completion
from multiprocessing import Pool
from tenacity import (
    retry,
    wait_exponential,
)  # Tenacity lets us add retry logic with a decorator. If the decorated function raises an exception, it waits using exponential backoff, then retries. Improvement: configure it to retry only on specific errors, such as rate-limit errors.


load_dotenv(override=True)

MODEL = "openai/gpt-4.1-nano"

DB_NAME = str(
    Path(__file__).parent.parent / "preprocessed_db"
)  # making sure we have the right path to our database.
COLLECTION_NAME = "docs"
embedding_model = "text-embedding-3-large"
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge-base"
EMPLOYEE_RECORDS_PATH = Path(__file__).parent.parent / "knowledge-base" / "employees"

AVERAGE_CHUNK_SIZE = 100
wait = wait_exponential(multiplier=1, min=10, max=240)


WORKERS = 5

openai = OpenAI()


class Result(BaseModel):
    page_content: str
    metadata: dict


class Chunk(BaseModel):
    headline: str = Field(
        description="A brief heading for this chunk, typically a few words, that is most likely to be surfaced in a query",
    )
    summary: str = Field(
        description="A few sentences summarizing the content of this chunk to answer common questions"
    )
    original_text: str = Field(
        description="The original text of this chunk from the provided document, exactly as is, not changed in any way"
    )

    def as_result(self, document):
        metadata = {"source": document["source"], "type": document["type"]}
        return Result(
            page_content=self.headline
            + "\n\n"
            + self.summary
            + "\n\n"
            + self.original_text,
            metadata=metadata,
        )


class Chunks(BaseModel):
    chunks: list[Chunk]


class DocumentSummary(BaseModel):
    title: str = Field(
        description=(
            "A short human-readable title for the document. "
            "Use the document's actual title if present; otherwise create a concise title."
        )
    )

    entity_name: str | None = Field(
        default=None,
        description=(
            "The main entity this document is about. "
            "For employee profiles, use the employee's full name. "
            "For product documents, use the product name. "
            "For contract documents, use the client/product contract name. "
            "For broad company notes with no single main entity, use null."
        ),
    )

    summary: str = Field(
        description=(
            "A 2-4 sentence overview of the whole document. "
            "Explain what the document is about and include the most important facts. "
            "Write this for semantic retrieval, so include natural phrases a user might ask about."
        )
    )

    key_facts: list[str] = Field(
        description=(
            "A list of specific factual bullets extracted from the document. "
            "Each item should be one clear fact. Include names, dates, awards, salaries, "
            "job titles, departments, product names, pricing, contract values, clients, "
            "teams, owners, and launch dates when present. "
            "Do not invent facts. If a fact is not in the document, leave it out."
        )
    )

    topics: list[str] = Field(
        description=(
            "A list of short retrieval tags for this document. "
            "Use lowercase tags where possible, such as employee, salary, product, pricing, "
            "contract, award, IIOTY, roadmap, launch date, team ownership, customer, "
            "engineering, marketing, sales, claims, health insurance, life insurance, reinsurance."
        )
    )


class GlobalIndexDoc(BaseModel):
    index_type: str = Field(
        description=(
            "The category of cross-document index this record represents. "
            "Use one short lowercase value such as 'awards', 'products', 'employees', "
            "or 'contracts'. Each GlobalIndexDoc should focus on one category only."
        )
    )
    title: str = Field(
        description=(
            "A short human-readable title for this global index document. "
            "Examples: 'Insurellm Employees Index', 'Insurellm Products Index', "
            "or 'Insurellm Contracts Index'."
        )
    )
    summary: str = Field(
        description=(
            "A 2-4 sentence overview of what this index covers across the whole knowledge base. "
            "Write this for broad retrieval questions, such as questions asking for all products, "
            "all award winners, every contract, or all employees matching a category."
        )
    )
    facts: list[str] = Field(
        description=(
            "Specific cross-document facts for this index category. "
            "Each item should be one clear fact. For employees, include names, roles, departments, salaries, and achievements. "
            "For products, include product names, insurance lines, owners, pricing, launch dates, and roadmap details. "
            "For contracts, include clients, values, products, renewal dates, and responsible teams. "
            "Do not invent missing details."
        )
    )

    def as_result(self):
        page_content = (
            f"Index type: {self.index_type}\n"
            f"Title: {self.title}\n\n"
            f"Summary:\n{self.summary}\n\n"
            f"Facts:\n" + "\n".join(f"- {fact}" for fact in self.facts)
        )

        metadata = {
            "source": f"global_index:{self.index_type}",  # eg. 'global_index:products' -> this is NOT a filepath, we cann use this to track the markdown files
            "doc_id": f"global_index:{self.index_type}",
            "type": "global_index",
            "level": "global_index",
            "index_type": self.index_type,
        }

        return Result(
            page_content=page_content, metadata=metadata
        )  # formatting the document aka the global index document


class GlobalIndexDocs(BaseModel):
    indexes: list[
        GlobalIndexDoc
    ]  # this model returns a list of all the global index documents


class EmployeeRecord(BaseModel):
    name: str | None = Field(
        default=None,
        description=(
            "The employee's full name exactly as stated in the document. "
            "Use null if the name is not present."
        ),
    )

    department: str | None = Field(
        default=None,
        description=(
            "The employee's department exactly as stated in the document. "
            "Do not infer the department from the job title. Use null if not present."
        ),
    )

    current_salary: int | None = Field(
        default=None,
        description=(
            "The employee's current salary as an integer number of dollars only. "
            "For example, '$85,000' should become 85000. "
            "Do not include currency symbols, commas, or text. "
            "Use null if the current salary is not present."
        ),
    )

    start_date: str | None = Field(
        default=None,
        description=(
            "The employee's start date exactly as stated in the document. "
            "Do not guess missing dates. Use null if not present."
        ),
    )

    job_title: str | None = Field(
        default=None,
        description=(
            "The employee's job title exactly as stated in the document. "
            "Use null if not present."
        ),
    )

    location: str | None = Field(
        default=None,
        description=(
            "The employee's work location exactly as stated in the document. "
            "Use null if not present."
        ),
    )

    education: str | None = Field(
        default=None,
        description=(
            "The employee's education background exactly as stated in the document. "
            "Include degree, institution, field of study, or certifications if present. "
            "Do not infer education from job title or seniority. Use null if not present."
        ),
    )

    source: str = Field(
        description=(
            "The source file path for the document this employee record was extracted from. "
            "This must be copied exactly from the provided document source."
        )
    )


def fetch_documents(folder_path=KNOWLEDGE_BASE_PATH):
    """A homemade version of the LangChain DirectoryLoader"""

    documents = []

    for folder in folder_path.iterdir():
        doc_type = folder.name
        for file in folder.rglob("*.md"):
            with open(file, "r", encoding="utf-8") as f:
                documents.append(
                    {"type": doc_type, "source": file.as_posix(), "text": f.read()}
                )

    # if the folder_path itself is a folder, because it has no other folders in it
    if folder_path == EMPLOYEE_RECORDS_PATH:
        doc_type = "employees"
        for file in folder_path.rglob("*.md"):
            with open(file, "r", encoding="utf-8") as f:
                documents.append(
                    {"type": doc_type, "source": file.as_posix(), "text": f.read()}
                )

    print(f"Loaded {len(documents)} documents")
    return documents


def make_prompt(document):
    how_many = (len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1
    return f"""
You take a document and you split the document into overlapping chunks for a KnowledgeBase.

The document is from the shared drive of a company called Insurellm.
The document is of type: {document["type"]}
The document has been retrieved from: {document["source"]}

A chatbot will use these chunks to answer questions about the company.
You should divide up the document as you see fit, being sure that the entire document is returned across the chunks - don't leave anything out.
This document should probably be split into at least {how_many} chunks, but you can have more or less as appropriate, ensuring that there are individual chunks to answer specific questions.
There should be overlap between the chunks as appropriate; typically about 25% overlap or about 50 words, so you have the same text in multiple chunks for best retrieval results.

For each chunk, you should provide a headline, a summary, and the original text of the chunk.
Together your chunks should represent the entire document with overlap.

Here is the document:

{document["text"]}

Respond with the chunks.
"""


def make_summary_prompt(document):
    return f"""
You summarize one knowledge-base document for retrieval.

The goal is NOT to answer a user yet.
The goal is to create a document-level summary that helps a RAG system find this document later.

Document type: {document["type"]}
Document source: {document["source"]}

Return a structured DocumentSummary.

Rules:
- Summarize the whole document, not just the first section.
- Preserve exact names, dates, awards, salaries, product names, client names, pricing, teams, and contract values.
- Put exact factual details in key_facts as separate bullet-style strings.
- Use topics as short retrieval tags.
- Do not invent facts.
- If there is no single main entity, set entity_name to null.

Document:
{document["text"]}
"""


def make_global_index_prompt(document_summaries):
    summaries_text = "\n\n---\n\n".join(
        summary.page_content for summary in document_summaries
    )

    return f"""
You create cross-document global index records for a company knowledge-base RAG system.

The company is called Insurellm.

You will receive document-level summaries. Each summary represents one source document.
Your job is to create a small set of global indexes that help answer broad questions across many documents.

Create these global indexes when the facts are present:
- awards: all awards, award winners, years, reasons, and related employees/products
- products: all products, insurance lines, owners, pricing, launch dates, and roadmap details
- employees: all employees, roles, departments, salaries, achievements, and notable facts
- contracts: all contracts, clients, values, products involved, renewal dates, and responsible teams

Rules:
- Use only facts found in the provided document summaries.
- Do not invent missing details.
- Each index must focus on one category only.
- Each fact should be specific enough to answer "all", "every", "list", and "across the company" questions.
- Prefer complete coverage over shortness.
- If a category has no useful facts, omit that index.

Document summaries:
{summaries_text}

Respond with the global indexes.
"""


def make_employee_record_prompt(document):
    return f"""
You extract one structured employee record from one employee/profile markdown document.
Return a structured EmployeeRecord.
Rules:
- Extract only one employee.
- Use only facts explicitly stated in the document.
- Do not infer missing values.
- Use null if the field is not present.
- current_salary must be an integer number of dollars only.
  Example: "$85,000" becomes 85000.
- Do not include currency symbols, commas, or text in current_salary.
- start_date should be copied exactly as stated where possible.
- education should include degree, institution, field of study, or certifications if present.
- Do not infer education from job title or seniority.
- source must be exactly: {document["source"]}

Document type: {document["type"]}
Document source: {document["source"]}

Document:
{document["text"]}

Do not infer missing values. Use null if the field is not present.
"""


def make_messages(document):
    return [
        {"role": "user", "content": make_prompt(document)},
    ]


def make_summary_messages(document):
    return [{"role": "user", "content": make_summary_prompt(document)}]


def make_global_index_messages(document_summaries):
    return [{"role": "user", "content": make_global_index_prompt(document_summaries)}]


def make_employee_record_messages(document):
    return [{"role": "user", "content": make_employee_record_prompt(document)}]


@retry(wait=wait)
def process_document(document):
    messages = make_messages(document)
    response = completion(model=MODEL, messages=messages, response_format=Chunks)
    reply = response.choices[0].message.content
    doc_as_chunks = Chunks.model_validate_json(reply).chunks
    return [chunk.as_result(document) for chunk in doc_as_chunks]


@retry(wait=wait)
def summarize_document(document):
    """This is a parallel to the process_document function, draft the prompt for each document, send it to the LLM for processing, then we get back the summarised documents."""
    messages = make_summary_messages(document)
    response = completion(
        model=MODEL, messages=messages, response_format=DocumentSummary
    )
    reply = response.choices[0].message.content
    doc_summary = DocumentSummary.model_validate_json(
        reply
    )  # convert the response into a document summary object
    page_content = (
        f"Title: {doc_summary.title}\n"
        f"Entity: {doc_summary.entity_name or 'None'}\n\n"
        f"Summary:\n{doc_summary.summary}\n\n"
        f"Key facts:\n"
        + "\n".join(f"- {fact}" for fact in doc_summary.key_facts)
        + "\n\n"
        "Topics:\n" + ", ".join(doc_summary.topics)
    )

    metadata = {
        "source": document["source"],
        "doc_id": document["source"],
        "type": document["type"],
        "level": "doc_summary",
        "entity_name": doc_summary.entity_name or "",
    }

    return Result(
        page_content=page_content, metadata=metadata
    )  # 1 document should only have 1 summary document.


@retry(wait=wait)
def extract_employee_record(document):
    """Returns an employee record in json format by asking the LLM to process each employee record"""
    messages = make_employee_record_messages(document)
    response = completion(
        model=MODEL, messages=messages, response_format=EmployeeRecord
    )
    reply = response.choices[0].message.content
    employee_record = EmployeeRecord.model_validate_json(
        reply
    )  # convert the response into a EmployeeRecord object
    return employee_record


def write_employee_records(documents):
    """
    Extract employee records from employee/profile documents and write them as JSONL.
    JSONL means one JSON object per line.
    Output path: structured/employees.jsonl
    """
    output_dir = Path(__file__).parent.parent / "structured"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "employees.jsonl"

    employee_documents = [doc for doc in documents]

    with open(output_path, "w", encoding="utf-8") as f:
        for document in tqdm(employee_documents):
            employee_record = extract_employee_record(document)
            json_line = (
                employee_record.model_dump_json()
            )  # converts the pydantic object into a json string
            f.write(json_line + "\n")

    print(f"Wrote {len(employee_documents)} employee records to {output_path}")


@retry(wait=wait)
def create_global_index_docs(document_summaries):
    """Create cross-document index records from document summary Results."""
    messages = make_global_index_messages(document_summaries)
    response = completion(
        model=MODEL, messages=messages, response_format=GlobalIndexDocs
    )
    reply = response.choices[0].message.content
    global_indexes = GlobalIndexDocs.model_validate_json(
        reply
    ).indexes  # fetches the list of all the indexes

    print(global_indexes)

    return [index.as_result() for index in global_indexes]


def create_chunks(documents):
    """
    Create chunks using a number of workers in parallel.
    If you get a rate limit error, set the WORKERS to 1.
    """
    chunks = []

    # multi-processing -> spawn multiple pythons and run in parallel (3 different chunks are running in parallel, in the WORKERS variable)
    with Pool(processes=WORKERS) as pool:
        for result in tqdm(
            pool.imap_unordered(process_document, documents), total=len(documents)
        ):
            chunks.extend(result)
    return chunks


def create_document_summaries(documents):
    # creating the chunks 1 one by one here but can also do multi-processing like above create_chunks function
    summaries = []

    for document in tqdm(documents):
        summaries.append(summarize_document(document))

    return summaries


def create_embeddings(chunks, collection_name=COLLECTION_NAME):
    chroma = PersistentClient(path=DB_NAME)
    if collection_name in [c.name for c in chroma.list_collections()]:
        chroma.delete_collection(collection_name)

    texts = [chunk.page_content for chunk in chunks]
    emb = openai.embeddings.create(model=embedding_model, input=texts).data
    vectors = [e.embedding for e in emb]

    collection = chroma.get_or_create_collection(collection_name)

    ids = [str(i) for i in range(len(chunks))]
    metas = [chunk.metadata for chunk in chunks]

    collection.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metas)
    print(f"Vectorstore created with {collection.count()} documents")


if __name__ == "__main__":
    documents = fetch_documents()

    # # 1 document -> multiple chunks
    # chunks = create_chunks(documents)
    # create_embeddings(chunks)

    # # 1 document -> 1 summary 'chunk'
    # document_summaries = create_document_summaries(documents)
    # create_embeddings(
    #     document_summaries, collection_name="doc_summaries"
    # )  # we are embedding the summary documents, so 1 summary document is essentially '1 chunk' because it's small enough and we want the model to be able to query that entire summary.

    # # many document summaries -> a few global index docs
    # global_index_docs = create_global_index_docs(document_summaries)
    # create_embeddings(global_index_docs, collection_name="global_indexes")

    write_employee_records(fetch_documents(EMPLOYEE_RECORDS_PATH))

    print("Ingestion complete")
