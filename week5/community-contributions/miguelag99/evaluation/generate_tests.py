"""
Generates evaluation/tests.jsonl style ground truth for the PokeRAG knowledge base.

Parses the markdown files under poke-knowledge-base/ (produced by
build_knowledge_base.py) and derives test questions directly from that data,
so reference answers stay accurate to whatever is actually in the knowledge
base. Output format matches evaluation/test.py's TestQuestion schema:
{"question", "keywords", "reference_answer", "category"}.
"""

import json
import re
from pathlib import Path

KB_DIR = Path(__file__).parent.parent / "poke-knowledge-base"
POKEMON_DIR = KB_DIR / "pokemon"
ITEMS_DIR = KB_DIR / "items"
OUTPUT_FILE = Path(__file__).parent / "poke_tests.jsonl"


def parse_pokemon(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    name = re.search(r"^# (.+)$", text, re.MULTILINE).group(1)
    pokedex_id = int(re.search(r"\*\*Pokedex ID:\*\* (\d+)", text).group(1))
    types = [t.strip() for t in re.search(r"\*\*Type\(s\):\*\* (.+)", text).group(1).split(",")]
    height = float(re.search(r"\*\*Height:\*\* ([\d.]+) m", text).group(1))
    weight = float(re.search(r"\*\*Weight:\*\* ([\d.]+) kg", text).group(1))
    abilities = [a.strip() for a in re.search(r"\*\*Abilities:\*\* (.+)", text).group(1).split(",")]
    red_blue = re.search(r"\*\*Red/Blue:\*\* (.+)", text)
    yellow = re.search(r"\*\*Yellow:\*\* (.+)", text)
    return {
        "name": name,
        "id": pokedex_id,
        "types": types,
        "height": height,
        "weight": weight,
        "abilities": abilities,
        "red_blue_desc": red_blue.group(1) if red_blue else None,
        "yellow_desc": yellow.group(1) if yellow else None,
    }


def parse_item(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    name = re.search(r"^# (.+)$", text, re.MULTILINE).group(1)
    item_id = int(re.search(r"\*\*Item ID:\*\* (\d+)", text).group(1))
    category = re.search(r"\*\*Category:\*\* (.+)", text).group(1)
    cost_match = re.search(r"\*\*Cost:\*\* (\d+)", text)
    cost = int(cost_match.group(1)) if cost_match else None
    attrs_match = re.search(r"\*\*Attributes:\*\* (.+)", text)
    attributes = [a.strip() for a in attrs_match.group(1).split(",")] if attrs_match else []
    effect_match = re.search(r"## Effect\s*\n\s*\n(.+)", text)
    return {
        "name": name,
        "id": item_id,
        "category": category,
        "cost": cost,
        "attributes": attributes,
        "effect": effect_match.group(1).strip() if effect_match else None,
    }


def make_test(question, keywords, reference_answer, category):
    return {
        "question": question,
        "keywords": keywords,
        "reference_answer": reference_answer,
        "category": category,
    }


def build_tests(pokemon: list[dict], items: list[dict]) -> list[dict]:
    tests = []
    pokemon_by_id = {p["id"]: p for p in pokemon}
    items_by_name = {i["name"]: i for i in items}

    # --- direct_fact: pokemon types, height/weight, abilities ---
    for p in pokemon[::6]:  # every 6th pokemon -> ~25 rows
        types_str = " and ".join(p["types"])
        tests.append(make_test(
            f"What type(s) is {p['name']}?",
            [p["name"], *p["types"]],
            f"{p['name']} is a {types_str}-type Pokemon.",
            "direct_fact",
        ))

    for p in pokemon[3::7]:  # ~22 rows, offset from the above
        tests.append(make_test(
            f"What are {p['name']}'s height and weight?",
            [p["name"], str(p["height"]), str(p["weight"])],
            f"{p['name']} is {p['height']} m tall and weighs {p['weight']} kg.",
            "direct_fact",
        ))

    for p in pokemon[2::9]:  # ~17 rows
        tests.append(make_test(
            f"What abilities can {p['name']} have?",
            [p["name"], *[a.split(" (")[0] for a in p["abilities"]]],
            f"{p['name']}'s possible abilities are {', '.join(p['abilities'])}.",
            "direct_fact",
        ))

    for i in items[::7]:  # ~17 rows
        tests.append(make_test(
            f"What item category does {i['name']} belong to?",
            [i["name"], i["category"]],
            f"{i['name']} belongs to the {i['category']} category.",
            "direct_fact",
        ))

    priced_items = [i for i in items if i["cost"] is not None]
    for i in priced_items[3::8]:  # ~15 rows
        tests.append(make_test(
            f"How much does {i['name']} cost?",
            [i["name"], str(i["cost"])],
            f"{i['name']} costs {i['cost']} in-game currency (a cost of 0 means it cannot be bought in a shop).",
            "direct_fact",
        ))

    # --- numerical ---
    for p in pokemon[1::15]:  # ~10 rows
        tests.append(make_test(
            f"How many types does {p['name']} have?",
            [p["name"], str(len(p["types"]))],
            f"{p['name']} has {len(p['types'])} type(s): {', '.join(p['types'])}.",
            "numerical",
        ))

    for p in pokemon[5::20]:  # ~7 rows
        tests.append(make_test(
            f"What is {p['name']}'s Pokedex number?",
            [p["name"], str(p["id"])],
            f"{p['name']}'s Pokedex number is {p['id']}.",
            "numerical",
        ))

    # --- comparative ---
    comparisons = [
        (pokemon_by_id[1], pokemon_by_id[4]),   # bulbasaur vs charmander
        (pokemon_by_id[7], pokemon_by_id[1]),    # squirtle vs bulbasaur
        (pokemon_by_id[143], pokemon_by_id[25]),  # snorlax vs pikachu
        (pokemon_by_id[130], pokemon_by_id[129]),  # gyarados vs magikarp
        (pokemon_by_id[95], pokemon_by_id[92]),   # onix vs gastly
    ]
    for a, b in comparisons:
        heavier = a if a["weight"] > b["weight"] else b
        lighter = b if heavier is a else a
        tests.append(make_test(
            f"Which is heavier, {a['name']} or {b['name']}?",
            [a["name"], b["name"], str(heavier["weight"])],
            f"{heavier['name']} ({heavier['weight']} kg) is heavier than {lighter['name']} ({lighter['weight']} kg).",
            "comparative",
        ))
    for a, b in comparisons:
        taller = a if a["height"] > b["height"] else b
        shorter = b if taller is a else a
        tests.append(make_test(
            f"Which is taller, {a['name']} or {b['name']}?",
            [a["name"], b["name"], str(taller["height"])],
            f"{taller['name']} ({taller['height']} m) is taller than {shorter['name']} ({shorter['height']} m).",
            "comparative",
        ))

    # Pick pairs dynamically from items with known costs - PokeAPI's item
    # price data is only partially backfilled, so specific named items may
    # not have a resolvable cost at generation time.
    priced_items_by_cost = sorted(priced_items, key=lambda i: i["cost"])
    item_comparisons = []
    if len(priced_items_by_cost) >= 6:
        item_comparisons = [
            (priced_items_by_cost[0], priced_items_by_cost[-1]),
            (priced_items_by_cost[len(priced_items_by_cost) // 3], priced_items_by_cost[-2]),
            (priced_items_by_cost[1], priced_items_by_cost[len(priced_items_by_cost) // 2]),
        ]
    for a, b in item_comparisons:
        pricier = a if a["cost"] > b["cost"] else b
        cheaper = b if pricier is a else a
        tests.append(make_test(
            f"Which costs more, {a['name']} or {b['name']}?",
            [a["name"], b["name"], str(pricier["cost"])],
            f"{pricier['name']} (cost {pricier['cost']}) costs more than {cheaper['name']} (cost {cheaper['cost']}).",
            "comparative",
        ))

    # --- relationship ---
    dual_type_examples = [p for p in pokemon if len(p["types"]) == 2][:8]
    for p in dual_type_examples:
        tests.append(make_test(
            f"What is the type combination of {p['name']}?",
            [p["name"], *p["types"]],
            f"{p['name']} has the {p['types'][0]}/{p['types'][1]} type combination.",
            "relationship",
        ))

    ability_groups: dict[str, list[str]] = {}
    for p in pokemon:
        for a in p["abilities"]:
            base_ability = a.split(" (")[0]
            ability_groups.setdefault(base_ability, []).append(p["name"])
    for ability in ["Levitate", "Intimidate", "Chlorophyll", "Swarm"]:
        names = ability_groups.get(ability, [])
        if names:
            tests.append(make_test(
                f"Which Gen 1 Pokemon can have the ability {ability}?",
                [ability, *names[:5]],
                f"Gen 1 Pokemon that can have {ability} include: {', '.join(names)}.",
                "relationship",
            ))

    for category_name in ["Standard Balls", "Vitamins", "Evolution"]:
        names = sorted(i["name"] for i in items if i["category"] == category_name)
        if names:
            tests.append(make_test(
                f"Which items belong to the {category_name} category?",
                [category_name, *names[:5]],
                f"Items in the {category_name} category include: {', '.join(names)}.",
                "relationship",
            ))

    # --- spanning (combine two or more facts) ---
    spanning_pokemon = [pokemon_by_id[id_] for id_ in (1, 6, 25, 94, 150) if id_ in pokemon_by_id]
    for p in spanning_pokemon:
        tests.append(make_test(
            f"What is the Pokedex number and type of the Pokemon whose Red/Blue Pokedex entry says: \"{p['red_blue_desc']}\"?",
            [p["name"], str(p["id"]), *p["types"]],
            f"That entry describes {p['name']} (#{p['id']}), a {'/'.join(p['types'])}-type Pokemon.",
            "spanning",
        ))

    tests.append(make_test(
        "What are the height, weight, and abilities of the Pokemon with Pokedex number 25?",
        [pokemon_by_id[25]["name"], str(pokemon_by_id[25]["height"]), str(pokemon_by_id[25]["weight"])],
        f"Pokedex #25 is {pokemon_by_id[25]['name']}, {pokemon_by_id[25]['height']} m tall, "
        f"{pokemon_by_id[25]['weight']} kg, with abilities {', '.join(pokemon_by_id[25]['abilities'])}.",
        "spanning",
    ))

    master_ball = items_by_name["Master Ball"]
    master_ball_cost = master_ball["cost"] if master_ball["cost"] is not None else 0
    tests.append(make_test(
        f"What category and cost does the item with the effect \"{master_ball['effect']}\" have?",
        [master_ball["name"], master_ball["category"], str(master_ball_cost)],
        f"That item is the {master_ball['name']}, in the {master_ball['category']} category, costing {master_ball_cost}.",
        "spanning",
    ))

    # --- holistic (aggregate across the whole dataset) ---
    heaviest = max(pokemon, key=lambda p: p["weight"])
    lightest = min(pokemon, key=lambda p: p["weight"])
    tallest = max(pokemon, key=lambda p: p["height"])
    shortest = min(pokemon, key=lambda p: p["height"])
    dual_type_count = sum(1 for p in pokemon if len(p["types"]) == 2)
    single_type_count = len(pokemon) - dual_type_count
    all_types = sorted({t for p in pokemon for t in p["types"]})
    type_counts: dict[str, int] = {}
    for p in pokemon:
        for t in p["types"]:
            type_counts[t] = type_counts.get(t, 0) + 1
    most_common_type = max(type_counts, key=type_counts.get)

    most_expensive_item = max(priced_items, key=lambda i: i["cost"])
    free_items = [i["name"] for i in items if i["cost"] == 0]
    tm_count = sum(1 for i in items if i["name"].startswith("Tm"))
    hm_count = sum(1 for i in items if i["name"].startswith("Hm"))
    category_counts: dict[str, int] = {}
    for i in items:
        category_counts[i["category"]] = category_counts.get(i["category"], 0) + 1
    largest_item_category = max(category_counts, key=category_counts.get)

    tests += [
        make_test(
            "Which Gen 1 Pokemon has the highest weight?",
            [heaviest["name"], str(heaviest["weight"])],
            f"{heaviest['name']} is the heaviest Gen 1 Pokemon at {heaviest['weight']} kg.",
            "holistic",
        ),
        make_test(
            "Which Gen 1 Pokemon has the lowest weight?",
            [lightest["name"], str(lightest["weight"])],
            f"{lightest['name']} is the lightest Gen 1 Pokemon at {lightest['weight']} kg.",
            "holistic",
        ),
        make_test(
            "Which Gen 1 Pokemon is the tallest?",
            [tallest["name"], str(tallest["height"])],
            f"{tallest['name']} is the tallest Gen 1 Pokemon at {tallest['height']} m.",
            "holistic",
        ),
        make_test(
            "Which Gen 1 Pokemon is the shortest?",
            [shortest["name"], str(shortest["height"])],
            f"{shortest['name']} is the shortest Gen 1 Pokemon at {shortest['height']} m.",
            "holistic",
        ),
        make_test(
            "How many Gen 1 Pokemon have two types instead of one?",
            [str(dual_type_count), "dual"],
            f"{dual_type_count} of the 151 Gen 1 Pokemon have two types, and {single_type_count} have a single type.",
            "holistic",
        ),
        make_test(
            "How many distinct Pokemon types appear across all Gen 1 Pokemon?",
            [str(len(all_types))],
            f"There are {len(all_types)} distinct types represented across Gen 1 Pokemon: {', '.join(all_types)}.",
            "holistic",
        ),
        make_test(
            "Which Pokemon type is most common among Gen 1 Pokemon?",
            [most_common_type, str(type_counts[most_common_type])],
            f"{most_common_type.title()} is the most common type, appearing on {type_counts[most_common_type]} Gen 1 Pokemon.",
            "holistic",
        ),
        make_test(
            "How many Pokemon are documented in the knowledge base?",
            [str(len(pokemon)), "151"],
            f"The knowledge base documents all {len(pokemon)} Generation 1 Pokemon.",
            "holistic",
        ),
        make_test(
            "What is the most expensive item in the knowledge base?",
            [most_expensive_item["name"], str(most_expensive_item["cost"])],
            f"{most_expensive_item['name']} is the most expensive item, costing {most_expensive_item['cost']}.",
            "holistic",
        ),
        make_test(
            "How many items in the knowledge base have a shop cost of 0?",
            [str(len(free_items))],
            f"{len(free_items)} item(s) have a cost of 0 (not purchasable in shops): {', '.join(free_items[:5])}.",
            "holistic",
        ),
        make_test(
            "How many TMs and HMs are included in the knowledge base?",
            [str(tm_count), str(hm_count), "TM", "HM"],
            f"The knowledge base includes {tm_count} TMs and {hm_count} HMs.",
            "holistic",
        ),
        make_test(
            "Which item category has the most items in the knowledge base?",
            [largest_item_category, str(category_counts[largest_item_category])],
            f"{largest_item_category} has the most items, with {category_counts[largest_item_category]} entries.",
            "holistic",
        ),
    ]

    # --- temporal (Red/Blue vs Yellow Pokedex description differences) ---
    version_diff_pokemon = [
        p for p in pokemon
        if p["red_blue_desc"] and p["yellow_desc"] and p["red_blue_desc"] != p["yellow_desc"]
    ][:8]
    for p in version_diff_pokemon:
        tests.append(make_test(
            f"How does {p['name']}'s Pokedex description in Yellow differ from Red/Blue?",
            [p["name"], "Yellow", "Red"],
            f"In Red/Blue, {p['name']}'s entry reads: \"{p['red_blue_desc']}\". "
            f"In Yellow, it instead reads: \"{p['yellow_desc']}\".",
            "temporal",
        ))

    return tests


def main():
    pokemon = sorted((parse_pokemon(p) for p in POKEMON_DIR.glob("*.md")), key=lambda p: p["id"])
    items = sorted((parse_item(p) for p in ITEMS_DIR.glob("*.md")), key=lambda i: i["id"])

    tests = build_tests(pokemon, items)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for test in tests:
            f.write(json.dumps(test, ensure_ascii=False) + "\n")

    print(f"Wrote {len(tests)} test questions to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
