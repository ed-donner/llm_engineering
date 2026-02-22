"""AI Mastered Dungeon Extraction Game scenes illustrator using OpenAI's GPT."""

import base64
from io import BytesIO

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image


# Environment initialization.
load_dotenv(override=True)

# Define global defaults.
MODEL = 'gpt-image-1'
QUALITY = 'low'

# Client instantiation.
CLIENT = OpenAI()


# Function definition.
def draw(prompt, size=(1024, 1024), client=CLIENT, model=MODEL, quality=QUALITY):
    """Generate an image based on the prompt."""
    # Generate image.
    response = client.images.generate(
        model=model, prompt=prompt, n=1,
        size=f'{size[0]}x{size[1]}',
        output_format='png',
        quality=quality)
    # Process response.
    return Image.open(BytesIO(base64.b64decode(response.data[0].b64_json)))
