
import base64
from io import BytesIO
from PIL import Image


def generate_meal_image(recipe: str, client, model: str):
    """Generate an illustration of a prepared meal."""

    if not recipe or not recipe.strip():
        return None

    response = client.images.generate(
        model=model,
        prompt=f"""
        Create a photorealistic food photography image
        of the finished meal described below.

        Recipe:
        {recipe[:4000]}

        Requirements:
        - Show the actual ingredients from the recipe.
        - Realistic portions and presentation.
        - Beautiful restaurant-style food photography.
        - Natural lighting.
        - No text, labels, or nutritional information.
        """,
        size="1024x1024"
    )

    image_data = base64.b64decode(response.data[0].b64_json)

    return Image.open(BytesIO(image_data)).convert("RGB")


def generate_image_from_chat(chat_history, client, model):
    """Generate an image using the latest AI Chef response."""

    if not chat_history:
        return None

    for message in reversed(chat_history):
        if message["role"] == "assistant":
            return generate_meal_image(
                recipe=message["content"],
                client=client,
                model=model
            )

    return None


def generate_recipe_image(recipe, client, model):
    """Automatically generate an image if a recipe exists."""

    if not recipe:
        return None

    return generate_meal_image(
        recipe=recipe,
        client=client,
        model=model
    )

