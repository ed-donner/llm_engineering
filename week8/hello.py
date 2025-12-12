import modal
from modal import Image

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
