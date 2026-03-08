"""
Week 6 capstone implementation for "The Price Is Right".

This script turns the day-by-day notebook flow into a reusable project with
commands for:
- planning requirements
- building baseline models
- evaluating model quality
- preparing OpenAI fine-tuning JSONL files
- starting and tracking fine-tune jobs
- deploying a local Gradio app
"""

from __future__ import annotations

import argparse
import json
import math
import os
import pickle
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from types import SimpleNamespace
from typing import Any

import gradio as gr
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI


HERE = Path(__file__).resolve()
WEEK6_DIR = HERE.parents[3]
REPO_ROOT = HERE.parents[4]
ARTIFACTS_DIR = HERE.parent / "artifacts"
JSONL_DIR = ARTIFACTS_DIR / "jsonl"
MODEL_PATH = ARTIFACTS_DIR / "model_bundle.pkl"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"

if str(WEEK6_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK6_DIR))

from pricer.items import Item  # noqa: E402


PRICE_REGEX = re.compile(r"[-+]?\d*\.\d+|\d+")
PROMPT = "Estimate the price of this product. Respond with only the price."
DEFAULT_DATASET_OWNER = "ed-donner"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_REMOTE_MODEL = "openai/gpt-4.1-mini"


def get_openrouter_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Set OPENROUTER_API_KEY (or OPENAI_API_KEY fallback) for remote inference.")
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Set OPENAI_API_KEY for OpenAI fine-tuning commands.")
    return OpenAI(api_key=api_key)


def resolve_remote_model(cli_value: str | None) -> str:
    """Pick remote model from CLI/env; default when OpenRouter key exists."""
    if cli_value:
        return cli_value
    env_model = os.getenv("REMOTE_MODEL") or os.getenv("FINE_TUNED_MODEL")
    if env_model:
        return env_model
    if os.getenv("OPENROUTER_API_KEY"):
        return DEFAULT_REMOTE_MODEL
    return ""


@dataclass
class ModelBundle:
    vocabulary: list[str]
    weights_text: list[float]
    tabular_weights: list[float]
    avg_price: float

    def _item_text(self, item: Any) -> str:
        return getattr(item, "summary", None) or getattr(item, "full", None) or getattr(item, "title", "")

    def _item_features(self, item: Any) -> list[float]:
        text = self._item_text(item)
        weight = float(getattr(item, "weight", 0) or 0)
        return [weight, 1.0 if weight == 0 else 0.0, float(len(text))]

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def _vectorize_text(self, text: str) -> np.ndarray:
        token_counts = Counter(self._tokenize(text))
        # log-scaled term counts keep dimensions stable and reduce outlier impact.
        vec = np.array([math.log1p(token_counts.get(token, 0)) for token in self.vocabulary], dtype=float)
        return vec

    def predict(self, item: Any) -> float:
        text = self._item_text(item)
        if not text.strip():
            return self.avg_price
        text_vec = self._vectorize_text(text)
        pred_text = float(np.dot(text_vec, np.array(self.weights_text, dtype=float)))
        tab_vec = np.array(self._item_features(item), dtype=float)
        pred_tab = float(np.dot(tab_vec, np.array(self.tabular_weights, dtype=float)))
        blended = (0.75 * pred_text) + (0.25 * pred_tab)
        return max(0.0, blended)


def extract_price(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("$", "").replace(",", "")
    match = PRICE_REGEX.search(text)
    return float(match.group(0)) if match else 0.0


def load_items(lite_mode: bool) -> tuple[list[Item], list[Item], list[Item]]:
    dataset_name = f"{DEFAULT_DATASET_OWNER}/items_lite" if lite_mode else f"{DEFAULT_DATASET_OWNER}/items_full"
    train, val, test = Item.from_hub(dataset_name)
    return train, val, test


def limit_items(items: list[Item], size: int | None) -> list[Item]:
    if size is None or size <= 0:
        return items
    return items[: min(size, len(items))]


def evaluate_predictor(predictor, items: list[Item], size: int) -> dict[str, float]:
    subset = items[: min(size, len(items))]
    truths = np.array([float(item.price) for item in subset], dtype=float)
    preds = np.array([extract_price(predictor(item)) for item in subset], dtype=float)
    errors = np.abs(truths - preds)
    within_20 = float(np.mean(errors <= 20) * 100) if len(errors) else 0.0
    rmse = float(np.sqrt(np.mean((truths - preds) ** 2))) if len(truths) else 0.0
    if len(truths):
        tss = float(np.sum((truths - truths.mean()) ** 2))
        rss = float(np.sum((truths - preds) ** 2))
        r2 = 0.0 if tss == 0 else 1 - (rss / tss)
    else:
        r2 = 0.0
    return {
        "count": float(len(subset)),
        "mae": float(np.mean(errors)) if len(errors) else 0.0,
        "rmse": rmse,
        "r2": float(r2),
        "within_20_pct": within_20,
    }


def fit_ridge(x: np.ndarray, y: np.ndarray, alpha: float = 1.0) -> np.ndarray:
    if x.size == 0 or x.shape[1] == 0:
        return np.zeros((x.shape[1],), dtype=float)
    n_features = x.shape[1]
    xtx = x.T @ x
    reg = alpha * np.eye(n_features)
    return np.linalg.solve(xtx + reg, x.T @ y)


def build_vocabulary(texts: list[str], max_features: int = 2500, min_count: int = 3) -> list[str]:
    counts: Counter[str] = Counter()
    for text in texts:
        counts.update(re.findall(r"[a-z0-9]+", text.lower()))
    tokens = [token for token, count in counts.items() if count >= min_count]
    tokens.sort(key=lambda tok: counts[tok], reverse=True)
    return tokens[:max_features]


def vectorize_texts(texts: list[str], vocabulary: list[str]) -> np.ndarray:
    rows: list[np.ndarray] = []
    for text in texts:
        token_counts = Counter(re.findall(r"[a-z0-9]+", text.lower()))
        row = np.array([math.log1p(token_counts.get(token, 0)) for token in vocabulary], dtype=float)
        rows.append(row)
    return np.vstack(rows) if rows else np.zeros((0, len(vocabulary)), dtype=float)


def train_bundle(train_items: list[Item]) -> ModelBundle:
    texts = [(item.summary or item.full or item.title or "").strip() for item in train_items]
    prices = np.array([float(item.price) for item in train_items])
    vocabulary = build_vocabulary(texts, max_features=2500, min_count=3)
    x_text = vectorize_texts(texts, vocabulary)
    weights_text = fit_ridge(x_text, prices, alpha=3.0)

    tabular_x = []
    for item, text in zip(train_items, texts):
        weight = float(item.weight or 0)
        tabular_x.append([weight, 1.0 if weight == 0 else 0.0, float(len(text))])
    x_tab = np.array(tabular_x, dtype=float)
    tabular_weights = fit_ridge(x_tab, prices, alpha=0.5)
    return ModelBundle(
        vocabulary=vocabulary,
        weights_text=weights_text.tolist(),
        tabular_weights=tabular_weights.tolist(),
        avg_price=float(mean(prices)) if len(prices) else 0.0,
    )


def save_bundle(bundle: ModelBundle) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with MODEL_PATH.open("wb") as f:
        pickle.dump(bundle, f)


def load_bundle() -> ModelBundle:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Missing model artifact at: {MODEL_PATH}")
    with MODEL_PATH.open("rb") as f:
        return pickle.load(f)


def print_requirements_plan() -> None:
    plan = {
        "day_1_data_curation": [
            "Load Amazon Reviews 2023 metadata by category.",
            "Filter prices into realistic range and clean product text.",
            "Drop low-quality rows and standardize item objects.",
        ],
        "day_2_preprocessing": [
            "Rewrite raw text into concise standardized summaries.",
            "Persist train/validation/test datasets for fast reuse.",
            "Track token and API cost for rewrite stage.",
        ],
        "day_3_baselines_eval": [
            "Build random and constant baselines first.",
            "Train traditional regressors over text/features.",
            "Evaluate with MAE, RMSE, R2, and error threshold metrics.",
        ],
        "day_4_neural_llm": [
            "Benchmark against neural and zero/few-shot LLM pricing.",
            "Compare quality against human/heuristic estimates.",
            "Capture failure modes and price-range outliers.",
        ],
        "day_5_frontier_finetuning": [
            "Create OpenAI fine-tune JSONL train/validation files.",
            "Launch fine-tuning job with controlled hyperparameters.",
            "Evaluate fine-tuned model on held-out test items.",
        ],
        "build_deploy_expectation": [
            "Package into reusable CLI commands.",
            "Provide reproducible setup + test checklist.",
            "Offer local deployment surface (Gradio app).",
        ],
    }
    print(json.dumps(plan, indent=2))


def make_messages(item: Item) -> list[dict[str, str]]:
    text = item.summary or item.full or item.title
    return [
        {"role": "system", "content": "You estimate product prices. Return only the numeric price."},
        {"role": "user", "content": f"{PROMPT}\n\n{text}"},
        {"role": "assistant", "content": f"${float(item.price):.2f}"},
    ]


def write_finetune_jsonl(items: list[Item], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            line = {"messages": make_messages(item)}
            f.write(json.dumps(line))
            f.write("\n")


def start_finetune(train_path: Path, val_path: Path, base_model: str, epochs: int) -> dict[str, str]:
    client = get_openai_client()
    with train_path.open("rb") as f:
        train_file = client.files.create(file=f, purpose="fine-tune")
    with val_path.open("rb") as f:
        val_file = client.files.create(file=f, purpose="fine-tune")

    job = client.fine_tuning.jobs.create(
        training_file=train_file.id,
        validation_file=val_file.id,
        model=base_model,
        hyperparameters={"n_epochs": int(epochs), "batch_size": 1},
        seed=42,
        suffix="week6-pricer",
    )
    return {"job_id": job.id, "training_file_id": train_file.id, "validation_file_id": val_file.id}


def fine_tune_status(job_id: str) -> dict[str, Any]:
    client = get_openai_client()
    job = client.fine_tuning.jobs.retrieve(job_id)
    events = client.fine_tuning.jobs.list_events(fine_tuning_job_id=job_id, limit=5)
    return {
        "id": job.id,
        "status": job.status,
        "fine_tuned_model": getattr(job, "fine_tuned_model", None),
        "trained_tokens": getattr(job, "trained_tokens", None),
        "latest_events": [event.message for event in events.data],
    }


def predict_with_remote_model(model_id: str, product_text: str) -> float:
    client = get_openai_client() if model_id.startswith("ft:") else get_openrouter_client()
    response = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": f"{PROMPT}\n\n{product_text}"}],
        temperature=0.0,
    )
    content = response.choices[0].message.content or "0"
    return extract_price(content)


def command_plan(_: argparse.Namespace) -> None:
    print_requirements_plan()


def command_build(args: argparse.Namespace) -> None:
    train, val, _ = load_items(lite_mode=args.lite_mode)
    train = limit_items(train, args.train_size)
    val = limit_items(val, args.val_size)

    bundle = train_bundle(train)
    save_bundle(bundle)

    metrics = {
        "config": {"lite_mode": args.lite_mode, "train_size": len(train), "val_size": len(val)},
        "validation": evaluate_predictor(bundle.predict, val, size=len(val)),
    }
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


def command_evaluate(args: argparse.Namespace) -> None:
    _, _, test = load_items(lite_mode=args.lite_mode)
    test = limit_items(test, args.test_size)
    bundle = load_bundle()

    report = {"local_bundle": evaluate_predictor(bundle.predict, test, size=len(test))}
    remote_model = resolve_remote_model(args.remote_model)
    if remote_model:
        sample = test[: min(args.fine_tuned_sample, len(test))]
        ft_metrics = evaluate_predictor(
            lambda item: predict_with_remote_model(remote_model, item.summary or item.full or item.title),
            sample,
            size=len(sample),
        )
        report["remote_model"] = ft_metrics
    print(json.dumps(report, indent=2))


def command_prepare_finetune(args: argparse.Namespace) -> None:
    train, val, _ = load_items(lite_mode=args.lite_mode)
    train = limit_items(train, args.train_size)
    val = limit_items(val, args.val_size)

    train_path = JSONL_DIR / "fine_tune_train.jsonl"
    val_path = JSONL_DIR / "fine_tune_validation.jsonl"
    write_finetune_jsonl(train, train_path)
    write_finetune_jsonl(val, val_path)
    result = {
        "train_path": str(train_path),
        "validation_path": str(val_path),
        "train_examples": len(train),
        "validation_examples": len(val),
    }
    print(json.dumps(result, indent=2))


def command_start_finetune(args: argparse.Namespace) -> None:
    train_path = JSONL_DIR / "fine_tune_train.jsonl"
    val_path = JSONL_DIR / "fine_tune_validation.jsonl"
    if not train_path.exists() or not val_path.exists():
        raise FileNotFoundError("Missing JSONL files. Run `prepare-finetune` first.")

    result = start_finetune(
        train_path=train_path,
        val_path=val_path,
        base_model=args.base_model,
        epochs=args.epochs,
    )
    print(json.dumps(result, indent=2))


def command_status_finetune(args: argparse.Namespace) -> None:
    print(json.dumps(fine_tune_status(args.job_id), indent=2))


def command_deploy(args: argparse.Namespace) -> None:
    bundle = load_bundle()
    remote_model = resolve_remote_model(args.remote_model)

    def infer(product_text: str) -> tuple[str, str, str]:
        if not product_text.strip():
            return "", "", "Provide a product description."
        item = SimpleNamespace(summary=product_text, full=product_text, title="User input", weight=0)
        local_price = bundle.predict(item)

        local_msg = f"${local_price:.2f}"
        ft_msg = "Not configured (set OPENROUTER_API_KEY or --remote-model)"
        if remote_model:
            try:
                ft_price = predict_with_remote_model(remote_model, product_text)
                ft_msg = f"${ft_price:.2f}"
            except Exception as exc:  # noqa: BLE001
                ft_msg = f"Error: {exc}"
        winner = "Local bundle" if ft_msg == "Not configured" else "Compare both estimates."
        return local_msg, ft_msg, winner

    demo = gr.Interface(
        fn=infer,
        inputs=gr.Textbox(
            lines=8,
            label="Product Description",
            placeholder="Paste title + features + details to estimate price...",
        ),
        outputs=[
            gr.Textbox(label="Local Model Estimate"),
            gr.Textbox(label="Fine-Tuned Model Estimate"),
            gr.Textbox(label="Notes"),
        ],
        title="Week 6 Price Is Right - Capstone Deployment",
        description="Estimate product prices with the trained local model and optionally a fine-tuned OpenAI model.",
    )
    demo.launch(server_name=args.host, server_port=args.port, share=args.share)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Week 6 Price Is Right capstone CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_cmd = sub.add_parser("plan", help="Print end-to-end requirements and execution plan")
    plan_cmd.set_defaults(func=command_plan)

    build_cmd = sub.add_parser("build", help="Train and persist baseline model bundle")
    build_cmd.add_argument("--lite-mode", action="store_true", help="Use ed-donner/items_lite dataset")
    build_cmd.add_argument("--train-size", type=int, default=12000, help="Training item count cap")
    build_cmd.add_argument("--val-size", type=int, default=3000, help="Validation item count cap")
    build_cmd.set_defaults(func=command_build)

    eval_cmd = sub.add_parser("evaluate", help="Evaluate local model and optional fine-tuned model")
    eval_cmd.add_argument("--lite-mode", action="store_true", help="Use ed-donner/items_lite dataset")
    eval_cmd.add_argument("--test-size", type=int, default=1500, help="Test item count cap")
    eval_cmd.add_argument(
        "--remote-model",
        type=str,
        default="",
        help="Remote model id (OpenRouter model, or OpenAI ft: model)",
    )
    eval_cmd.add_argument("--fine-tuned-sample", type=int, default=150, help="Eval sample size for fine-tuned model")
    eval_cmd.set_defaults(func=command_evaluate)

    prep_cmd = sub.add_parser("prepare-finetune", help="Build train/validation JSONL for OpenAI fine-tuning")
    prep_cmd.add_argument("--lite-mode", action="store_true", help="Use ed-donner/items_lite dataset")
    prep_cmd.add_argument("--train-size", type=int, default=100, help="Fine-tune train rows")
    prep_cmd.add_argument("--val-size", type=int, default=50, help="Fine-tune validation rows")
    prep_cmd.set_defaults(func=command_prepare_finetune)

    start_cmd = sub.add_parser("start-finetune", help="Upload JSONL and create fine-tune job")
    start_cmd.add_argument("--base-model", default="gpt-4.1-nano-2025-04-14", help="OpenAI base model id")
    start_cmd.add_argument("--epochs", type=int, default=1, help="Fine-tuning epochs")
    start_cmd.set_defaults(func=command_start_finetune)

    status_cmd = sub.add_parser("status-finetune", help="Check OpenAI fine-tune job status")
    status_cmd.add_argument("job_id", help="Fine-tuning job id")
    status_cmd.set_defaults(func=command_status_finetune)

    deploy_cmd = sub.add_parser("deploy", help="Launch Gradio app for local deployment")
    deploy_cmd.add_argument(
        "--remote-model",
        default="",
        help="Remote model id (OpenRouter model, or OpenAI ft: model)",
    )
    deploy_cmd.add_argument("--host", default="127.0.0.1", help="Gradio host")
    deploy_cmd.add_argument("--port", type=int, default=7866, help="Gradio port")
    deploy_cmd.add_argument("--share", action="store_true", help="Enable temporary public Gradio URL")
    deploy_cmd.set_defaults(func=command_deploy)
    return parser


def main() -> None:
    # Load env vars from both repo root and project folder.
    # Shell-provided env vars keep priority (override=False).
    load_dotenv(REPO_ROOT / ".env", override=False)
    load_dotenv(HERE.parent / ".env", override=False)
    load_dotenv(override=False)
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
