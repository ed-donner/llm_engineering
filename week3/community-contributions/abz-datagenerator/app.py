"""Gradio interface"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

import gradio as gr
import pandas as pd

from evaluator import summarize
from generator import MODELS, HFChat, expand_spec, generate_dataset, validate_spec
from presets import PRESETS

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")


def _make_llm(model: str, token: str) -> HFChat:
    token = (token or "").strip() or os.getenv("HF_TOKEN", "")
    if not token:
        raise gr.Error("Hugging Face token is not filled. Fill in the token column or set env HF_TOKEN.")
    return HFChat(model, token)


def on_preset(name: str) -> str:
    return PRESETS.get(name, "")


def on_build_spec(description: str, model: str, token: str):
    if not description or not description.strip():
        raise gr.Error("Write a description of the dataset first.")
    llm = _make_llm(model, token)
    try:
        spec = expand_spec(description.strip(), llm)
    except Exception as e:
        raise gr.Error(str(e))
    return (
        json.dumps(spec, indent=2, ensure_ascii=False),
        "The schema has been successfully created. Review or edit it if necessary, then open the **Generate** tab.",
    )


def on_generate(spec_text, total, batch_size, temperature, threshold, model, token,
                progress=gr.Progress()):
    try:
        spec = validate_spec(json.loads(spec_text))
    except (json.JSONDecodeError, ValueError) as e:
        raise gr.Error(f"Schema is notvalid: {e}")
    llm = _make_llm(model, token)

    rows, stats = generate_dataset(
        spec, llm, int(total), int(batch_size), float(temperature), float(threshold),
        on_progress=lambda frac, msg: progress(frac, desc=msg),
    )
    if not rows:
        raise gr.Error("No valid rows generated. Try a different model, "
                       "reduce batch size, or simplify the schema.")

    df = pd.DataFrame(rows)
    out_dir = tempfile.mkdtemp()
    csv_path = os.path.join(out_dir, "dataset.csv")
    jsonl_path = os.path.join(out_dir, "dataset.jsonl")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")  # utf-8-sig for clean excel
    df.to_json(jsonl_path, orient="records", lines=True, force_ascii=False)

    status = f"Done: {len(df)} rows. Download below the table."
    return df, [csv_path, jsonl_path], summarize(df, spec, stats, int(total)), status


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="AgriSynth") as demo:
        gr.Markdown(
            "# AgriSynth\nSynthetic data generator for agricultural data in Indonesian. "
            "Tulis deskripsi singkat, tinjau skema, lalu generate."
        )
        with gr.Row():
            model = gr.Dropdown(MODELS, value=MODELS[0], label="Model Hugging Face",
                                allow_custom_value=True)
            token = gr.Textbox(label="HF Token (opsional jika HF_TOKEN sudah di-set)",
                               type="password")

        with gr.Tabs():
            with gr.Tab("1. Skema"):
                preset = gr.Dropdown(list(PRESETS), value="(Tulis sendiri)", label="Preset")
                desc = gr.Textbox(lines=4, label="Deskripsi dataset",
                                  placeholder="Contoh: keluhan petani cabai tentang hama...")
                build_btn = gr.Button("Buat Skema", variant="primary")
                spec_status = gr.Markdown()
                spec_box = gr.Code(language="json", label="Skema (bisa diedit)",
                                   interactive=True, lines=18)

            with gr.Tab("2. Generate"):
                with gr.Row():
                    total = gr.Slider(10, 200, value=30, step=10, label="Jumlah baris")
                    batch = gr.Slider(3, 10, value=5, step=1, label="Ukuran batch")
                with gr.Row():
                    temp = gr.Slider(0.3, 1.2, value=0.8, step=0.1, label="Temperature")
                    thr = gr.Slider(0.5, 0.95, value=0.8, step=0.05,
                                    label="Batas kemiripan (dedup)")
                gen_btn = gr.Button("Generate", variant="primary")
                gen_status = gr.Markdown()
                table = gr.Dataframe(label="Hasil", wrap=True)
                files = gr.File(label="Unduh (CSV & JSONL)", file_count="multiple")

            with gr.Tab("3. Evaluasi"):
                report = gr.Markdown("Jalankan generate terlebih dahulu.")

        preset.change(on_preset, preset, desc)
        build_btn.click(on_build_spec, [desc, model, token], [spec_box, spec_status])
        gen_btn.click(on_generate, [spec_box, total, batch, temp, thr, model, token],
                      [table, files, report, gen_status])
    return demo


demo = build_ui()

if __name__ == "__main__":
    demo.queue().launch()
