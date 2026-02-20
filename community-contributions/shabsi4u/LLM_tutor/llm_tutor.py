from dotenv import load_dotenv
import os
from openai import OpenAI
from pathlib import Path
import frontmatter

# Constants
MODEL_GPT = 'gpt-4o-mini'
MODEL_LLAMA = 'llama3.2'
SYSTEM_PROMPT_FILE =  "prompts/system_prompt.txt"
META_PROMPT_FILE = "prompts/meta_prompt.txt"
FEW_SHOTS_PATH = "prompts/few_shots/"


def get_client(model_type="openai"):
    """
    Get OpenAI client configured for either OpenAI API or local Ollama
    
    Args:
        model_type (str): Either "openai" or "ollama"
    
    Returns:
        OpenAI: Configured client instance
    """
    if model_type == "ollama":
        # Local Ollama configuration
        client = OpenAI(
            base_url="http://localhost:11434/v1",  # Local Ollama API
            api_key="ollama"  # Dummy key, required by SDK
        )
        print("✅ Using local Ollama client")
        return client
    
    else:  # Default to OpenAI
        load_dotenv(override=True)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key.startswith('sk-proj-') and len(api_key) > 10:
            # print("✅ API key looks good!")
            pass
        else:
            print("⚠️  There might be a problem with your API key")
            print("Make sure you have set OPENAI_API_KEY in your .env file or environment variables")
        client = OpenAI(api_key=api_key)
        print("✅ Using OpenAI client")
        return client

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: File not found: {file_path}")
        return ""
    except PermissionError:
        print(f"Error: Permission denied reading {file_path}")
        return ""
    except IsADirectoryError:
        print(f"Error: {file_path} is a directory, not a file")
        return ""
    except UnicodeDecodeError as e:
        print(f"Error: Unable to decode {file_path}: {e}")
        return ""
    except Exception as e:
        print(f"Unexpected error reading {file_path}: {e}")
        return ""

def get_system_prompt():
    return read_file(SYSTEM_PROMPT_FILE)

def get_meta_prompt():
    return read_file(META_PROMPT_FILE)

def get_few_shots():
    messages = []
    few_shots_dir = Path(FEW_SHOTS_PATH)
    
    if not few_shots_dir.exists():
        print(f"Warning: Few shots directory {FEW_SHOTS_PATH} does not exist")
        return messages
    
    for path in few_shots_dir.glob("*.md"):
        try:
            post = frontmatter.load(path)
            
            # Validate required fields exist
            if "user" not in post:
                print(f"Warning: Missing 'user' field in {path}")
                continue
                
            if not post.content.strip():
                print(f"Warning: Empty content in {path}")
                continue
            
            messages.append({"role": "user", "content": post["user"]})
            messages.append({"role": "assistant", "content": post.content.strip()})
            
        except Exception as e:
            print(f"Error loading {path}: {e}")
            continue
    
    return messages

def build_messages(system_prompt, user_prompt, few_shots=None):
    messages = [{"role": "system", "content": system_prompt}]
    if few_shots:
        messages.extend(few_shots)
    messages.append({"role": "user", "content": user_prompt})
    return messages

def get_response(model, client, messages, stream=False):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=stream)
    return response


class LLMTutor:
    def __init__(self, model, client):
        self.model = model
        self.client = client

    def get_structured_question(self, question):
        meta_prompt = get_meta_prompt()
        messages = build_messages(meta_prompt, question)
        response = get_response(self.model, self.client, messages)
        return response.choices[0].message.content

    def get_response(self, structured_question, stream=False):
        system_prompt = get_system_prompt()
        few_shots = get_few_shots()
        messages = build_messages(system_prompt, structured_question, few_shots)
        response = get_response(self.model, self.client, messages, stream)
        
        if stream:
            # Handle streaming response
            content = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content += chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content, end="", flush=True)
            print()  # Add newline after streaming
            return content
        else:
            # Handle non-streaming response
            print(response.choices[0].message.content)
            return response.choices[0].message.content

def main():
    try:
        print("Enter the model you want to use: [1] GPT-4o-mini, [2] Llama 3.2 (local)")
        model_choice = input()
        if model_choice == "1":
            model = MODEL_GPT
            client = get_client("openai")
        elif model_choice == "2":
            model = MODEL_LLAMA
            client = get_client("ollama")
        else:
            print("Invalid model choice. Enter 1 for GPT-4o-mini or 2 for Llama 3.2 (local)")
            return
        
        question = input("Enter the question you want to ask: ")
        
        llm_tutor = LLMTutor(model, client)
        recur = True
        while recur:
            print("\nStructuring your question...")
            structured_question = llm_tutor.get_structured_question(question)       
            print("\nGenerating response...")
            response = llm_tutor.get_response(structured_question, stream=True)

            question = input("Do you wish me to answer any of the follow up questions? (y/n): ")
            if question == "y":
                question = input("Enter the follow up question you want to ask: ")
            else:
                recur = False
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
    