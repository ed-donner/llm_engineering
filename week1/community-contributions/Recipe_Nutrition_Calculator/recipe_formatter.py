"""
Recipe Data Formatter Module

Utility functions to format recipe data for LLM prompts.
"""


def format_ingredients_for_prompt(recipe_data):
    """Format ingredients list for LLM prompt."""
    ingredients_text = "\n".join([
        f"- {ing.get('quantity', '')} {ing.get('ingredient', '')} {ing.get('notes', '')}"
        for ing in recipe_data.get('ingredients', [])
    ])
    return ingredients_text


def format_ingredients_simple(recipe_data):
    """Format ingredients list without notes (for simpler prompts)."""
    ingredients_text = "\n".join([
        f"- {ing.get('quantity', '')} {ing.get('ingredient', '')}"
        for ing in recipe_data.get('ingredients', [])
    ])
    return ingredients_text


def format_instructions_for_prompt(recipe_data):
    """Format instructions for LLM prompt."""
    instructions_text = "\n".join([
        f"{i+1}. {step}"
        for i, step in enumerate(recipe_data.get('instructions', []))
    ])
    return instructions_text


def format_nutrition_for_prompt(nutrition_data):
    """Format nutrition data for substitution prompts."""
    per_serving = nutrition_data.get('per_serving', {})
    return (
        f"- Calories: {per_serving.get('calories', 'N/A')}\n"
        f"- Fat: {per_serving.get('fat_g', 'N/A')}g\n"
        f"- Saturated Fat: {per_serving.get('saturated_fat_g', 'N/A')}g\n"
        f"- Sugar: {per_serving.get('sugar_g', 'N/A')}g\n"
        f"- Sodium: {per_serving.get('sodium_mg', 'N/A')}mg"
    )

