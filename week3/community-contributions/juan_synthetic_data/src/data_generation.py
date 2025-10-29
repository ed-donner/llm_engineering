import os
from typing import List

import pandas as pd
from PIL import Image

from src.constants import MAX_TOKENS_MODEL, N_REFERENCE_ROWS
from src.evaluator import SimpleEvaluator
from src.helpers import hash_row, sample_reference
from src.openai_utils import detect_total_rows_from_prompt, generate_batch


# ------------------- Main Function -------------------
def generate_and_evaluate_data(
    system_prompt: str,
    user_prompt: str,
    temp_dir: str,
    reference_file=None,
    openai_model: str = "gpt-4o-mini",
    max_tokens_model: int = MAX_TOKENS_MODEL,
    n_reference_rows: int = N_REFERENCE_ROWS,
):
    """
    Generate synthetic data in batches, evaluate against reference data, and save results.
    Uses dynamic batching and reference sampling to optimize cost and token usage.
    """
    os.makedirs(temp_dir, exist_ok=True)
    reference_df = pd.read_csv(reference_file) if reference_file else None
    total_rows = detect_total_rows_from_prompt(user_prompt, openai_model)

    final_df = pd.DataFrame()
    existing_hashes = set()
    rows_left = total_rows
    iteration = 0

    print(f"[Info] Total rows requested: {total_rows}")

    # Estimate tokens for the prompt by adding system, user and sample (used once per batch)
    prompt_sample = f"{system_prompt}  {user_prompt}  {sample_reference(reference_df, n_reference_rows)}"
    prompt_tokens = max(1, len(prompt_sample) // 4)

    # Estimate tokens per row dynamically using a sample
    example_sample = sample_reference(reference_df, n_reference_rows)
    if example_sample is not None and len(example_sample) > 0:
        sample_text = str(example_sample)
        tokens_per_row = max(1, len(sample_text) // len(example_sample) // 4)
    else:
        tokens_per_row = 30  # fallback if no reference

    print(f"[Info] Tokens per row estimate: {tokens_per_row}, Prompt tokens: {prompt_tokens}")

    # ---------------- Batch Generation Loop ----------------
    while rows_left > 0:
        iteration += 1
        batch_sample = sample_reference(reference_df, n_reference_rows)
        batch_size = min(rows_left, max(1, (max_tokens_model - prompt_tokens) // tokens_per_row))
        print(f"[Batch {iteration}] Batch size: {batch_size}, Rows left: {rows_left}")

        try:
            df_batch = generate_batch(
                system_prompt, user_prompt, batch_sample, batch_size, openai_model
            )
        except Exception as e:
            print(f"[Error] Batch {iteration} failed: {e}")
            break

        # Filter duplicates using hash
        new_rows = [
            row
            for _, row in df_batch.iterrows()
            if hash_row(row) not in existing_hashes
        ]
        for row in new_rows:
            existing_hashes.add(hash_row(row))

        final_df = pd.concat([final_df, pd.DataFrame(new_rows)], ignore_index=True)
        rows_left = total_rows - len(final_df)
        print(
            f"[Batch {iteration}] Unique new rows added: {len(new_rows)}, Total so far: {len(final_df)}"
        )

        if len(new_rows) == 0:
            print("[Warning] No new unique rows. Stopping batches.")
            break

    # ---------------- Evaluation ----------------
    report_df, vis_dict = pd.DataFrame(), {}
    if reference_df is not None and not final_df.empty:
        evaluator = SimpleEvaluator(temp_dir=temp_dir)
        evaluator.evaluate(reference_df, final_df)
        report_df = evaluator.results_as_dataframe()
        vis_dict = evaluator.create_visualizations_temp_dict(reference_df, final_df)
        print(f"[Info] Evaluation complete. Report shape: {report_df.shape}")

    # ---------------- Collect Images ----------------
    all_images: List[Image.Image] = []
    for imgs in vis_dict.values():
        if isinstance(imgs, list):
            all_images.extend([img for img in imgs if img is not None])

    # ---------------- Save CSV ----------------
    final_csv_path = os.path.join(temp_dir, "synthetic_data.csv")
    final_df.to_csv(final_csv_path, index=False)
    print(f"[Done] Generated {len(final_df)} rows → saved to {final_csv_path}")

    generated_state = {}

    return final_df, final_csv_path, report_df, generated_state, all_images
