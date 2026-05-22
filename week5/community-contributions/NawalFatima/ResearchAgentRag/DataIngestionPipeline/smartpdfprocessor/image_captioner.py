import os
import time
import json
import re
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.genai import types

logger = logging.getLogger(__name__)

IMAGE_SIZE_THRESHOLD = 75 * 1024  # 50KB — skip logos, icons, decorations
IMAGE_BATCH_SIZE     = 8          # images per Gemini call
RETRY_ATTEMPTS       = 3
FREE_TIER_DELAY      = 5          # seconds between sequential calls

GEMINI_PROMPT = """You are processing images extracted from a business document for a RAG knowledge base.

For each image provided, return a JSON array with one object per image using this exact schema:
{
  "image_index": <int>,
  "type": <"logo" | "photo" | "diagram" | "chart" | "table" | "screenshot" | "other">,
  "complexity": <"simple" | "complex">,
  "caption": <string>,
  "key_data": <string | null>
}

Rules — follow strictly:
- Logo / brand mark / watermark / icon: type = "logo", caption = "Logo: <brand name if visible>", key_data = null
- Simple images (photos, decorative, non-data visuals): one line caption only, complexity = "simple", key_data = null
- Complex images (diagrams, charts, graphs, technical drawings, data tables as images):
    - complexity = "complex"
    - caption: min 2 sentences and up to 4 sentences MAX — what the image communicates, not how it looks
    - key_data: extracted numbers, trends, axis labels, or key findings (charts/diagrams only)
- Never less than 2 sentences
- Never exceed 4 sentences for any caption under any circumstance
- Return only a valid JSON array — no markdown fences, no preamble, no explanation"""


class ImageCaptioner:
    """
    Collects images written by pymupdf4llm, batches them,
    and captions each batch via Gemini Vision.

    max_workers=1  → sequential with delay (free tier safe)
    max_workers>1  → parallel with ThreadPoolExecutor (paid tier)
    """

    def __init__(self, client, gemini_model: str, max_workers: int = 1):
        self.client = client
        self.gemini_model = gemini_model
        self.max_workers = max_workers

    def collect(self, img_dir: str) -> dict:
        """
        Reads image files written by pymupdf4llm to img_dir.
        Parses page number from filename format:
            <docname>-{page_zero_indexed}-{img_idx}.png

        Filters out images under IMAGE_SIZE_THRESHOLD (50KB).

        Returns:
            { page_num (1-indexed): [image_path_str, ...] }
        """
        images_by_page = {}
        for filename in os.listdir(img_dir):
            if not filename.endswith(".png"):
                continue
            try:
                parts = filename.replace(".png", "").split("-")
                page_num = int(parts[-2]) + 1  # zero-indexed → 1-indexed
                img_path = os.path.join(img_dir, filename)
                if os.path.getsize(img_path) > IMAGE_SIZE_THRESHOLD:
                    images_by_page.setdefault(page_num, []).append(img_path)
            except (ValueError, IndexError):
                continue
        return images_by_page

    def caption(self, images_by_page: dict) -> dict:
        """
        Captions all images grouped by page.

        Returns:
            { page_num: [caption_dict, ...] }

        caption_dict schema:
            {
                "image_index": int,
                "type": str,
                "complexity": str,
                "caption": str,
                "key_data": str | null
            }
        """
        if not images_by_page:
            return {}

        # Flatten: (page_num, image_path, global_index)
        flat_images = []
        for page_num, paths in images_by_page.items():
            for path in paths:
                flat_images.append((page_num, path, len(flat_images)))

        batches = [
            flat_images[i : i + IMAGE_BATCH_SIZE]
            for i in range(0, len(flat_images), IMAGE_BATCH_SIZE)
        ]

        all_captions = {}

        if self.max_workers == 1:
            # Sequential — safe for free tier
            for batch_num, batch in enumerate(batches):
                results = self._call_with_retry(batch, batch_num, len(batches))
                if results:
                    for result in results:
                        global_idx = batch[result["image_index"]][2]
                        all_captions[global_idx] = result
                time.sleep(FREE_TIER_DELAY)
        else:
            # Parallel — paid tier
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_batch = {
                    executor.submit(
                        self._call_with_retry, batch, batch_num, len(batches)
                    ): (batch_num, batch)
                    for batch_num, batch in enumerate(batches)
                }
                for future in as_completed(future_to_batch):
                    batch_num, batch = future_to_batch[future]
                    results = future.result()
                    if results:
                        for result in results:
                            global_idx = batch[result["image_index"]][2]
                            all_captions[global_idx] = result

        # Re-group by page
        captions_by_page = {}
        for page_num, _, global_idx in flat_images:
            caption = all_captions.get(global_idx)
            if caption:
                captions_by_page.setdefault(page_num, []).append(caption)

        return captions_by_page

    def _call_with_retry(self, batch: list, batch_num: int, total: int) -> list:
        """
        Wraps a single Gemini batch call with exponential backoff retry.
        Retries on 429 rate limit errors only.
        Other errors fail fast.
        """
        for attempt in range(RETRY_ATTEMPTS):
            try:
                logger.info(
                    f"Captioning batch {batch_num + 1}/{total} "
                    f"(attempt {attempt + 1})"
                )
                return self._describe_batch(batch)
            except Exception as e:
                if "429" in str(e):
                    wait = 30 * (attempt + 1)  # 30s → 60s → 90s
                    logger.warning(
                        f"Rate limited on batch {batch_num + 1} "
                        f"— retrying in {wait}s"
                    )
                    time.sleep(wait)
                else:
                    logger.warning(f"Batch {batch_num + 1} failed: {e}")
                    break

        logger.warning(
            f"Batch {batch_num + 1} skipped after {RETRY_ATTEMPTS} attempts"
        )
        return []

    def _describe_batch(self, batch: list) -> list:
        """
        Sends one image batch to Gemini and parses the JSON response.

        batch: list of (page_num, image_path, global_index)
        Returns: list of caption dicts
        """
        contents = [GEMINI_PROMPT]

        for local_idx, (_, img_path, _) in enumerate(batch):
            img_bytes = Path(img_path).read_bytes()
            contents.append(
                types.Part.from_bytes(data=img_bytes, mime_type="image/png")
            )
            contents.append(f"Image index: {local_idx}")

        response = self.client.models.generate_content(
            model=self.gemini_model,
            contents=contents,
        )

        raw = response.text.strip()
        # Strip markdown fences if Gemini wraps response in ```json
        raw = re.sub(
            r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE
        ).strip()
        return json.loads(raw)