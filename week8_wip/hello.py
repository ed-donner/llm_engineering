import modal
from modal import App, Volume, Image

# Setup

app = modal.App("hello")
image = Image.debian_slim().pip_install("requests")
gpu = "T4"

# Hello!

@app.function(image=image)
def hello() -> str:
    import requests
    
    response = requests.get('https://ipinfo.io/json')
    data = response.json()
    city, region, country = data['city'], data['region'], data['country']
    return f"Hello from {city}, {region}, {country}!!"
