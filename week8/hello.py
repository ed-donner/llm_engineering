import modal
import os
from modal import Image
from dotenv import load_dotenv

load_dotenv(override=True)
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Setup

app = modal.App("hello")
image = Image.debian_slim().pip_install("requests")

# Hello!


@app.function(image=image)
def hello() -> str:
    import requests

    response = requests.get("https://ipinfo.io/json")
    data = response.json()
    city, region, country = data["city"], data["region"], data["country"]
    return f"Hello from {city}, {region}, {country}!!"


# New - added thanks to student Tue H.!


@app.function(image=image, region="eu")
def hello_europe() -> str:
    import requests

    response = requests.get("https://ipinfo.io/json")
    data = response.json()
    city, region, country = data["city"], data["region"], data["country"]
    return f"Hello from {city}, {region}, {country}!!"

@app.function(image=image)
def get_new_data() -> str:
    import requests
    def get_top_news() -> str:
        response = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}")
        data = response.json()
        return data["articles"][0]["title"]

    response = requests.get("https://ipinfo.io/json")
    data = response.json()
    city, region, country = data["city"], data["region"], data["country"]
    top_news = get_top_news()
    return f"Hello from {city}, {region}, {country}!!\n{top_news}"