"""
Retrieval evaluation metrics (MRR, nDCG, keyword coverage) for the bugs RAG.
"""
import math
from pydantic import BaseModel, Field


class RetrievalEval(BaseModel):
    """Evaluation metrics for retrieval performance."""

    mrr: float = Field(description="Mean Reciprocal Rank - average across all keywords")
    ndcg: float = Field(description="Normalized Discounted Cumulative Gain (binary relevance)")
    keywords_found: int = Field(description="Number of keywords found in top-k results")
    total_keywords: int = Field(description="Total number of keywords to find")
    keyword_coverage: float = Field(description="Percentage of keywords found")


def calculate_mrr(keyword: str, retrieved_docs: list) -> float:
    """Calculate reciprocal rank for a single keyword (case-insensitive)."""
    keyword_lower = keyword.lower()
    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword_lower in doc.page_content.lower():
            return 1.0 / rank
    return 0.0


def calculate_dcg(relevances: list, k: int) -> float:
    """Calculate Discounted Cumulative Gain."""
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)  # rank starts at 1
    return dcg


def calculate_ndcg(keyword: str, retrieved_docs: list, k: int = 10) -> float:
    """Calculate nDCG for a single keyword (binary relevance, case-insensitive)."""
    keyword_lower = keyword.lower()
    relevances = [
        1 if keyword_lower in doc.page_content.lower() else 0
        for doc in retrieved_docs[:k]
    ]
    dcg = calculate_dcg(relevances, k)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = calculate_dcg(ideal_relevances, k)
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_retrieval_from_docs(
    keywords: list[str], retrieved_docs: list, k: int = 10
) -> RetrievalEval:
    """Compute retrieval metrics from keywords and already-retrieved docs."""
    mrr_scores = [calculate_mrr(kw, retrieved_docs) for kw in keywords]
    ndcg_scores = [calculate_ndcg(kw, retrieved_docs, k) for kw in keywords]
    keywords_found = sum(1 for s in mrr_scores if s > 0)
    total_keywords = len(keywords)
    keyword_coverage = (keywords_found / total_keywords * 100) if total_keywords > 0 else 0.0
    return RetrievalEval(
        mrr=sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0,
        ndcg=sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0,
        keywords_found=keywords_found,
        total_keywords=total_keywords,
        keyword_coverage=keyword_coverage,
    )
