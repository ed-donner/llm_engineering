# Image Generator

Quick image generator using OpenAI's DALL-E 3. Generates 1024x1024 images from either random themes or your own prompts.

## Setup

You'll need an OpenAI API key. Set it as an environment variable:
```bash
export OPENAI_API_KEY='your-key-here'
```

Or just enter it when the notebook prompts you.

## How to Use

1. Open `day1_random_img_generator.ipynb`
2. Run the cells in order
3. When prompted, type either:
   - `random` - picks a random theme from the list
   - `custom` - lets you enter your own prompt
4. Wait 10-30 seconds for the image to generate
5. Image shows up in the notebook

## What's Inside

- 15 pre-made themes (cyberpunk cities, fantasy forests, etc.)
- Uses DALL-E 3 for image generation
- Standard quality to keep costs reasonable
- Simple error handling

## Cost Warning

DALL-E 3 costs about $0.04 per image. Not huge but watch your usage.

## Example Prompts

If you go custom, try stuff like:
- "a cat astronaut floating in space"
- "steampunk coffee shop interior"
- "synthwave sunset over ocean waves"

Keep it descriptive for better results.

