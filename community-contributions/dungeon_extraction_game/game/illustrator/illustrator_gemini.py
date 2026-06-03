"""AI Mastered Dungeon Extraction Game scenes illustrator using Google's Gemini."""

from io import BytesIO

from dotenv import load_dotenv
from google import genai  # New Google's SDK 'genai' to replace 'generativeai'.
from PIL import Image


# Environment initialization.
load_dotenv(override=True)

# Define globals.
MODEL = 'gemini-2.5-flash-image-preview'

# Client instantiation.
CLIENT = genai.Client()


# Function definition.
def draw(prompt, size=(1024, 1024), client=CLIENT, model=MODEL):
    """Generate an image based on the prompt."""
    # Generate image.
    response = client.models.generate_content(
        model=model, contents=[prompt])
    # Process response.
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image_data = part.inline_data.data
    # Open the generated image.
    generated_image = Image.open(BytesIO(image_data))
    # Resize the image to the specified dimensions.
    resized_image = generated_image.resize(size)
    return resized_image
