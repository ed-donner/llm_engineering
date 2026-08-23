# Week 1 Exercise: Recipe Book Generator

This folder contains a Week 1 LLM engineering exercise that builds a small recipe book from recipe websites.

The main notebook is `week_1_exercise.ipynb`. It starts from a list of recipe websites, collects links from those pages, normalizes and deduplicates the URLs, then uses an OpenAI model to identify which links point to individual recipe pages.

Once the recipe URLs are selected, the notebook uses `recipe_scrapers` to extract factual recipe data such as title, description, ingredients, instructions, total time, servings, and image URL. The LLM is then used again for presentation: it turns the structured scraped data into a readable Markdown recipe book without inventing missing recipe details.

## Files

- `week_1_exercise.ipynb`: end-to-end notebook for collecting recipe links, scraping recipe data, and generating the recipe book.
- `scraper.py`: small helper module for fetching website contents and links.
- `recipe_book.json`: structured recipe data exported from the notebook.
- `recipe_book.md`: Markdown version of the generated recipe book.
- `day_1_exercise.ipynb` and `day_2_exercise.ipynb`: earlier Week 1 practice notebooks.

## Pipeline

1. Define source recipe websites.
2. Fetch all links from each website.
3. Normalize relative URLs and remove duplicates.
4. Use an LLM to select links that point directly to recipes.
5. Scrape each selected recipe page with `recipe_scrapers`.
6. Track successful and failed scrapes separately.
7. Ask the LLM to format the scraped recipes as a Markdown recipe book.
8. Export the result as `recipe_book.json` and `recipe_book.md`.

## Notes

The notebook intentionally separates factual extraction from LLM formatting. Recipe facts come from the scraped web pages, while the LLM is used to classify recipe URLs and create a cleaner final presentation.

To rerun the notebook, make sure an `OPENAI_API_KEY` is available in your environment and run the cells in order.
