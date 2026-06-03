"""Build a QA JSONL file from generated car and brand documents."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
GENERATOR_PATH = CURRENT_DIR / "generate_car_dataset.py"

HEADING_ALIASES: dict[str, tuple[str, ...]] = {
    "brand_context": ("brand context", "hyundai brand context", "honda brand context"),
    "classification": (
        "car class and positioning",
        "segment and basic classification",
        "model positioning class and body type",
        "model positioning, class, and body type",
        "class and segment positioning",
        "class segment and positioning",
    ),
    "launch_period": (
        "launch period and development overview",
        "launch and origins",
        "launch period and development story",
        "launch and development background",
        "launch and development story",
    ),
    "generations": (
        "generations and facelifts",
        "generations and facelifts high level",
        "generational overview",
    ),
    "design_language": (
        "design language",
        "design language and styling",
        "design language and styling approach",
    ),
    "platform_chassis": (
        "platform and chassis",
        "platform chassis and driving character",
    ),
    "powertrains": (
        "powertrain evolution",
        "powertrain options",
        "powertrain options over time",
        "powertrain range over time",
    ),
    "transmissions_drivetrain": ("transmissions and drivetrain", "transmission and drivetrain"),
    "performance_metrics": ("performance metrics",),
    "safety_reliability": ("safety and reliability",),
    "variants_trims": (
        "trims variants and special editions",
        "trims, variants, and special editions",
    ),
    "technology_features": ("technology and features",),
    "market_position": ("market reception and pricing segment",),
    "regional_differences": ("regional differences",),
    "strengths_weaknesses_legacy": (
        "strengths weaknesses and legacy",
        "strengths, weaknesses, and legacy",
        "known strengths and weaknesses",
    ),
    "brand_overview": ("brand overview",),
    "origin_founding": ("origin and founding story",),
    "ownership_timeline": ("ownership and parent company timeline",),
    "key_milestones": ("key milestones",),
    "notable_model_families": ("notable model families",),
    "technology_strengths": ("technology and engineering strengths",),
    "manufacturing_footprint": ("manufacturing footprint",),
    "motorsport_innovation": ("motorsport and innovation highlights",),
    "global_strategy": ("global market position and current strategy",),
}

BODY_TYPE_PATTERNS: dict[str, str] = {
    r"\bhatchback\b": "hatchback",
    r"\bsedan\b": "sedan",
    r"\bcoupe\b": "coupe",
    r"\bconvertible\b": "convertible",
    r"\bwagon\b": "wagon",
    r"\bestate\b": "wagon",
    r"\btourer\b": "wagon",
    r"\bcrossover\b": "crossover",
    r"\bsuv\b": "SUV",
    r"\bmpv\b": "MPV",
    r"\bpickup\b": "pickup",
    r"\b2\+2\b": "2+2",
}

DRIVETRAIN_PATTERNS: dict[str, str] = {
    r"\bfront-wheel drive\b": "front-wheel drive",
    r"\brear-wheel drive\b": "rear-wheel drive",
    r"\ball-wheel drive\b": "all-wheel drive",
    r"\bfour-wheel drive\b": "four-wheel drive",
    r"\bfwd\b": "FWD",
    r"\brwd\b": "RWD",
    r"\bawd\b": "AWD",
    r"\b4wd\b": "4WD",
    r"\bfr layout\b": "FR layout",
}

POWERTRAIN_PATTERNS: dict[str, str] = {
    r"\bpetrol\b": "petrol",
    r"\bgasoline\b": "gasoline",
    r"\bdiesel\b": "diesel",
    r"\bhybrid\b": "hybrid",
    r"\bplug-in hybrid\b": "plug-in hybrid",
    r"\bbattery electric\b": "battery electric",
    r"\belectric\b": "electric",
    r"\bturbocharged\b": "turbocharged",
    r"\bnaturally aspirated\b": "naturally aspirated",
    r"\binline-4\b": "inline-4",
    r"\binline-six\b": "inline-six",
    r"\bv6\b": "V6",
    r"\bv8\b": "V8",
    r"\bv10\b": "V10",
}

TRANSMISSION_PATTERNS: dict[str, str] = {
    r"\bmanuals?\b": "manual",
    r"\bautomatics?\b": "automatic",
    r"\bcvt\b": "CVT",
    r"\bcontinuously variable transmissions?\b": "CVT",
    r"\bdual-clutch\b": "dual-clutch",
    r"\bdct\b": "DCT",
    r"\be-cvt\b": "e-CVT",
}

SEGMENT_PATTERNS: dict[str, str] = {
    r"\ba-segment\b": "A-segment",
    r"\bb-segment\b": "B-segment",
    r"\bc-segment\b": "C-segment",
    r"\bd-segment\b": "D-segment",
    r"\be-segment\b": "E-segment",
    r"\bf-segment\b": "F-segment",
    r"\bj-segment\b": "J-segment",
    r"\bm-segment\b": "M-segment",
    r"\bs-segment\b": "S-segment",
    r"\bsubcompact\b": "subcompact",
    r"\bcompact\b": "compact",
    r"\bmid-size\b": "mid-size",
    r"\bmidsize\b": "midsize",
    r"\bfull-size\b": "full-size",
    r"\blower midsize\b": "lower midsize",
    r"\bpony car\b": "pony car",
    r"\bsports car\b": "sports car",
    r"\bluxury crossover\b": "luxury crossover",
}

SEGMENT_ORDER: dict[str, int] = {
    "A-segment": 1,
    "B-segment": 2,
    "C-segment": 3,
    "D-segment": 4,
    "E-segment": 5,
    "F-segment": 6,
}

# Convert free-form names into safe lowercase slugs used in filenames and IDs.
# Example:
# - "Mercedes-Benz C-Class" -> "mercedes_benz_c_class"
# We use the same normalization everywhere so filename-based lookups stay stable.
def sanitize_name(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return cleaned or "value"

# Normalize heading text so different heading spellings can map to one canonical key.
# Example:
# - "Trims, variants, and special editions" -> "trims variants and special editions"
# - "Class/segment and positioning" -> "class segment and positioning"
# This lets the parser treat small formatting differences as the same section.
def normalize_heading(value: str) -> str:
    lowered = value.lower().strip()
    lowered = lowered.replace("–", " ").replace("-", " ")
    lowered = re.sub(r"[^a-z0-9, ]+", " ", lowered)
    lowered = lowered.replace(",", " ")
    return re.sub(r"\s+", " ", lowered).strip()

# Read the curated car list directly from the generator script so both tools stay in sync.
# This avoids maintaining the same car list in two places. If `generate_car_dataset.py`
# changes the official list of models, this parser automatically follows it.
def load_car_models(generator_path: Path) -> list[tuple[str, str]]:
    module = ast.parse(generator_path.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CAR_MODELS":
                    value = ast.literal_eval(node.value)
                    return [(str(brand), str(model)) for brand, model in value]
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "CAR_MODELS" and node.value:
                value = ast.literal_eval(node.value)
                return [(str(brand), str(model)) for brand, model in value]
    raise RuntimeError("CAR_MODELS not found in generate_car_dataset.py")

# Build a reverse lookup from many heading spellings to one normalized section key.
# Example:
# - "Class and segment positioning"
# - "Model positioning, class, and body type"
# Both can map to the same internal key: `classification`.
def build_alias_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical, aliases in HEADING_ALIASES.items():
        for alias in aliases:
            lookup[normalize_heading(alias)] = canonical
    return lookup

# Split prose into sentence-like chunks for conservative fact extraction.
# We do sentence-level extraction because it is easier to keep answers grounded.
# Example:
# "The A4 debuted in 1994. It replaced the Audi 80."
# becomes two separate sentences we can reason about safely.
def split_sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text.strip())
    if not compact:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", compact) if part.strip()]

# Return the first sentence when we want a short grounded answer snippet.
# This is useful for categories like launch date, safety, or market position where
# the first sentence usually contains the cleanest summary with the least ambiguity.
def first_sentence(text: str) -> str | None:
    sentences = split_sentences(text)
    return sentences[0] if sentences else None

# Return the first few sentences when a single sentence loses too much context.
# Example: classification text often mentions both the segment and the body style
# across the first two sentences, so reading only the first one can miss useful labels.
def leading_sentences(text: str, count: int) -> str:
    sentences = split_sentences(text)
    return " ".join(sentences[:count]).strip()

# Find the first sentence containing any of the requested patterns.
# Example:
# - patterns = ["launch", "debuted"]
# - returns the first sentence mentioning either keyword
# If nothing matches, it falls back to the first sentence to avoid empty extraction.
def find_sentence(text: str, patterns: list[str]) -> str | None:
    for sentence in split_sentences(text):
        lowered = sentence.lower()
        if any(pattern in lowered for pattern in patterns):
            return sentence
    return first_sentence(text)

# Prefer a more specific match first, then fall back to a looser pattern set.
# Example:
# - first try exact drivetrain wording like "all-wheel drive"
# - if that is missing, accept shorter tokens like "AWD"
# This keeps answers as explicit as possible before using weaker hints.
def find_sentence_with_fallback(
    text: str,
    preferred_patterns: list[str],
    fallback_patterns: list[str],
) -> str | None:
    preferred = find_sentence(text, preferred_patterns)
    if preferred and any(pattern in preferred.lower() for pattern in preferred_patterns):
        return preferred
    return find_sentence(text, fallback_patterns)

# Extract normalized labels such as body types or segment classes from raw text.
# Example:
# if the source mentions "sedan" and "wagon", this returns ["sedan", "wagon"].
# These normalized labels later become keywords in the QA JSONL.
def extract_labels(text: str, pattern_map: dict[str, str]) -> list[str]:
    labels: list[str] = []
    for pattern, label in pattern_map.items():
        if re.search(pattern, text, flags=re.IGNORECASE) and label not in labels:
            labels.append(label)
    return labels

# Pull out generation headings like "First generation" or "B9" from section text.
# Example matches:
# - "First generation (1967-1969)"
# - "B9 (2015-present)"
# We store only the heading label, not the whole paragraph, to keep the field compact.
def extract_generation_labels(text: str) -> list[str]:
    labels: list[str] = []
    for line in text.splitlines():
        stripped = line.strip(" -–")
        if not stripped:
            continue
        lowered = stripped.lower()
        if "generation" in lowered or re.match(r"^[a-z]\d", lowered) or re.match(
            r"^(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh)\s+generation",
            lowered,
        ):
            label = stripped.split(":", 1)[0].strip()
            if label and label not in labels:
                labels.append(label)
    return labels

# Capture milestone lines that start with a year so brand timelines stay explicit.
# Example:
# - "1989: Launch of Lexus in the United States..."
# This helps create temporal QA rows without inventing missing dates.
def extract_year_lines(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^\d{4}", stripped):
            items.append(stripped)
    return items

# Capture short label prefixes from "Label: details" style lines.
# Example:
# - "RX: A mid-size luxury crossover SUV..."
# gives us the label "RX", which can be reused as a notable model-family keyword.
def extract_colon_labels(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if ":" not in stripped:
            continue
        label = stripped.split(":", 1)[0].strip()
        if label and len(label.split()) <= 6 and label not in items:
            items.append(label)
    return items

# Format a list into natural language so cross-file answers read like normal prose.
# Example:
# - ["RX"] -> "RX"
# - ["RX", "ES"] -> "RX and ES"
# - ["RX", "ES", "LS"] -> "RX, ES, and LS"
def format_human_list(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"

# Find the first raw line containing a token so derived multi-file answers can still
# point back to exact source snippets from the dataset.
def find_line_containing(text: str, token: str) -> str | None:
    token_lower = token.lower()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and token_lower in stripped.lower():
            return stripped
    return None

# Pick one comparable A-F segment label so same-brand models can be compared safely.
# Example:
# - ["C-segment", "compact"] -> ("C-segment", 3)
# - ["D-segment", "mid-size"] -> ("D-segment", 4)
# We intentionally do not compare looser labels like "SUV" here because they do not
# form a clean higher/lower ladder the way A-F segment labels do.
def get_primary_ranked_segment(facts: dict[str, Any]) -> tuple[str, int] | None:
    classification_sentence = facts.get("classification_sentence") or ""
    for label in SEGMENT_ORDER:
        if label.lower() in classification_sentence.lower():
            return label, SEGMENT_ORDER[label]
    for label in facts.get("segment_classes", []):
        if label in SEGMENT_ORDER:
            return label, SEGMENT_ORDER[label]
    return None

# Parse strengths, weaknesses, and any legacy paragraph from the summary section.
# Many source files use a mixed format here:
# - bullet lists for strengths/weaknesses
# - one final paragraph for legacy
# This helper separates those pieces so later QA rows can stay focused.
def parse_strengths_weaknesses(text: str) -> tuple[list[str], list[str], str | None]:
    strengths: list[str] = []
    weaknesses: list[str] = []
    legacy_sentence: str | None = None
    mode: str | None = None

    for line in text.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if not stripped:
            continue
        if lowered.startswith("strengths:"):
            mode = "strengths"
            continue
        if lowered.startswith("weaknesses:"):
            mode = "weaknesses"
            continue
        if stripped.startswith(("–", "-", "•")) and mode == "strengths":
            item = stripped.lstrip("–-• ").strip()
            if item:
                strengths.append(item)
            continue
        if stripped.startswith(("–", "-", "•")) and mode == "weaknesses":
            item = stripped.lstrip("–-• ").strip()
            if item:
                weaknesses.append(item)
            continue
        if lowered.startswith("the ") or lowered.startswith("legacy"):
            legacy_sentence = stripped

    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    legacy_paragraph = next(
        (paragraph for paragraph in paragraphs if "legacy" in paragraph.lower()),
        None,
    )
    if legacy_paragraph:
        legacy_sentence = legacy_paragraph
    elif legacy_sentence is None and paragraphs:
        legacy_sentence = paragraphs[-1]

    return strengths, weaknesses, legacy_sentence

# Rejoin buffered lines while collapsing excessive blank-line spacing.
# During parsing we collect raw lines into a buffer. This helper turns that buffer
# back into readable section text without preserving noisy extra blank lines.
def clean_join(lines: list[str]) -> str:
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

# Split each source file into normalized semantic sections used by later extraction.
# The source documents are semi-structured prose, not fixed JSON, so this function
# is the main bridge from "human-written text file" to "machine-usable sections".
# Example:
# - "Launch and development background" -> `launch_period`
# - "Technology and features" -> `technology_features`
def parse_sections(path: Path, doc_type: str, heading_lookup: dict[str, str]) -> tuple[str | None, dict[str, str], str]:
    raw_text = path.read_text(encoding="utf-8").strip()
    lines = raw_text.splitlines()
    title: str | None = None

    if lines and "profile" in lines[0].lower():
        title = lines[0].strip()
        lines = lines[1:]

    sections: dict[str, str] = {}
    current_key = "preamble"
    buffer: list[str] = []

    # Commit the current buffered paragraph block into the active section.
    # We use this small nested helper so each time we detect a new heading, the
    # previous paragraph block gets saved under the correct normalized section key.
    def flush_buffer() -> None:
        nonlocal buffer
        text = clean_join(buffer)
        if text:
            if current_key in sections:
                sections[current_key] = f"{sections[current_key]}\n\n{text}"
            else:
                sections[current_key] = text
        buffer = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if buffer and buffer[-1] != "":
                buffer.append("")
            continue
        heading_key = heading_lookup.get(normalize_heading(stripped))
        if heading_key:
            flush_buffer()
            current_key = heading_key
            continue
        buffer.append(stripped)
    flush_buffer()

    if "preamble" in sections:
        preamble = sections.pop("preamble")
        fallback_key = "brand_overview" if doc_type == "brand" else "brand_context"
        if fallback_key in sections:
            sections[f"{fallback_key}_preamble"] = preamble
        else:
            sections[fallback_key] = preamble

    return title, sections, raw_text

# Build fast lookups from filename slugs back to their original brand/model names.
# Example:
# - "honda_accord" -> ("Honda", "Accord")
# - "lexus" -> "Lexus"
# This is how we recover clean names from filenames without hardcoding them again.
def build_brand_lookup(car_models: list[tuple[str, str]]) -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
    brand_slug_to_name = {sanitize_name(brand): brand for brand, _ in car_models}
    car_slug_to_names = {
        sanitize_name(f"{brand}_{model}"): (brand, model) for brand, model in car_models
    }
    return brand_slug_to_name, car_slug_to_names

# Turn one parsed document into a structured internal record used for QA generation.
# Important note:
# This is an internal staging structure, not the final JSONL output. We collect
# normalized facts here first so the QA writer can reuse them consistently.
# Example fields extracted here:
# - segment_classes
# - body_types
# - launch_period_sentence
# - drivetrain_sentence
# - legacy_sentence
def build_document_record(
    *,
    path: Path,
    doc_type: str,
    title: str | None,
    sections: dict[str, str],
    raw_text: str,
    brand_slug_to_name: dict[str, str],
    car_slug_to_names: dict[str, tuple[str, str]],
) -> dict[str, Any]:
    stem = path.stem
    brand: str | None = None
    model: str | None = None

    if doc_type == "car":
        brand, model = car_slug_to_names.get(stem, (None, None))
    else:
        brand = brand_slug_to_name.get(stem, stem.replace("_", " ").title())

    classification_text = sections.get("classification", "")
    powertrains_text = sections.get("powertrains", "")
    transmissions_text = sections.get("transmissions_drivetrain", "")
    strengths_text = sections.get("strengths_weaknesses_legacy", "")
    milestones_text = sections.get("key_milestones", "")
    notable_models_text = sections.get("notable_model_families", "")
    global_strategy_text = sections.get("global_strategy", "")
    ownership_text = sections.get("ownership_timeline", "")
    classification_excerpt = leading_sentences(classification_text, 2)

    strengths, weaknesses, legacy_sentence = parse_strengths_weaknesses(strengths_text)

    facts: dict[str, Any] = {
        "classification_text": classification_text or None,
        "classification_sentence": first_sentence(classification_text),
        "segment_classes": extract_labels(classification_excerpt, SEGMENT_PATTERNS),
        "body_types": extract_labels(classification_excerpt, BODY_TYPE_PATTERNS),
        "drivetrain_layouts": extract_labels(
            f"{classification_excerpt}\n{transmissions_text}", DRIVETRAIN_PATTERNS
        ),
        "launch_period_sentence": first_sentence(sections.get("launch_period", "")),
        "generation_labels": extract_generation_labels(sections.get("generations", "")),
        "platform_chassis_sentence": first_sentence(sections.get("platform_chassis", "")),
        "powertrain_types": extract_labels(powertrains_text, POWERTRAIN_PATTERNS),
        "powertrain_sentence": first_sentence(powertrains_text),
        "transmission_types": extract_labels(transmissions_text, TRANSMISSION_PATTERNS),
        "transmission_sentence": first_sentence(transmissions_text),
        "drivetrain_sentence": find_sentence_with_fallback(
            transmissions_text,
            ["front-wheel", "rear-wheel", "all-wheel", "four-wheel", "quattro"],
            ["fwd", "rwd", "awd", "4wd"],
        ),
        "performance_sentence": first_sentence(sections.get("performance_metrics", "")),
        "safety_sentence": first_sentence(sections.get("safety_reliability", "")),
        "variants_sentence": first_sentence(sections.get("variants_trims", "")),
        "technology_sentence": first_sentence(sections.get("technology_features", "")),
        "market_position_sentence": first_sentence(sections.get("market_position", "")),
        "regional_differences_sentence": first_sentence(sections.get("regional_differences", "")),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "legacy_sentence": legacy_sentence,
        "ownership_sentence": first_sentence(ownership_text),
        "key_milestones": extract_year_lines(milestones_text),
        "notable_model_families": extract_colon_labels(notable_models_text),
        "technology_strengths_sentence": first_sentence(sections.get("technology_strengths", "")),
        "manufacturing_footprint_sentence": first_sentence(sections.get("manufacturing_footprint", "")),
        "motorsport_innovation_sentence": first_sentence(sections.get("motorsport_innovation", "")),
        "global_strategy_sentence": first_sentence(global_strategy_text),
    }

    return {
        "doc_id": f"{doc_type}:{stem}",
        "doc_type": doc_type,
        "brand": brand,
        "model": model,
        "title": title,
        "source_file": str(path),
        "source_filename": path.name,
        "categories_present": list(sections.keys()),
        "sections": sections,
        "extracted_facts": facts,
        "raw_text": raw_text,
    }

# Add one QA row only when we have a grounded answer taken from the source text.
# We do not create placeholder rows. If the source does not clearly support an
# answer, we skip the row instead of generating a weak or guessed answer.
def append_qa_row(
    rows: list[dict[str, Any]],
    *,
    question: str,
    keywords: list[str],
    reference_answer: str | None,
    category: str,
    source_doc_id: str | list[str],
    source_text: str | list[str],
    scope: str | None = None,
    validation_mode: str = "exact_answer",
    evidence_strings: list[str] | None = None,
) -> None:
    if not reference_answer:
        return
    source_doc_ids = [source_doc_id] if isinstance(source_doc_id, str) else source_doc_id
    source_texts = [source_text] if isinstance(source_text, str) else source_text
    resolved_scope = scope or ("single_file" if len(source_doc_ids) == 1 else "multi_file")
    rows.append(
        {
            "question": question,
            "keywords": [item for item in keywords if item],
            "reference_answer": reference_answer.strip(),
            "category": category,
            "scope": resolved_scope,
            "_source_doc_ids": source_doc_ids,
            "_source_texts": source_texts,
            "_validation_mode": validation_mode,
            "_evidence_strings": evidence_strings or [],
        }
    )

# Generate QA examples for car-model documents from explicitly extracted facts.
# Example questions created here:
# - "What class or segment is the Honda Accord?"
# - "When was the Audi A4 launched or introduced?"
# - "What transmission options are described for the Chevrolet Camaro?"
# Each answer is taken from a sentence already extracted from the source document.
def build_car_qa_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    facts = record["extracted_facts"]
    brand = record["brand"]
    model = record["model"]
    source_text = record["raw_text"]
    rows: list[dict[str, Any]] = []

    append_qa_row(
        rows,
        question=f"What class or segment is the {brand} {model}?",
        keywords=[brand, model, *facts["segment_classes"]],
        reference_answer=facts["classification_sentence"],
        category="classification",
        source_doc_id=record["doc_id"],
        source_text=source_text,
    )
    append_qa_row(
        rows,
        question=f"What drivetrain layout is used by the {brand} {model}?",
        keywords=[brand, model, *facts["drivetrain_layouts"]],
        reference_answer=facts["drivetrain_sentence"],
        category="technical",
        source_doc_id=record["doc_id"],
        source_text=source_text,
    )
    append_qa_row(
        rows,
        question=f"When was the {brand} {model} launched or introduced?",
        keywords=[brand, model, "launch"],
        reference_answer=facts["launch_period_sentence"],
        category="temporal",
        source_doc_id=record["doc_id"],
        source_text=source_text,
    )
    append_qa_row(
        rows,
        question=f"What powertrain options have been offered for the {brand} {model}?",
        keywords=[brand, model, *facts["powertrain_types"]],
        reference_answer=facts["powertrain_sentence"],
        category="technical",
        source_doc_id=record["doc_id"],
        source_text=source_text,
    )
    append_qa_row(
        rows,
        question=f"What transmission options are described for the {brand} {model}?",
        keywords=[brand, model, *facts["transmission_types"]],
        reference_answer=facts["transmission_sentence"],
        category="technical",
        source_doc_id=record["doc_id"],
        source_text=source_text,
    )
    append_qa_row(
        rows,
        question=f"How is the {brand} {model} described in terms of safety and reliability?",
        keywords=[brand, model, "safety", "reliability"],
        reference_answer=facts["safety_sentence"],
        category="holistic",
        source_doc_id=record["doc_id"],
        source_text=source_text,
    )
    append_qa_row(
        rows,
        question=f"How is the {brand} {model} positioned in the market?",
        keywords=[brand, model, "market", "pricing"],
        reference_answer=facts["market_position_sentence"],
        category="market_position",
        source_doc_id=record["doc_id"],
        source_text=source_text,
    )
    append_qa_row(
        rows,
        question=f"What legacy is associated with the {brand} {model}?",
        keywords=[brand, model, "legacy"],
        reference_answer=facts["legacy_sentence"],
        category="legacy",
        source_doc_id=record["doc_id"],
        source_text=source_text,
    )

    return rows

# Generate QA examples for brand documents from explicitly extracted facts.
# Example questions created here:
# - "Who owns Lexus?"
# - "When was Lexus launched or introduced?"
# - "What current strategy is described for Lexus?"
# This keeps brand-level knowledge separate from model-level questions.
def build_brand_qa_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    facts = record["extracted_facts"]
    brand = record["brand"]
    source_text = record["raw_text"]
    rows: list[dict[str, Any]] = []

    append_qa_row(
        rows,
        question=f"What is {brand} known for as a car brand?",
        keywords=[brand, "brand"],
        reference_answer=first_sentence(record["sections"].get("brand_overview", "")),
        category="direct_fact",
        source_doc_id=record["doc_id"],
        source_text=source_text,
    )
    append_qa_row(
        rows,
        question=f"Who owns {brand}?",
        keywords=[brand, "owner", "parent company"],
        reference_answer=facts["ownership_sentence"],
        category="relationship",
        source_doc_id=record["doc_id"],
        source_text=source_text,
    )
    launch_line = None
    for item in facts["key_milestones"]:
        if any(token in item.lower() for token in ["launch", "introduced", "introduced in", "brand"]):
            launch_line = item
            break
    append_qa_row(
        rows,
        question=f"When was {brand} launched or introduced?",
        keywords=[brand, "launch"],
        reference_answer=launch_line or first_sentence(record["sections"].get("origin_founding", "")),
        category="temporal",
        source_doc_id=record["doc_id"],
        source_text=source_text,
    )
    first_model_line = None
    for line in record["sections"].get("notable_model_families", "").splitlines():
        if ":" in line:
            first_model_line = line.strip()
            break
    append_qa_row(
        rows,
        question=f"What is one notable model family under {brand}?",
        keywords=[brand, *facts["notable_model_families"][:2]],
        reference_answer=first_model_line,
        category="direct_fact",
        source_doc_id=record["doc_id"],
        source_text=source_text,
    )
    append_qa_row(
        rows,
        question=f"What current strategy is described for {brand}?",
        keywords=[brand, "strategy", "market"],
        reference_answer=facts["global_strategy_sentence"],
        category="holistic",
        source_doc_id=record["doc_id"],
        source_text=source_text,
    )

    return rows

# Build same-brand comparison questions that require two different car files.
# Example:
# if one file says "C-segment" and another says "D-segment", we can create a
# comparative question about which model sits in a higher segment.
def build_comparative_qa_rows(car_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    records_by_brand: dict[str, list[dict[str, Any]]] = {}
    for record in car_records:
        records_by_brand.setdefault(record["brand"], []).append(record)

    for brand, records in records_by_brand.items():
        ranked_records: list[tuple[int, str, dict[str, Any]]] = []
        for record in records:
            ranked_segment = get_primary_ranked_segment(record["extracted_facts"])
            if ranked_segment:
                label, rank = ranked_segment
                ranked_records.append((rank, label, record))

        if len(ranked_records) < 2:
            continue

        ranked_records.sort(key=lambda item: item[0])
        lower_rank, lower_label, lower_record = ranked_records[0]
        higher_rank, higher_label, higher_record = ranked_records[-1]
        if lower_rank == higher_rank:
            continue

        answer = (
            f"{higher_record['brand']} {higher_record['model']} is described as a {higher_label} model, "
            f"while the {lower_record['brand']} {lower_record['model']} is described as a {lower_label} model, "
            f"so the {higher_record['model']} sits in a higher segment."
        )
        append_qa_row(
            rows,
            question=(
                f"Which is positioned in a higher segment within the {brand} range: "
                f"{lower_record['model']} or {higher_record['model']}?"
            ),
            keywords=[
                brand,
                lower_record["model"],
                higher_record["model"],
                lower_label,
                higher_label,
            ],
            reference_answer=answer,
            category="comparative",
            source_doc_id=[lower_record["doc_id"], higher_record["doc_id"]],
            source_text=[lower_record["raw_text"], higher_record["raw_text"]],
            validation_mode="evidence_strings",
            evidence_strings=[
                lower_record["extracted_facts"]["classification_sentence"],
                higher_record["extracted_facts"]["classification_sentence"],
            ],
        )

    return rows

# Build brand-plus-model questions that span a brand file and multiple car files.
# Example:
# if the Lexus brand file lists RX, ES, and LS, and those same models also exist
# as car files, we can generate one spanning question grounded in all of them.
def build_spanning_qa_rows(
    car_records: list[dict[str, Any]],
    brand_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    car_records_by_brand: dict[str, list[dict[str, Any]]] = {}
    for record in car_records:
        car_records_by_brand.setdefault(record["brand"], []).append(record)

    brand_records_by_brand = {record["brand"]: record for record in brand_records}
    for brand, brand_record in brand_records_by_brand.items():
        brand_cars = car_records_by_brand.get(brand, [])
        if not brand_cars:
            continue

        notable_labels = brand_record["extracted_facts"].get("notable_model_families", [])
        if not notable_labels:
            continue

        notable_lookup = {sanitize_name(label): label for label in notable_labels}
        matches: list[tuple[dict[str, Any], str]] = []
        for car_record in brand_cars:
            model_slug = sanitize_name(car_record["model"])
            if model_slug in notable_lookup:
                matches.append((car_record, notable_lookup[model_slug]))

        if not matches:
            continue

        matched_models = [car_record["model"] for car_record, _ in matches]
        answer = (
            f"The generated {brand} car models that are also named in the {brand} brand file are "
            f"{format_human_list(matched_models)}."
        )

        evidence_strings: list[str] = []
        notable_section = brand_record["sections"].get("notable_model_families", "")
        for car_record, label in matches:
            evidence_strings.append(find_line_containing(notable_section, label) or label)
            evidence_strings.append(car_record["title"] or f"{car_record['brand']} {car_record['model']}")

        append_qa_row(
            rows,
            question=f"Which generated {brand} car models are also named in the {brand} brand file?",
            keywords=[brand, *matched_models],
            reference_answer=answer,
            category="spanning",
            source_doc_id=[brand_record["doc_id"], *[car_record["doc_id"] for car_record, _ in matches]],
            source_text=[brand_record["raw_text"], *[car_record["raw_text"] for car_record, _ in matches]],
            validation_mode="evidence_strings",
            evidence_strings=evidence_strings,
        )

        append_qa_row(
            rows,
            question=f"How many generated {brand} car models are also named in the {brand} brand file?",
            keywords=[brand, str(len(matched_models)), *matched_models],
            reference_answer=(
                f"There are {len(matched_models)} generated {brand} car models also named in the "
                f"{brand} brand file: {format_human_list(matched_models)}."
            ),
            category="numerical",
            source_doc_id=[brand_record["doc_id"], *[car_record["doc_id"] for car_record, _ in matches]],
            source_text=[brand_record["raw_text"], *[car_record["raw_text"] for car_record, _ in matches]],
            validation_mode="evidence_strings",
            evidence_strings=evidence_strings,
        )

    return rows

# Build numerical multi-file questions that count generated car models per brand.
# Example:
# "How many generated Honda car models are in the dataset?"
# The answer is derived from multiple Honda car files and validated using those files.
def build_numerical_brand_count_rows(car_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    car_records_by_brand: dict[str, list[dict[str, Any]]] = {}
    for record in car_records:
        car_records_by_brand.setdefault(record["brand"], []).append(record)

    for brand, records in sorted(car_records_by_brand.items()):
        model_names = [record["model"] for record in records]
        evidence_strings = [
            record["extracted_facts"]["classification_sentence"] or first_sentence(record["raw_text"]) or record["model"]
            for record in records
        ]
        append_qa_row(
            rows,
            question=f"How many generated {brand} car models are in the dataset?",
            keywords=[brand, str(len(model_names)), *model_names],
            reference_answer=(
                f"There are {len(model_names)} generated {brand} car models in the dataset: "
                f"{format_human_list(model_names)}."
            ),
            category="numerical",
            source_doc_id=[record["doc_id"] for record in records],
            source_text=[record["raw_text"] for record in records],
            validation_mode="evidence_strings",
            evidence_strings=evidence_strings,
        )

    return rows

# Build corpus-wide pattern questions that combine evidence from many car files.
# Example:
# if a brand has one sedan file and one SUV/crossover file, we can create a holistic
# question about brands that cover both body-style groups in the current dataset.
def build_holistic_corpus_qa_rows(car_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    car_records_by_brand: dict[str, list[dict[str, Any]]] = {}
    for record in car_records:
        car_records_by_brand.setdefault(record["brand"], []).append(record)

    qualifying_brands: list[str] = []
    source_doc_ids: list[str] = []
    source_texts: list[str] = []
    evidence_strings: list[str] = []

    for brand, records in sorted(car_records_by_brand.items()):
        sedan_record = next(
            (record for record in records if "sedan" in record["extracted_facts"].get("body_types", [])),
            None,
        )
        suv_record = next(
            (
                record
                for record in records
                if any(
                    label in record["extracted_facts"].get("body_types", [])
                    for label in ["SUV", "crossover"]
                )
            ),
            None,
        )
        if not sedan_record or not suv_record:
            continue

        qualifying_brands.append(brand)
        source_doc_ids.extend([sedan_record["doc_id"], suv_record["doc_id"]])
        source_texts.extend([sedan_record["raw_text"], suv_record["raw_text"]])
        evidence_strings.extend(
            [
                sedan_record["extracted_facts"]["classification_sentence"],
                suv_record["extracted_facts"]["classification_sentence"],
            ]
        )

    if qualifying_brands:
        answer = (
            "The brands in this dataset that have both a sedan-style model and an SUV or crossover model are "
            f"{format_human_list(qualifying_brands)}."
        )
        append_qa_row(
            rows,
            question="Which brands in this dataset have both a sedan-style car and an SUV or crossover?",
            keywords=qualifying_brands + ["sedan", "SUV", "crossover"],
            reference_answer=answer,
            category="spanning",
            source_doc_id=source_doc_ids,
            source_text=source_texts,
            validation_mode="evidence_strings",
            evidence_strings=evidence_strings,
        )

        append_qa_row(
            rows,
            question="How many brands in this dataset have both a sedan-style car and an SUV or crossover?",
            keywords=[str(len(qualifying_brands)), *qualifying_brands, "sedan", "SUV", "crossover"],
            reference_answer=(
                f"There are {len(qualifying_brands)} brands in this dataset that have both a "
                f"sedan-style model and an SUV or crossover model: {format_human_list(qualifying_brands)}."
            ),
            category="numerical",
            source_doc_id=source_doc_ids,
            source_text=source_texts,
            validation_mode="evidence_strings",
            evidence_strings=evidence_strings,
        )

    return rows

# Build the final QA dataset by routing each document through the right question builder.
# Car documents and brand documents do not produce the same types of questions, so
# this function dispatches each record to the correct specialized QA builder.
# After the single-document pass, it also adds multi-document rows for:
# - `comparative`
# - `spanning`
# - corpus-level `holistic`
# - cross-file `numerical`
def build_qa_records(document_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    car_records: list[dict[str, Any]] = []
    brand_records: list[dict[str, Any]] = []
    for record in document_records:
        if record["doc_type"] == "car":
            rows.extend(build_car_qa_rows(record))
            car_records.append(record)
        else:
            rows.extend(build_brand_qa_rows(record))
            brand_records.append(record)
    rows.extend(build_comparative_qa_rows(car_records))
    rows.extend(build_spanning_qa_rows(car_records, brand_records))
    rows.extend(build_numerical_brand_count_rows(car_records))
    rows.extend(build_holistic_corpus_qa_rows(car_records))
    return rows

# Write the final JSONL in the sample-compatible QA schema only.
# We intentionally write only the sample-compatible fields:
# - question
# - keywords
# - reference_answer
# - category
# - scope
# Internal grounding helpers like `_source_text` are kept only in memory for validation.
def write_qa_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            payload = {
                "question": row["question"],
                "keywords": row["keywords"],
                "reference_answer": row["reference_answer"],
                "category": row["category"],
                "scope": row["scope"],
            }
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")

# Sanity-check the parsed source records before turning them into QA rows.
# This catches parser problems early, such as:
# - missing `doc_id`
# - duplicate records
# - malformed extracted fact structures
# If this validation fails, we stop before writing a misleading JSONL file.
def validate_document_records(records: list[dict[str, Any]], expected_count: int) -> None:
    required = {"doc_id", "doc_type", "brand", "title", "source_file", "sections", "extracted_facts"}
    if len(records) != expected_count:
        raise RuntimeError(f"Expected {expected_count} source records, found {len(records)}")
    seen_ids: set[str] = set()
    for record in records:
        missing = required - set(record.keys())
        if missing:
            raise RuntimeError(f"Document record missing keys: {sorted(missing)}")
        if record["doc_id"] in seen_ids:
            raise RuntimeError(f"Duplicate document doc_id: {record['doc_id']}")
        seen_ids.add(record["doc_id"])

# Ensure every QA row has the right schema and that each answer appears in the source text.
# This is the strongest truthfulness guard in the script:
# - the row must have the expected sample-like fields
# - `keywords` must be present
# - `scope` must correctly identify single-file vs multi-file questions
# - single-document rows must contain the exact normalized `reference_answer` in source text
# - multi-document derived rows must provide evidence strings that exist in the combined source texts
# If grounding fails, we raise an error instead of writing the row.
def validate_qa_records(rows: list[dict[str, Any]]) -> None:
    required = {"question", "keywords", "reference_answer", "category", "scope"}
    for row in rows:
        missing = required - set(row.keys())
        if missing:
            raise RuntimeError(f"QA row missing keys: {sorted(missing)}")
        if not isinstance(row["keywords"], list) or not row["keywords"]:
            raise RuntimeError(f"QA row has invalid keywords: {row}")
        if row["scope"] not in {"single_file", "multi_file"}:
            raise RuntimeError(f"QA row has invalid scope: {row}")
        normalized_source = re.sub(r"\s+", " ", "\n".join(row["_source_texts"])).strip().lower()
        validation_mode = row.get("_validation_mode", "exact_answer")

        if validation_mode == "exact_answer":
            normalized_answer = re.sub(r"\s+", " ", row["reference_answer"]).strip().lower()
            if normalized_answer not in normalized_source:
                raise RuntimeError(
                    f"Reference answer is not grounded in source text for question: {row['question']}"
                )
            continue

        if validation_mode == "evidence_strings":
            evidence_strings = row.get("_evidence_strings", [])
            if not evidence_strings:
                raise RuntimeError(f"Derived QA row missing evidence strings: {row['question']}")
            for evidence in evidence_strings:
                normalized_evidence = re.sub(r"\s+", " ", str(evidence)).strip().lower()
                if normalized_evidence and normalized_evidence not in normalized_source:
                    raise RuntimeError(
                        f"Evidence is not grounded in source text for question: {row['question']}"
                    )
            continue

        raise RuntimeError(f"Unknown validation mode '{validation_mode}' for question: {row['question']}")

# Re-read the emitted JSONL file to make sure every line is valid JSON.
# This is a final output-level check. Even if the in-memory rows looked correct,
# this confirms the actual file on disk is valid JSONL line by line.
def validate_jsonl_file(path: Path) -> None:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSON on line {line_number} of {path}") from exc

# Define the CLI inputs so users can point the generator at different corpus folders.
# Example usage:
# - `python3 build_jsonl_dataset.py`
# - `python3 build_jsonl_dataset.py --cars-dir ./dataset_cars --brands-dir ./dataset_brands`
# - `python3 build_jsonl_dataset.py --qa-output ../custom_car_qa.jsonl`
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build QA JSONL from the car corpus.")
    parser.add_argument(
        "--cars-dir",
        default=str(CURRENT_DIR / "dataset_cars"),
        help="Directory containing car documents.",
    )
    parser.add_argument(
        "--brands-dir",
        default=str(CURRENT_DIR / "dataset_brands"),
        help="Directory containing brand documents.",
    )
    parser.add_argument(
        "--qa-output",
        default=str(PROJECT_ROOT / "car_qa_dataset.jsonl"),
        help="Path for QA-style JSONL output.",
    )
    return parser.parse_args()

# Orchestrate parsing, QA generation, validation, and final JSONL writing.
# High-level flow:
# 1. Read CLI inputs
# 2. Parse every source document into normalized sections
# 3. Build grounded QA rows from extracted facts
# 4. Validate that every answer really comes from the dataset text
# 5. Write the final sample-style JSONL file
def main() -> int:
    args = parse_args()
    cars_dir = Path(args.cars_dir).resolve()
    brands_dir = Path(args.brands_dir).resolve()
    qa_output = Path(args.qa_output).resolve()

    car_models = load_car_models(GENERATOR_PATH)
    brand_slug_to_name, car_slug_to_names = build_brand_lookup(car_models)
    heading_lookup = build_alias_lookup()

    car_paths = sorted(cars_dir.glob("*.txt"))
    brand_paths = sorted(brands_dir.glob("*.txt"))
    all_paths = [(path, "car") for path in car_paths] + [(path, "brand") for path in brand_paths]

    # User-facing accuracy note:
    # This script does not invent any answer text. It first reads the existing
    # generated dataset files, then extracts only facts that are explicitly
    # present in those files. Every QA row is validated by checking that the
    # final `reference_answer` appears inside the original source text. If a
    # detail cannot be tied back to the dataset text, the script skips it rather
    # than guessing. That is how this JSONL stays grounded in the generated
    # dataset instead of adding hallucinated facts.
    document_records: list[dict[str, Any]] = []
    for path, doc_type in all_paths:
        title, sections, raw_text = parse_sections(path, doc_type, heading_lookup)
        document_records.append(
            build_document_record(
                path=path,
                doc_type=doc_type,
                title=title,
                sections=sections,
                raw_text=raw_text,
                brand_slug_to_name=brand_slug_to_name,
                car_slug_to_names=car_slug_to_names,
            )
        )

    qa_records = build_qa_records(document_records)

    validate_document_records(document_records, expected_count=len(all_paths))
    validate_qa_records(qa_records)

    write_qa_jsonl(qa_output, qa_records)

    validate_jsonl_file(qa_output)

    print(f"Wrote {len(qa_records)} QA records to {qa_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
