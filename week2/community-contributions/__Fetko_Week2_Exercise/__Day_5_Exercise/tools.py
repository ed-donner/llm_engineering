
from database import get_connection

# Tool schemas exposed to the LLM

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_food",
            "description": "Search the food database by ingredient name. Returns nutritional values per 100 grams.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Ingredient name or partial name"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_recipe_macros",
            "description": "Calculate total calories, protein, carbs and fat for a recipe using database ingredients. Names must match database entries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredients": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Exact ingredient name from the database"
                                },
                                "grams": {
                                    "type": "number",
                                    "description": "Ingredient quantity in grams"
                                }
                            },
                            "required": ["name", "grams"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["ingredients"],
                "additionalProperties": False
            }
        }
    }
]


def search_food(query: str) -> list[dict]:
    """Search for foods by name."""

    with get_connection() as conn:
        conn.row_factory = __import__("sqlite3").Row

        rows = conn.execute(
            """
            SELECT *
            FROM foods
            WHERE name LIKE ? COLLATE NOCASE
            ORDER BY name
            """,
            (f"%{query}%",)
        ).fetchall()

    return [dict(row) for row in rows]


def calculate_recipe_macros(ingredients: list[dict]) -> dict:
    """Calculate total nutrition for a list of ingredients."""

    totals = {
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fat": 0
    }

    breakdown = []
    missing = []

    with get_connection() as conn:
        for ingredient in ingredients:
            name = ingredient["name"]
            grams = ingredient["grams"]

            if not isinstance(grams, (int, float)) or isinstance(grams, bool) or grams <= 0:
                raise ValueError(f"Invalid grams for {name}")

            food = conn.execute(
                """
                SELECT calories, protein, carbs, fat
                FROM foods
                WHERE name = ? COLLATE NOCASE
                """,
                (name,)
            ).fetchone()

            if food is None:
                missing.append(name)
                continue

            factor = grams / 100

            values = {
                "calories": food[0] * factor,
                "protein": food[1] * factor,
                "carbs": food[2] * factor,
                "fat": food[3] * factor
            }

            for key in totals:
                totals[key] += values[key]

            breakdown.append({
                "name": name,
                "grams": grams,
                **{key: round(value, 1) for key, value in values.items()}
            })

    return {
        "totals": {
            key: round(value, 1)
            for key, value in totals.items()
        },
        "breakdown": breakdown,
        "missing": missing
    }




# Map LLM tool names to Python functions

AVAILABLE_TOOLS = {
    "search_food": search_food,
    "calculate_recipe_macros": calculate_recipe_macros
}


def execute_tool(tool_name: str, arguments: dict):
    """Execute a tool requested by the LLM."""

    if tool_name not in AVAILABLE_TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        return AVAILABLE_TOOLS[tool_name](**arguments)
    except (ValueError, TypeError, KeyError) as error:
        return {"error": str(error)}



