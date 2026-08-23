"""AI Mastered Dungeon Extraction Game scenes illustrator using xAI's Grok."""

import base64
import os
from io import BytesIO

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
from xai_sdk import Client


# Environment initialization.
load_dotenv(override=True)

# Define global defaults.
MODEL = 'grok-2-image'
QUALITY = None

# Client instantiation.
XAI_API_KEY = os.getenv('XAI_API_KEY')
CLIENT = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")


# Function definition.
def draw(prompt, size=(1024, 1024), client=CLIENT, model=MODEL, quality=QUALITY):
    """Generate an image based on the prompt."""
    # Generate image.
    response = client.images.generate(
        model=model, prompt=prompt, n=1,
        response_format='b64_json')
    # Process response.
    return Image.open(BytesIO(base64.b64decode(response.data[0].b64_json)))


# xAI SDK Version:
CLIENT_X = Client(api_key=XAI_API_KEY)


def draw_x(prompt, size=(1024, 1024), client=CLIENT_X, model=MODEL, quality=QUALITY):
    """Generate an image based on the prompt."""
    # Generate image.
    response = client.image.sample(
        model=model, prompt=prompt,
        image_format='base64')
    # Process response.
    return Image.open(BytesIO(response.image))
