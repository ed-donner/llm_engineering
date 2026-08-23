import os
import math
from pathlib import Path
from unicodedata import category
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI
from langchain_chroma import Chroma
import json


load_dotenv(override=True)

DB_NAME = str(Path(__file__).parent.parent.parent / "vector_db")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
retriever = Chroma(persist_directory=DB_NAME, embedding_function=embeddings).as_retriever()

GEMINI_KEY = os.getenv('GEMINI_API_KEY')
# client = OpenAI(base_url="https://generativelanguage.googleapis.com/v1beta", api_key=GEMINI_KEY)
# client = OpenAI(base_url="http://localhost:11434/v1", api_key=GEMINI_KEY)
client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv('GROQ_API_KEY'))

#TestQuestion pydantic format
class TestQuestion(BaseModel):
    question: str = Field(description="The question the user wants to ask")
    keywords: list[str] = Field(description="The keywords that must be present in the retrieved documents")
    reference_answer: str = Field(description="The ideal refernce answer to the question")
    category: str = Field(description="The category in which the question belongs to. i.e, spanning, numerical, direct_fact, holistic")

def load_tests() ->list[TestQuestion]:
    TEST_FILE = str(Path(__file__).parent.parent / "tests.jsonl")
    tests = []
    with open(TEST_FILE, 'r', encoding="utf-8") as f:
        for line in f:
            data = json.loads(line.strip())
            tests.append(TestQuestion(**data))
    return tests

#retieval evaluation result pydantic format
class RetrievalEval(BaseModel):
    mrr: float = Field(description="The MRR score for the test")
    ndcg: float = Field(description="The NDCG score for the test")
    keyword_coverage: float = Field(description="Keyword coverage for the test")

#answer evaluation result pydantic format
class AnswerEval(BaseModel):
    feedback: str = Field(description="The llm evaluator's feedback regarding the evaluation results")
    accuracy: int = Field(description="Accuracy score")
    completeness: int = Field(description="Completeness score")
    relevance: int = Field(description="Relevance score")

def answer(question) ->str:
    SYSTEM_PROMPT = """"You are an assistant representing a company called InsureLLM
    Your task is to respond to the user's questions regarding InsureLLM only.
    You will be provided with context relevant to the user's question where applicable.
    Be as concise and accurate as possible. If you don't know the answer to the question please say so.
    Do not answer questions outside the InsureLLM company context and if a user asks a question outside the context, differ from answering it and encourage the user to maintain the
    to maintain the InsureLLM context in a polite manner.
    Do not guess answers to questions, instead, use the given context if available. If you don't know the answer, say so.

    Context:
    {context}
    """
    docs = retriever.invoke(question)
    context = "\n".join(doc.page_content for doc in docs)
    system_message = SYSTEM_PROMPT.format(context=context)

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": question},
        ],
        temperature=0
    )
    return response.choices[0].message.content


#ndcg, mrr, keyword_coverage

def calculate_ndcg(keyword: str, retrieved_docs: list) ->float:
    key_rel = [1 if keyword.lower() in doc.page_content.lower() else 0 for doc in retrieved_docs]
    dcg = sum(rel/math.log2(rank + 1) for rank, rel in enumerate(key_rel, start=1))
    key_rel.sort(reverse=True)
    idcg = sum(rel/math.log2(rank + 1) for rank, rel in enumerate(key_rel, start=1))
    return dcg / idcg if idcg > 0 else 0.0

def calculate_mrr(keyword: str, retrieved_docs: list) ->float:
    key_rel = [1 if keyword.lower() in doc.page_content.lower() else 0 for doc in retrieved_docs]
    for rank, rel in enumerate(key_rel, start=1):
        if rel > 0:
            return 1/rank
    return 0.0

def calculate_keyword_coverage(keywords: list, retrieved_docs: list) ->float:
    mrr_scores = [calculate_mrr(key, retrieved_docs) for key in keywords]
    keys_found = sum(1 if mrr > 0 else 0 for mrr in mrr_scores)
    return keys_found / len(mrr_scores) * 100

#retrival evaluation

def evaluate_retrieval(test: TestQuestion) ->RetrievalEval:
    docs = retriever.invoke(test.question)
    mrr = sum(calculate_mrr(key, docs) for key in test.keywords) / len(test.keywords)
    ndcg = sum(calculate_ndcg(key, docs) for key in test.keywords) / len(test.keywords)
    keyword_coverage = calculate_keyword_coverage(test.keywords, docs)

    return RetrievalEval(
        mrr=mrr,
        ndcg=ndcg,
        keyword_coverage=keyword_coverage
    )

def evaluate_answer(test: TestQuestion) ->AnswerEval:
    llm_response = answer(test.question)
    judge_messages = [
        {
            "role": "system",
            "content": "You are an expert evaluator assessing the quality of answers. Evaluate the generated answer by comparing it to the reference answer. Only give 5/5 scores for perfect answers.",
        },
        {
            "role": "user",
            "content": f"""Question:
{test.question}

Generated Answer:
{llm_response}

Reference Answer:
{test.reference_answer}

Please evaluate the generated answer on three dimensions:
1. Accuracy: How factually correct is it compared to the reference answer? Only give 5/5 scores for perfect answers.
2. Completeness: How thoroughly does it address all aspects of the question, covering all the information from the reference answer?
3. Relevance: How well does it directly answer the specific question asked, giving no additional information?

Provide detailed feedback and scores from 1 (very poor) to 5 (ideal) for each dimension. If the answer is wrong, then the accuracy score must be 1.""",
        },
    ]
    response = client.chat.completions.parse(
        model="openai/gpt-oss-20b",
        messages=judge_messages,
        response_format=AnswerEval
    )

    result = response.choices[0].message.content
    try:
        return AnswerEval.model_validate_json(result)
    except ValidationError as e:
        print(f"Encountered a validation error: {e}")

    

def evaluate_all_retrieval():
    tests = load_tests()
    total_tests = len(tests[100:])
    for index, test in enumerate(tests[100:], start=1):
        result = evaluate_retrieval(test)
        progress = index/total_tests
        yield test, result, progress

def evaluate_all_answers():
    tests = load_tests()
    total_tests = len(tests[100:])
    for index, test in enumerate(tests[100:], start=1):
        result = evaluate_answer(test)
        progress = index/total_tests
        yield test, result, progress
