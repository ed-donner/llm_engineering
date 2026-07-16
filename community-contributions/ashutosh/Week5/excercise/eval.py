from judges.completeness import evaluate_completeness
from judges.faithfulness import evaluate_faithfulness
from judges.answer_relevancy import evaluate_answer_relevance
from judges.retrieval_relevancy import evaluate_retrieval_relevance
from answer import answer_question

def evaluate_response(query, chunks, answer):
    retrieval_relevance_result = evaluate_retrieval_relevance(query, chunks)
    faithfulness_result = evaluate_faithfulness(chunks, answer)
    completeness_result = evaluate_completeness(query, chunks, answer)
    answer_relevance_result = evaluate_answer_relevance(query, answer)

    return {
        "retrieval_relevance": retrieval_relevance_result,
        "faithfulness": faithfulness_result,
        "completeness": completeness_result,
        "answer_relevance": answer_relevance_result,
    }

if __name__ == "__main__":
    query = "What is KL divergence?"
    answer, chunks = answer_question(query)
    print("Answer: ", answer)
    print("\nRetrieved Context:")
    for doc in chunks: 
        print(f"Source: {doc.metadata['source']}")
        print(doc.page_content[:50])
        print("\n---\n")
    evaluation_results = evaluate_response(query, chunks, answer)
    print("Evaluation Results:")
    for metric, result in evaluation_results.items():
        print(f"{metric.capitalize()}: {result.score:.2f}")
        print(f"Reasoning: {result.reasoning[:100]}\n")
    