# week8/community_contributions/agentic_legal_qna_with_rag_on_bare_acts/modal_expander.py
import os, json, re
from typing import List
import modal

# minimal image: vLLM + torch + HF hub
image = (
    modal.Image.from_registry("nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install(
        "vllm==0.10.2",
        "torch==2.8.0",
        "huggingface_hub[hf_transfer]==0.35.0",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

app = modal.App("legal-query-expander-qwen3-v2", image=image)

MODEL_NAME = "Qwen/Qwen3-4B-Instruct"   # use instruct, defaults everywhere
_llm = None  # warm-container cache


def _extract_json_array(text: str) -> List[str]:
    try:
        parsed = json.loads(text)
        return [x for x in parsed if isinstance(x, str)]
    except Exception:
        pass
    m = re.search(r"\[(?:.|\n|\r)*\]", text)
    if m:
        try:
            parsed = json.loads(m.group(0))
            return [x for x in parsed if isinstance(x, str)]
        except Exception:
            return []
    return []


def _sanitize_and_dedupe(items: List[str], n: int) -> List[str]:
    out, seen = [], set()
    for q in items:
        q = re.sub(r"[^\w\s\-./]", "", (q or "")).strip()
        k = q.lower()
        if q and k not in seen:
            seen.add(k)
            out.append(q)
        if len(out) >= n:
            break
    return out


@app.function(
    image=image,
    gpu=modal.gpu.L4(),  # pick any available GPU (A100/H100 also fine)
    timeout=600,
    secrets=[modal.Secret.from_name("huggingface-secret")],  # set HF token here
)
def expand(question: str, n: int = 5) -> List[str]:
    """
    Return up to n short, diverse retrieval keyphrases for Bare Acts.
    Uses Qwen3-4B-Instruct with its default chat template.
    """
    global _llm
    from vllm import LLM, SamplingParams

    # ensure HF token is available to vLLM
    tok = os.environ.get("HUGGINGFACE_HUB_TOKEN") or os.environ.get("HF_TOKEN")
    if tok and not os.environ.get("HUGGINGFACE_HUB_TOKEN"):
        os.environ["HUGGINGFACE_HUB_TOKEN"] = tok

    if _llm is None:
        _llm = LLM(
            model=MODEL_NAME,
            trust_remote_code=True,
            dtype="auto",
            tensor_parallel_size=1,
        )

    user = (
        "You are Search Query Expander."
        "For given search query you give 4-5 different variants of it to search the database better. It is a legal search query and our database is of legal data like bare acts."
        "Respond ONLY as a JSON array of strings; no prose, no section numbers."
        f"Question:\n{question}\n\n"
        f"Return {n} distinct keyphrases (4–20 words each), which captures the what to search inside rag database. Return as a JSON array. No commentary."
    )

    messages = [
        {"role": "user", "content": user},
    ]

    tokenizer = _llm.get_tokenizer()
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    result = _llm.generate(
        [prompt],
        SamplingParams(
            max_tokens=256,
            temperature=0.2,
        ),
    )
    text = result[0].outputs[0].text

    arr = _sanitize_and_dedupe(_extract_json_array(text), n)

    if not arr:
        # deterministic fallback (keeps things non-empty)
        base = re.sub(r"[?]+$", "", (question or "")).strip()
        pool = [
            f"{base} section",
            f"{base} provision bare act",
            f"{base} indian penal code",
            f"{base} bharatiya nyaya sanhita",
            f"{base} punishment section keywords",
        ]
        arr = _sanitize_and_dedupe(pool, n)

    return arr
