import requests
import json
import os
import time

def download_labels(limit=10, output_dir="data/raw"):
    """
    Downloads drug labels from OpenFDA API.
    
    Args:
        limit (int): Number of labels to download.
        output_dir (str): Directory to save JSON files.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Query for recent human prescription drug labels
    # We filter by effective_time to get recent updates
    # We prioritize labels that have 'indications_and_usage' to ensure they are useful
    url = "https://api.fda.gov/drug/label.json"
    params = {
        "search": "effective_time:[20240101 TO 20251231] AND _exists_:indications_and_usage",
        "limit": limit
    }
    
    print(f"Fetching {limit} labels from OpenFDA...")
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return

    results = data.get("results", [])
    print(f"Found {len(results)} labels.")

    for i, result in enumerate(results):
        # robust naming strategy
        openfda = result.get("openfda", {})
        brand_name = openfda.get("brand_name", ["Unknown"])[0]
        generic_name = openfda.get("generic_name", ["Unknown"])[0]
        
        # Prefer brand name, fallback to generic
        name = brand_name if brand_name != "Unknown" else generic_name
        
        # Sanitize filename
        safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
        if not safe_name:
            safe_name = f"Drug_{i}"
            
        filename = os.path.join(output_dir, f"{safe_name}.json")
        
        with open(filename, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Saved: {filename}")

if __name__ == "__main__":
    download_labels()
