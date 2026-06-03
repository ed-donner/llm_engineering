import pandas as pd
import json

from src.retrieval.vector_store import PharmaVectorStore
def run_benchmark():
    store = PharmaVectorStore()
    
    # Load questions
    with open("data/ground_truth.json", "r") as f:
        questions = json.load(f)
    
    results_data = []
    
    for q in questions:
        print(f"Asking: {q['question']}")
        
        # 1. Run Search
        results = store.search(q['question'], k=1)
        
        # 2. Check Retrieval Quality
        top_doc = results['documents'][0][0]
        top_meta = results['metadatas'][0][0] # drug_name, section
        
        # 3. Score it (Did we get the right section?)
        is_correct_section = top_meta['section'] == q['expected_section']
        
        results_data.append({
            "Question": q['question'],
            "Expected Section": q['expected_section'],
            "Retrieved Section": top_meta['section'],
            "Pass": is_correct_section
        })
    # Output Report
    df = pd.DataFrame(results_data)
    print("\n--- BENCHMARK REPORT ---")
    print(df.to_markdown())
if __name__ == "__main__":
    run_benchmark()