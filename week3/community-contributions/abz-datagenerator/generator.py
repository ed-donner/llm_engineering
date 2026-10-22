"""
Flow:  brief description -> expand_spec() -> JSON schema (user-editable)
    schema -> generate_dataset() -> batch LLM -> validation -> dedup -> data rows
"""
from __future__ import annotations

import itertools
import json
import math
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterator, Protocol

FIELD_TYPES = {"string", "integer", "float", "category", "boolean", "date"}

# The list of models can be customized, availability on the HF free tier changes frequently
MODELS = [
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct",
]


# 1. LLM Layer
class LLM(Protocol):
    def chat(self, system: str, user: str, temperature: float = 0.7,
             max_tokens: int = 2048) -> str: ...


class HFChat:
    """A wrapper for huggingface_hub.InferenceClient with simple retry logic."""

    def __init__(self, model: str, token: str | None = None):
        from huggingface_hub import InferenceClient

        self.model = model
        self.client = InferenceClient(model=model, token=token, timeout=120)

    def chat(self, system: str, user: str, temperature: float = 0.7,
             max_tokens: int = 2048) -> str:
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                resp = self.client.chat_completion(
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return resp.choices[0].message.content or ""
            except Exception as e: 
                last_err = e
                time.sleep(2 * (attempt + 1))
        raise RuntimeError(f"Failed to call model {self.model}: {last_err}")


# 2. Parsing JSON from output model 
def extract_json(text: str, want: type | tuple = (dict, list)):
    """Extract the first JSON object of type `want` from the free text."""
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    decoder = json.JSONDecoder()
    for m in re.finditer(r"[\[{]", cleaned):
        try:
            obj, _ = decoder.raw_decode(cleaned[m.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, want):
            return obj
    raise ValueError("No valid JSON found in the model output")


# 3. Specification (schema) of the dataset
SPEC_SYSTEM = """You are a data designer. Convert a short description of a desired \
synthetic dataset into a JSON specification. Respond with JSON only, no explanation.

Format:
{"dataset_name": "string",
 "language": "id",
 "fields": [{"name": "snake_case_english", "type": "string|integer|float|category|boolean|date",
             "description": "what this field contains",
             "allowed_values": ["only for type category"]}],
 "variation_attributes": {"attribute_name": ["3 to 8 diverse values"]}}

Rules:
- 4 to 8 fields. Include one main free-text field if the dataset is text-like.
- Dates use the format YYYY-MM-DD.
- variation_attributes are the hidden dimensions that make rows diverse
  (e.g. commodity, region, tone, severity, season). Provide 2 to 4 of them.
- All values and descriptions should be in Indonesian; field names in English snake_case."""


def validate_spec(spec) -> dict:
    """Validation + normalization of the schema. Raises ValueError with a clear message."""
    if not isinstance(spec, dict):
        raise ValueError("The schema must be aJSON object")
    fields = spec.get("fields")
    if not isinstance(fields, list) or not fields:
        raise ValueError("'fields' must contain at least one field")

    clean_fields, seen = [], set()
    for f in fields:
        if not isinstance(f, dict):
            raise ValueError("Each field must be a JSON object")
        name = str(f.get("name", "")).strip()
        ftype = str(f.get("type", "string")).strip().lower()
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise ValueError(f"Invalid field name: '{name}' (use snake_case)")
        if name in seen:
            raise ValueError(f"Duplicate field name: '{name}'")
        if ftype not in FIELD_TYPES:
            raise ValueError(f"Unknown field type: '{ftype}' {sorted(FIELD_TYPES)}")
        item = {"name": name, "type": ftype, "description": str(f.get("description", ""))}
        if ftype == "category":
            vals = f.get("allowed_values")
            if not isinstance(vals, list) or not vals:
                raise ValueError(f"Category field '{name}' needs 'allowed_values'")
            item["allowed_values"] = [str(v) for v in vals]
        clean_fields.append(item)
        seen.add(name)

    attrs = spec.get("variation_attributes") or {}
    if not isinstance(attrs, dict):
        raise ValueError("'variation_attributes' must be a object")
    clean_attrs = {
        str(k): [str(v) for v in vs]
        for k, vs in attrs.items()
        if isinstance(vs, list) and vs
    }
    return {
        "dataset_name": str(spec.get("dataset_name", "dataset")),
        "language": str(spec.get("language", "id")),
        "fields": clean_fields,
        "variation_attributes": clean_attrs,
    }


def expand_spec(description: str, llm: LLM, retries: int = 3) -> dict:
    """Convert a brief description into a structured schema using LLM."""
    last_err = "unknown"
    for _ in range(retries):
        raw = llm.chat(SPEC_SYSTEM, f"Dataset description: {description}",
                       temperature=0.3, max_tokens=1500)
        try:
            return validate_spec(extract_json(raw, want=dict))
        except ValueError as e:
            last_err = str(e)
    raise ValueError(f"Model failed to create a valid schema ({last_err}). "
                     "Coba lagi, perjelas deskripsi, atau ganti model.")


# 4. Diversity control: variation attributes are selected by the CODE, not by the LLM.
def attribute_stream(attrs: dict[str, list[str]], rng: random.Random) -> Iterator[dict]:
    """Stream of attribute combinations without stopping; all combinations are used evenly."""
    if not attrs:
        while True:
            yield {}
    names = list(attrs)
    size = math.prod(len(v) for v in attrs.values())
    if size <= 5000:
        combos = list(itertools.product(*attrs.values()))
        while True:
            rng.shuffle(combos)
            for c in combos:
                yield dict(zip(names, c))
    while True:
        yield {n: rng.choice(attrs[n]) for n in names}


def meta_column(name: str) -> str:
    return "meta_" + re.sub(r"\W+", "_", name.lower()).strip("_")


# 5. Generate one batch + Validation rows
GEN_SYSTEM = (
    "You generate realistic synthetic data rows. Respond with a JSON array only: "
    "no markdown, no commentary. Every element is an object with exactly the given fields."
)


def build_batch_prompt(spec: dict, attrs: dict, n: int) -> str:
    field_lines = []
    for f in spec["fields"]:
        extra = ""
        if f["type"] == "category":
            extra = f" (pilih salah satu: {', '.join(f['allowed_values'])})"
        elif f["type"] == "date":
            extra = " (format YYYY-MM-DD)"
        field_lines.append(f"- {f['name']} [{f['type']}]{extra}: {f['description']}")
    ctx = "\n".join(f"- {k}: {v}" for k, v in attrs.items()) or "- (bebas)"
    return (
        f"Buat {n} baris data untuk dataset '{spec['dataset_name']}'.\n\n"
        f"Field:\n" + "\n".join(field_lines) + "\n\n"
        f"Konteks batch ini (semua baris harus mencerminkan konteks ini):\n{ctx}\n\n"
        "Aturan:\n"
        "- Teks dalam bahasa Indonesia yang natural dan realistis.\n"
        "- Setiap baris harus berbeda: variasikan kata, panjang, dan detail.\n"
        f"- Keluarkan hanya JSON array berisi {n} objek."
    )


def coerce_row(row, fields: list[dict]) -> dict | None:
    """Check & convert types. Returns None if the row is invalid."""
    if not isinstance(row, dict):
        return None
    out = {}
    for f in fields:
        name, t = f["name"], f["type"]
        if name not in row or row[name] is None or row[name] == "":
            return None
        v = row[name]
        try:
            if t == "string":
                v = str(v).strip()
                if not v:
                    return None
            elif t == "integer":
                v = int(float(v))
            elif t == "float":
                v = float(v)
            elif t == "boolean":
                if isinstance(v, str):
                    low = v.strip().lower()
                    if low in ("true", "ya", "yes"):
                        v = True
                    elif low in ("false", "tidak", "no"):
                        v = False
                    else:
                        return None
                else:
                    v = bool(v)
            elif t == "date":
                v = datetime.strptime(str(v).strip()[:10], "%Y-%m-%d").date().isoformat()
            elif t == "category":
                lookup = {a.lower(): a for a in f["allowed_values"]}
                key = str(v).strip().lower()
                if key not in lookup:
                    return None
                v = lookup[key]
        except (ValueError, TypeError):
            return None
        out[name] = v
    return out


def generate_batch(spec: dict, attrs: dict, n: int, llm: LLM,
                   temperature: float, retries: int = 2) -> list:
    prompt = build_batch_prompt(spec, attrs, n)
    last_err: Exception | None = None
    for _ in range(retries + 1):
        raw = llm.chat(GEN_SYSTEM, prompt, temperature=temperature, max_tokens=2500)
        try:
            return extract_json(raw, want=list)
        except ValueError as e:
            last_err = e
    raise ValueError(f"Batch gagal: {last_err}")

# 6. Dedup
def _tokens(row: dict, fields: list[dict]) -> set:
    text = " ".join(str(row[f["name"]]) for f in fields if f["type"] == "string")
    return set(re.findall(r"\w+", text.lower()))


def _is_near_duplicate(tokens: set, kept: list[set], threshold: float) -> bool:
    if not tokens:
        return False
    for other in kept:
        inter = len(tokens & other)
        if inter and inter / len(tokens | other) >= threshold:
            return True
    return False


# 7. Orchestration
@dataclass
class GenStats:
    batches: int = 0
    failed_batches: int = 0
    raw_rows: int = 0
    invalid_rows: int = 0
    duplicate_rows: int = 0


def generate_dataset(
    spec: dict,
    llm: LLM,
    total: int,
    batch_size: int = 5,
    temperature: float = 0.8,
    similarity_threshold: float = 0.8,
    seed: int = 42,
    on_progress: Callable[[float, str], None] | None = None,
) -> tuple[list[dict], GenStats]:
    spec = validate_spec(spec)
    fields = spec["fields"]
    rng = random.Random(seed)
    stream = attribute_stream(spec["variation_attributes"], rng)

    rows: list[dict] = []
    exact_keys: set[str] = set()
    token_sets: list[set] = []
    stats = GenStats()
    max_batches = math.ceil(total / batch_size) * 3  # limit to avoid infinite loop

    while len(rows) < total and stats.batches < max_batches:
        attrs = stream.__next__()
        need = min(batch_size, total - len(rows))
        stats.batches += 1
        try:
            raw_rows = generate_batch(spec, attrs, need, llm, temperature)
        except Exception:
            stats.failed_batches += 1
            continue

        meta = {meta_column(k): v for k, v in attrs.items()}
        for raw in raw_rows:
            stats.raw_rows += 1
            clean = coerce_row(raw, fields)
            if clean is None:
                stats.invalid_rows += 1
                continue
            key = json.dumps(clean, sort_keys=True, ensure_ascii=False)
            toks = _tokens(clean, fields)
            if key in exact_keys or _is_near_duplicate(toks, token_sets, similarity_threshold):
                stats.duplicate_rows += 1
                continue
            exact_keys.add(key)
            token_sets.append(toks)
            rows.append({**clean, **meta})
            if len(rows) >= total:
                break

        if on_progress:
            on_progress(min(len(rows) / total, 1.0),
                        f"{len(rows)}/{total} rows (batch {stats.batches})")

    return rows, stats
