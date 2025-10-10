# imports
import os, json, ast, pathlib
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI
import traceback
from typing import List, Dict
from httpx import Timeout


# ---------- utils ----------
def openai_api_key_loader():
    load_dotenv(dotenv_path=".env", override=True)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No API key found. Please check your .env file.")
        return False
    if not api_key.startswith("sk-proj-"):
        print("⚠️ API key found, but does not start with 'sk-proj-'. Check you're using the right one.")
        return False
    if api_key.strip() != api_key:
        print("⚠️ API key has leading/trailing whitespace. Please clean it.")
        return False
    print("✅ API key found and looks good!")
    return True

def ollama_installed_tags(base_url="http://localhost:11434"):
    r = requests.get(f"{base_url}/api/tags", timeout=10)
    r.raise_for_status()
    return {m["name"] for m in r.json().get("models", [])}

def get_urls(file_name: str):
    with open(f"{file_name}.txt", "r") as f:
        content = f.read()
    url_dict = ast.literal_eval(content)  # expects a dict literal in the file
    return url_dict

def text_from_url(url: str):
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/117.0.0.0 Safari/537.36"
        )
    })
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')

    title = soup.title.string.strip() if soup.title and soup.title.string else "No title found"

    body = soup.body
    if not body:
        return title, ""

    for irrelevant in body(["script", "style", "img", "input", "noscript"]):
        irrelevant.decompose()

    text = body.get_text(separator="\n", strip=True)
    return title, text

# ---------- contestants (Ollama) ----------
def summarize_with_model(text: str, model: str, ollama_client: OpenAI) -> str:
    clipped = text[:9000]  # keep it modest for small models
    messages = [
        {"role": "system", "content": "You are a concise, faithful web summarizer."},
        {"role": "user", "content": (
            "Summarize the article below in 4–6 bullet points. "
            "Be factual, avoid speculation, and do not add information not present in the text.\n\n"
            f"=== ARTICLE START ===\n{clipped}\n=== ARTICLE END ==="
        )}
    ]
    stream = ollama_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        stream=True,
        extra_body={"keep_alive": "30m", "num_ctx": 2048}  
    )
    chunks = []
    for event in stream:
        delta = getattr(event.choices[0].delta, "content", None)
        if delta:
            chunks.append(delta)
    return "".join(chunks).strip()

# ---------- judge (ChatGPT) ----------
JUDGE_MODEL = "gpt-4o-mini"

def judge_summaries(category: str, url: str, source_text: str, summaries: dict, judge_client: OpenAI) -> dict:
    src = source_text[:12000]
    judge_prompt = f"""
                        You are the referee in a web summarization contest.

                        Task:
                        1) Read the SOURCE ARTICLE (below).
                        2) Evaluate EACH SUMMARY on: Coverage, Accuracy/Faithfulness, Clarity/Organization, Conciseness.
                        3) Give a 0–5 integer SCORE for each model (5 best).
                        4) Brief rationale (1–2 sentences per model).
                        5) Choose a single WINNER (tie-break on accuracy then clarity).

                        Return STRICT JSON only with this schema:
                        {{
                        "category": "{category}",
                        "url": "{url}",
                        "scores": {{
                            "<model_name>": {{ "score": <0-5>, "rationale": "<1-2 sentences>" }}
                        }},
                        "winner": "<model_name>"
                        }}

                        SOURCE ARTICLE:
                        {src}

                        SUMMARIES:
                    """
    for m, s in summaries.items():
        judge_prompt += f"\n--- {m} ---\n{s}\n"

    messages = [
        {"role": "system", "content": "You are a strict, reliable evaluation judge for summaries."},
        {"role": "user", "content": judge_prompt}
    ]
    resp = judge_client.chat.completions.create(
                                                model=JUDGE_MODEL,
                                                messages=messages,
                                                response_format={"type": "json_object"},
                                                temperature=0
                                                )
    content = resp.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # fallback: wrap in an envelope if the model added extra text
        start = content.find("{")
        end = content.rfind("}")
        return json.loads(content[start:end+1])


def run_battle(url_dict: Dict[str, str], ollama_client: OpenAI, judge_client: OpenAI, models: List[str]) -> List[dict]:
    all_results = []

    for category, url in url_dict.items():
        title, text = text_from_url(url)
        summaries = {}

        for m in models:
            try:
                summaries[m] = summarize_with_model(text, m, ollama_client)
            except Exception as e:
                print(f"\n--- Error from {m} ---")
                print(repr(e))
                traceback.print_exc()
                summaries[m] = f"[ERROR from {m}: {e}]"

        clean_summaries = {m: s for m, s in summaries.items() if not s.startswith("[ERROR")}
        verdict = judge_summaries(category, url, text, clean_summaries or summaries, judge_client)

        all_results.append(verdict)

    return all_results

def warmup(ollama_client: OpenAI, model: str):
    try:
        ollama_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "OK"}],
            temperature=0,
            extra_body={"keep_alive": "30m"}
        )
    except Exception as e:
        print(f"[warmup] {model}: {e}")



# ---------- main ----------
def main():
    if not openai_api_key_loader():
        return

    # contestants (local Ollama)
    ollama_client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        timeout=Timeout(300.0, connect=30.0)  # generous read/connect timeouts
    )
    # judge (cloud OpenAI)
    judge_client = OpenAI()
    
    available = ollama_installed_tags()
    desired = ["llama3.2:latest", "deepseek-r1:1.5b", "phi3:latest"]  # keep here
    models  = [m for m in desired if m in available]

    print("Available:", sorted(available))
    print("Desired  :", desired)
    print("Running  :", models)

    if not models:
        raise RuntimeError(f"No desired models installed. Have: {sorted(available)}")

    url_dict = get_urls(file_name="urls")
    

    for m in models:
        warmup(ollama_client, m)
    results = run_battle(url_dict, ollama_client, judge_client, models)

    pathlib.Path("battle_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
