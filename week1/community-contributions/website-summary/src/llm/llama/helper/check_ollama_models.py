# src/llm/llama/helper/check_ollama_model_names.py
import requests

def list_ollama_models():
    """List all models available in Ollama with their exact names"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models_data = response.json()
            print("Available models in Ollama:")
            
            if "models" in models_data and models_data["models"]:
                for i, model in enumerate(models_data["models"], 1):
                    print(f"{i}. {model['name']}")
                
                print("\nTo use a specific model, update the default_model in llama_client.py")
            else:
                print("No models found in the response")
                print(f"Raw response: {models_data}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error connecting to Ollama API: {str(e)}")

if __name__ == "__main__":
    list_ollama_models()
