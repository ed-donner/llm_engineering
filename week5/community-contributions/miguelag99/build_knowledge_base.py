"""
Builds poke-knowledge-base/ from the official PokeAPI (https://pokeapi.co/api/v2/).

Writes one markdown file per Generation 1 Pokemon (#1-151) and one per
classic Generation 1 item, mirroring the two-subfolder-per-doc-type layout
used by knowledge-base/ elsewhere in this course.
"""

import json
import time
from pathlib import Path

import requests

API_BASE = "https://pokeapi.co/api/v2"
OUTPUT_DIR = Path(__file__).parent / "poke-knowledge-base"
POKEMON_DIR = OUTPUT_DIR / "pokemon"
ITEMS_DIR = OUTPUT_DIR / "items"
REQUEST_DELAY = 0.1

GEN1_POKEMON_COUNT = 151

# Curated list of items that actually existed in Pokemon Red/Blue/Yellow.
GEN1_ITEMS = [
    # Poke Balls
    "master-ball", "ultra-ball", "great-ball", "poke-ball", "safari-ball",
    # Medicine / status healing
    "potion", "super-potion", "hyper-potion", "max-potion", "full-restore",
    "revive", "antidote", "burn-heal", "ice-heal", "awakening",
    "paralyze-heal", "full-heal", "fresh-water", "soda-pop", "lemonade",
    # PP restoration
    "ether", "max-ether", "elixir", "max-elixir",
    # Stat vitamins / boosters
    "hp-up", "protein", "iron", "carbos", "calcium", "pp-up", "rare-candy",
    # Battle stat items
    "x-attack", "x-defense", "x-speed", "x-sp-atk", "x-accuracy",
    "dire-hit", "guard-spec",
    # Evolution stones
    "fire-stone", "water-stone", "thunder-stone", "leaf-stone", "moon-stone",
    # Field / utility items
    "escape-rope", "repel", "super-repel", "max-repel", "poke-doll",
    "nugget",
    # Key items
    "bicycle", "bike-voucher", "card-key", "coin-case", "dome-fossil",
    "helix-fossil", "old-amber", "exp-share", "lift-key",
    "oaks-parcel", "poke-flute", "town-map", "ss-ticket", "secret-key",
    "silph-scope", "dowsing-machine",
    # HMs
    "hm01", "hm02", "hm03", "hm04", "hm05",
    # TMs
    *[f"tm{i:02d}" for i in range(1, 51)],
]


def fetch(endpoint: str, name_or_id) -> dict | None:
    url = f"{API_BASE}/{endpoint}/{name_or_id}"
    response = requests.get(url)
    time.sleep(REQUEST_DELAY)
    if response.status_code != 200:
        return None
    # requests can mis-guess the response encoding when no charset header is
    # present, mangling non-ASCII characters (e.g. accented "é" in flavor
    # text) - decode the raw bytes as UTF-8 explicitly instead.
    return json.loads(response.content.decode("utf-8"))


def english_entry(entries: list[dict], text_field: str) -> str | None:
    for entry in entries:
        if entry["language"]["name"] == "en":
            return entry[text_field].replace("\n", " ").replace("\f", " ")
    return None


LANGUAGE_LABELS = {
    "ja": "Japanese",
    "ja-hrkt": "Japanese (Hiragana/Katakana)",
    "ko": "Korean",
    "zh-hans": "Chinese (Simplified)",
    "zh-hant": "Chinese (Traditional)",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "es-419": "Spanish (Latin America)",
    "it": "Italian",
    "pt-br": "Portuguese (Brazil)",
    "ru": "Russian",
    "roomaji": "Romaji",
}


def other_language_names(names: list[dict]) -> list[str]:
    entries = []
    for entry in names:
        lang = entry["language"]["name"]
        if lang == "en":
            continue
        label = LANGUAGE_LABELS.get(lang, lang.replace("-", " ").title())
        entries.append((label, entry["name"]))
    entries.sort(key=lambda pair: pair[0])
    return [f"- **{label}:** {name}" for label, name in entries]


def gen1_pokedex_descriptions(species_data: dict) -> dict[str, str]:
    descriptions = {}
    for entry in species_data["flavor_text_entries"]:
        version = entry["version"]["name"]
        if entry["language"]["name"] == "en" and version in ("red", "blue", "yellow"):
            descriptions.setdefault(version, entry["flavor_text"].replace("\n", " ").replace("\x0c", " "))
    return descriptions


def pokemon_to_markdown(data: dict, species_data: dict) -> str:
    name = data["name"].replace("-", " ").title()
    types = ", ".join(t["type"]["name"] for t in data["types"])
    abilities = []
    for a in data["abilities"]:
        label = a["ability"]["name"].replace("-", " ").title()
        if a["is_hidden"]:
            label += " (hidden)"
        abilities.append(label)

    lines = [
        f"# {name}",
        "",
        f"- **Pokedex ID:** {data['id']}",
        f"- **Type(s):** {types}",
        f"- **Height:** {data['height'] / 10} m",
        f"- **Weight:** {data['weight'] / 10} kg",
        f"- **Abilities:** {', '.join(abilities)}",
        "",
    ]

    descriptions = gen1_pokedex_descriptions(species_data)
    if descriptions:
        lines.append("## Pokedex Description")
        lines.append("")
        red_blue = descriptions.get("red") or descriptions.get("blue")
        if red_blue:
            lines.append(f"- **Red/Blue:** {red_blue}")
        yellow = descriptions.get("yellow")
        if yellow and yellow != red_blue:
            lines.append(f"- **Yellow:** {yellow}")
        lines.append("")

    return "\n".join(lines)


def item_cost(data: dict) -> int | None:
    # PokeAPI has moved from a flat "cost" field to a per-version-group
    # "prices" list (still sparsely populated as of this writing). Prefer
    # the old field if present, fall back to prices, else omit the cost.
    if "cost" in data:
        return data["cost"]
    prices = data.get("prices", [])
    if not prices:
        return None
    for preferred_group in ("red-blue", "yellow"):
        for price in prices:
            if price["version_group"]["name"] == preferred_group and price.get("purchase_price") is not None:
                return price["purchase_price"]
    for price in prices:
        if price.get("purchase_price") is not None:
            return price["purchase_price"]
    # Every entry has purchase_price: null (item can't be bought in a shop,
    # e.g. Master Ball) - treat as cost 0, matching the old flat "cost" field.
    return 0


def item_to_markdown(data: dict) -> str:
    name = data["name"].replace("-", " ").title()
    attributes = ", ".join(a["name"].replace("-", " ").title() for a in data["attributes"])
    effect = english_entry(data["effect_entries"], "short_effect")
    flavor_text = english_entry(data["flavor_text_entries"], "text")
    cost = item_cost(data)

    lines = [
        f"# {name}",
        "",
        f"- **Item ID:** {data['id']}",
        f"- **Category:** {data['category']['name'].replace('-', ' ').title()}",
    ]
    if cost is not None:
        lines.append(f"- **Cost:** {cost}")
    if attributes:
        lines.append(f"- **Attributes:** {attributes}")
    lines.append("")
    if effect:
        lines += ["## Effect", "", effect, ""]
    if flavor_text:
        lines += ["## Description", "", flavor_text, ""]

    localized_names = other_language_names(data.get("names", []))
    if localized_names:
        lines.append("## Names in Other Languages")
        lines.append("")
        lines += localized_names
        lines.append("")

    return "\n".join(lines)


def build_pokemon():
    POKEMON_DIR.mkdir(parents=True, exist_ok=True)
    failures = []
    for pokemon_id in range(1, GEN1_POKEMON_COUNT + 1):
        data = fetch("pokemon", pokemon_id)
        species_data = fetch("pokemon-species", pokemon_id)
        if data is None or species_data is None:
            failures.append(str(pokemon_id))
            print(f"WARNING: failed to fetch pokemon {pokemon_id}")
            continue
        markdown = pokemon_to_markdown(data, species_data)
        (POKEMON_DIR / f"{data['name']}.md").write_text(markdown, encoding="utf-8")
        print(f"Fetched {data['name']} ({pokemon_id}/{GEN1_POKEMON_COUNT})")
    return failures


def build_items():
    ITEMS_DIR.mkdir(parents=True, exist_ok=True)
    failures = []
    for i, item_name in enumerate(GEN1_ITEMS, start=1):
        data = fetch("item", item_name)
        if data is None:
            failures.append(item_name)
            print(f"WARNING: failed to fetch item '{item_name}'")
            continue
        markdown = item_to_markdown(data)
        (ITEMS_DIR / f"{data['name']}.md").write_text(markdown, encoding="utf-8")
        print(f"Fetched {data['name']} ({i}/{len(GEN1_ITEMS)})")
    return failures


def main():
    print("Building Pokemon markdown files...")
    pokemon_failures = build_pokemon()

    print("\nBuilding item markdown files...")
    item_failures = build_items()

    pokemon_count = len(list(POKEMON_DIR.glob("*.md")))
    item_count = len(list(ITEMS_DIR.glob("*.md")))
    print(f"\nDone. Wrote {pokemon_count} pokemon files and {item_count} item files to {OUTPUT_DIR}")

    if pokemon_failures:
        print(f"Failed pokemon ids: {pokemon_failures}")
    if item_failures:
        print(f"Failed item slugs: {item_failures}")


if __name__ == "__main__":
    main()
