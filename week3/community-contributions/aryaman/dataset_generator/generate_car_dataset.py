"""Generate car-model dataset files using an LLM."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import sys
import time
from pathlib import Path
import os

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ollama_client import LLMError, load_client  # noqa: E402


CAR_MODELS: list[tuple[str, str]] = [
    ("Toyota", "Corolla"),
    ("Toyota", "Camry"),
    ("Toyota", "Land Cruiser"),
    ("Honda", "Civic"),
    ("Honda", "Accord"),
    ("Honda", "CR-V"),
    ("Ford", "Mustang"),
    ("Ford", "F-150"),
    ("Ford", "Focus"),
    ("Chevrolet", "Corvette"),
    ("Chevrolet", "Camaro"),
    ("Chevrolet", "Silverado"),
    ("Nissan", "GT-R"),
    ("Nissan", "Altima"),
    ("Nissan", "Patrol"),
    ("Hyundai", "Elantra"),
    ("Hyundai", "Sonata"),
    ("Hyundai", "Tucson"),
    ("Kia", "Sportage"),
    ("Kia", "Stinger"),
    ("Kia", "Sorento"),
    ("BMW", "3 Series"),
    ("BMW", "5 Series"),
    ("BMW", "X5"),
    ("Mercedes-Benz", "C-Class"),
    ("Mercedes-Benz", "E-Class"),
    ("Mercedes-Benz", "G-Class"),
    ("Audi", "A4"),
    ("Audi", "A6"),
    ("Audi", "Q7"),
    ("Volkswagen", "Golf"),
    ("Volkswagen", "Passat"),
    ("Volkswagen", "Tiguan"),
    ("Lexus", "RX"),
    ("Lexus", "ES"),
    ("Lexus", "LS"),
    ("Mazda", "MX-5 Miata"),
    ("Mazda", "CX-5"),
    ("Mazda", "Mazda3"),
    ("Subaru", "Impreza"),
    ("Subaru", "Outback"),
    ("Subaru", "Forester"),
    ("Volvo", "XC90"),
    ("Volvo", "S90"),
    ("Volvo", "XC60"),
    ("Porsche", "911"),
    ("Porsche", "Cayenne"),
    ("Porsche", "Taycan"),
    ("Ferrari", "488 GTB"),
    ("Ferrari", "F8 Tributo"),
    ("Ferrari", "Roma"),
    ("Lamborghini", "Huracan"),
    ("Lamborghini", "Aventador"),
    ("Lamborghini", "Urus"),
    ("Maserati", "Ghibli"),
    ("Maserati", "Levante"),
    ("Maserati", "MC20"),
    ("Alfa Romeo", "Giulia"),
    ("Alfa Romeo", "Stelvio"),
    ("Alfa Romeo", "4C"),
    ("Jaguar", "F-Type"),
    ("Jaguar", "XF"),
    ("Jaguar", "I-PACE"),
    ("Land Rover", "Defender"),
    ("Land Rover", "Range Rover"),
    ("Land Rover", "Discovery"),
    ("Bentley", "Continental GT"),
    ("Bentley", "Bentayga"),
    ("Bentley", "Flying Spur"),
    ("Rolls-Royce", "Phantom"),
    ("Rolls-Royce", "Ghost"),
    ("Rolls-Royce", "Cullinan"),
    ("Aston Martin", "DB11"),
    ("Aston Martin", "Vantage"),
    ("Aston Martin", "DBX"),
    ("McLaren", "720S"),
    ("McLaren", "Artura"),
    ("McLaren", "P1"),
    ("Tesla", "Model S"),
    ("Tesla", "Model 3"),
    ("Tesla", "Model X"),
    ("Rivian", "R1T"),
    ("Rivian", "R1S"),
    ("Lucid", "Air"),
    ("Polestar", "Polestar 2"),
    ("BYD", "Han"),
    ("BYD", "Seal"),
    ("NIO", "ET7"),
    ("Xpeng", "P7"),
    ("Li Auto", "L9"),
    ("Tata Motors", "Nexon"),
    ("Mahindra", "Scorpio"),
    ("Maruti Suzuki", "Swift"),
    ("Suzuki", "Jimny"),
    ("Mitsubishi", "Pajero"),
    ("Isuzu", "D-Max"),
    ("Renault", "Clio"),
    ("Peugeot", "308"),
    ("Skoda", "Octavia"),
    ("Fiat", "500"),
]

SYSTEM_PROMPT = (
    "You are an automotive research writer. Return plain text only. "
    "Do not use markdown tables or bullet symbols."
)


def sanitize_name(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return cleaned or "car"


def build_car_prompt(brand: str, model: str) -> str:
    return (
        f"Write a detailed plain-text profile for the car model '{model}' from the brand '{brand}'. "
        "Focus primarily on car-model details and avoid repeating full brand history. "
        "Include a short brand context section (5-10% of total length), then concentrate on: "
        "car class/segment classification (explicitly identify class labels such as A, B, C, D, E, F, S, M, J "
        "when applicable, and also state body-type categories like hatchback, sedan, SUV/crossover, coupe, "
        "wagon, MPV, pickup where relevant), "
        "launch period, development story, generations/facelifts, design language, platform/chassis, "
        "powertrain options over time, transmission/drivetrain, performance metrics, safety and reliability, "
        "major trims and variants, special editions, technology/features, market reception, pricing segment, "
        "regional differences, known strengths/weaknesses, and legacy. "
        "Target 700 to 1000 words and keep a factual tone."
    )


def build_brand_prompt(brand: str) -> str:
    return (
        f"Write a detailed plain-text profile for the car brand '{brand}'. "
        "Include origin, founding story, ownership/parent company timeline, key milestones, "
        "notable model families, technology and engineering strengths, manufacturing footprint, "
        "motorsport or innovation highlights, global market position, and current strategy. "
        "Target 500 to 800 words and keep it factual."
    )


def get_text_response(client: object, model_name: str, request_user: str, prompt: str) -> str:
    response = client.responses.create(
        model=model_name,
        user=str(request_user),
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
            {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
        ],
        timeout=180,
    )
    output_text = getattr(response, "output_text", "") or ""
    if output_text.strip():
        return output_text.strip()
    if hasattr(response, "output") and response.output:
        chunks: list[str] = []
        for item in response.output:
            content_list = getattr(item, "content", None) or []
            for part in content_list:
                text_value = getattr(part, "text", None)
                if text_value:
                    chunks.append(str(text_value))
        combined = "\n".join(chunks).strip()
        if combined:
            return combined
    raise LLMError("Model returned an empty response.")


def write_with_retries(
    *,
    client: object,
    model_name: str,
    request_user: str,
    prompt: str,
    target_file: Path,
    overwrite: bool,
    max_retries: int,
    delay_seconds: float,
    progress_prefix: str,
) -> None:
    if target_file.exists() and not overwrite:
        print(f"{progress_prefix} Skipping existing {target_file.name}")
        return

    print(f"{progress_prefix} Generating {target_file.name}")
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            text = get_text_response(client, model_name, request_user, prompt)
            target_file.write_text(text + "\n", encoding="utf-8")
            print(f"{progress_prefix} Saved {target_file.name}")
            last_error = None
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"{progress_prefix} Attempt {attempt}/{max_retries} failed: {exc}")
            if attempt < max_retries:
                time.sleep(delay_seconds * attempt)
    if last_error is not None:
        raise RuntimeError(f"Failed to generate data for {target_file.name}") from last_error


def generate_dataset(
    output_dir: Path,
    brand_output_dir: Path,
    overwrite: bool,
    max_retries: int,
    delay_seconds: float,
    count: int,
    workers: int,
) -> None:
    if count < 1:
        raise ValueError("count must be at least 1")
    if count > len(CAR_MODELS):
        raise ValueError(f"count cannot be greater than {len(CAR_MODELS)}")

    client, model_name, request_user = load_client()
    output_dir.mkdir(parents=True, exist_ok=True)
    brand_output_dir.mkdir(parents=True, exist_ok=True)
    selected_cars = CAR_MODELS[:count]

    total = len(selected_cars)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        car_futures = [
            executor.submit(
                write_with_retries,
                client=client,
                model_name=model_name,
                request_user=request_user,
                prompt=build_car_prompt(brand, model),
                target_file=output_dir / f"{sanitize_name(f'{brand}_{model}')}.txt",
                overwrite=overwrite,
                max_retries=max_retries,
                delay_seconds=delay_seconds,
                progress_prefix=f"[car {index}/{total}]",
            )
            for index, (brand, model) in enumerate(selected_cars, start=1)
        ]
        for future in as_completed(car_futures):
            future.result()

    unique_brands = sorted({brand for brand, _ in selected_cars})
    brand_total = len(unique_brands)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        brand_futures = [
            executor.submit(
                write_with_retries,
                client=client,
                model_name=model_name,
                request_user=request_user,
                prompt=build_brand_prompt(brand),
                target_file=brand_output_dir / f"{sanitize_name(brand)}.txt",
                overwrite=overwrite,
                max_retries=max_retries,
                delay_seconds=delay_seconds,
                progress_prefix=f"[brand {index}/{brand_total}]",
            )
            for index, brand in enumerate(unique_brands, start=1)
        ]
        for future in as_completed(brand_futures):
            future.result()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate car-model text dataset using an LLM.")
    parser.add_argument(
        "--output-dir",
        default=str(CURRENT_DIR / "dataset"),
        help="Directory where car files (brand_model.txt) will be written.",
    )
    parser.add_argument(
        "--brand-output-dir",
        default=str(CURRENT_DIR / "dataset" / "brands"),
        help="Directory where brand files (brand.txt) will be written.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="How many car datasets to generate (1 to 100).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files instead of skipping.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Max retries per car when an API call fails.",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=2.0,
        help="Base delay in seconds for retry backoff.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=6,
        help="Number of worker threads for parallel API calls.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    brand_output_dir = Path(args.brand_output_dir).resolve()
    os.environ.setdefault("OLLAMA_MODEL", "llama3:8b")
    generate_dataset(
        output_dir=output_dir,
        brand_output_dir=brand_output_dir,
        overwrite=args.overwrite,
        max_retries=max(1, int(args.max_retries)),
        delay_seconds=max(0.0, float(args.delay_seconds)),
        count=int(args.count),
        workers=max(1, int(args.workers)),
    )
    print(f"Done. Car dataset written to: {output_dir}")
    print(f"Done. Brand dataset written to: {brand_output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
