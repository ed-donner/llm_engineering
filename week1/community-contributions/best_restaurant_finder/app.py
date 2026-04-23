import os
import json
from dotenv import load_dotenv
from scraper import fetch_tripadvisor_restaurants
from openai import OpenAI
from IPython import get_ipython
from IPython.display import Markdown, display, update_display


load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

if api_key and api_key.startswith('sk-proj-') and len(api_key)>10:
    print("API key looks good so far")
else:
    print("There might be a problem with your API key? Please visit the troubleshooting notebook!")
    
MODEL = 'gpt-5-nano'
openai = OpenAI()


# restaurants = fetch_tripadvisor_restaurants("https://wanderlog.com/list/geoCategory/197906/where-to-eat-best-restaurants-in-islamabad")
# payload = json.dumps(restaurants, indent=2)

# # `IPython.display.display(Markdown(...))` is meant for notebooks. When run from a
# # regular terminal, it typically prints `<IPython.core.display.Markdown object>`
# # instead of rendering. Detect this and fall back to plain stdout.
# try:
#     from IPython import get_ipython
#     from IPython.display import Markdown, display

#     if get_ipython():
#         display(Markdown(payload))
#     else:
#         print(payload)
# except Exception:
#     print(payload)

# print(f"Fetched {len(restaurants)} restaurants.")

restaurant_system_prompt = """
You are a system agent that filters a list of restaurants to find ONLY “pure desi” (authentic Pakistani/sub-continental traditional cuisine) restaurants.

Input:
You will be given a JSON object with a list of restaurants, each having:
- name: string
- url: string

Task:
For each restaurant, determine whether it is NOT primarily offering “fast food”.
Interpret “fast food” as restaurants whose core offering is mainly burgers, fries/chicken buckets, pizza, dough-based quick meals, international chain fast-food, or other “grab-and-go” fast-food concepts.
A “pure desi” restaurant should primarily offer traditional Desi/Pakistani cuisine such as: desi biryani, karahi, handi, nihari, haleem, kebabs (desi preparations), parathas with desi fillings, curries/gravies, dal/daal, desi desserts, etc.

How to decide:
1. Open and review the restaurant’s webpage using the provided `url`.
2. Base your decision only on observable evidence from the page (menu, description, categories, photos/cuisine labels).
3. If the page clearly indicates the restaurant is fast-food focused, exclude it.
4. If the page clearly indicates traditional desi cuisine as the main focus, include it.
5. If unclear or you cannot verify the cuisine due to missing info or access issues, be conservative: exclude it (do NOT guess).

Output format (strict JSON, no extra text):
{
  "restaurants": [
    {"name": "<restaurant name>", "url": "<restaurant url>"},
    {"name": "<restaurant name>", "url": "<restaurant url>"}
  ]
}

Return only the restaurants that meet the “pure desi and not fast-food-focused” criteria.
"""

def get_restaurants_user_prompt(url):
    restaurants = fetch_tripadvisor_restaurants(url)
    user_prompt = f"""
Here is a list of restaurants and their links from {url}.
Please identify ONLY the restaurants that are pure desi (traditional Pakistani/sub-continental cuisine)
and are NOT primarily fast food.

Return STRICT JSON in this exact shape:
{{
  "restaurants": [
    {{"name": "<restaurant name>", "url": "<restaurant url>"}}
  ]
}}

Use only the provided data and keep only entries that match the criteria.
Restaurants:
"""
    user_prompt += json.dumps({"restaurants": restaurants}, indent=2)
    return user_prompt

def select_relevant_restaurants(url):
    print(f"Selecting relevant restaurants for {url} by calling {MODEL}")
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": restaurant_system_prompt},
            {"role": "user", "content": get_restaurants_user_prompt(url)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    links = json.loads(result)
    return links

# print(c("https://wanderlog.com/list/geoCategory/197906/where-to-eat-best-restaurants-in-islamabad"))


restaurant_analysis_system_prompt = """
You are a restaurant analysis assistant.

You will receive a list of pre-filtered restaurants (from `select_relevant_restaurants`) with names and links.
Your task is to analyze the restaurants and identify which one(s) offer the best overall food experience.

Evaluation criteria:
1. Food options/variety and quality signals from available menu or cuisine data.
2. Ratings and number of ratings (higher rating with meaningful volume is stronger).
3. What people are saying in reviews (overall sentiment, common praise, common complaints).
4. Practical Islamabad location details (area/sector/address) for the shortlisted best option(s).

Decision rules:
- Prefer evidence-based conclusions from provided data.
- If data is missing for a restaurant, mention uncertainty and do not invent facts.
- If multiple restaurants are very close, return top 3 ranked options.

Output requirements:
- Respond in markdown (no code blocks).
- Use sections exactly in this order:
  1) Best Restaurant Recommendation
  2) Why It Is Best
  3) Ratings and Review Signals
  4) Location in Islamabad
  5) Runner-ups (if applicable)
- In "Location in Islamabad", include the most specific available location info for each recommended restaurant:
  name, area/sector, full address (if available), and map/location link if provided.
"""

def get_restaurant_analysis_user_prompt(url):
    restaurants = select_relevant_restaurants(url)
    user_prompt = f"""
Here is a list of restaurants and their links from {url}.
Please analyze these restaurants and identify which one(s) offer the best overall food experience.
Use only evidence available from the provided restaurant entries and their linked pages.

Focus your comparison on:
- food options/variety and quality signals
- rating quality (rating and number of ratings)
- review sentiment (common praise and complaints)
- practical location details in Islamabad

If one restaurant is clearly strongest, recommend it as the best.
If results are close, provide top 3 ranked options.

Restaurant data:
"""
    user_prompt += json.dumps(restaurants, indent=2)
    return user_prompt


def stream_restaurant_analysis(url):
    stream = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": restaurant_analysis_system_prompt},
            {"role": "user", "content": get_restaurant_analysis_user_prompt(url)}
          ],
        stream=True
    )    
    response = ""
    in_notebook = bool(get_ipython())
    display_handle = display(Markdown(""), display_id=True) if in_notebook else None

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if not delta:
            continue

        response += delta
        if in_notebook and display_handle:
            update_display(Markdown(response), display_id=display_handle.display_id)
        else:
            # Stream token-by-token in terminal instead of re-printing full text.
            print(delta, end="", flush=True)

    if not in_notebook:
        print()

    return response

print(stream_restaurant_analysis("https://wanderlog.com/list/geoCategory/197906/where-to-eat-best-restaurants-in-islamabad"))