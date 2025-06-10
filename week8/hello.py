# Method #1  => myday.ipynb

# Method #2 => Terminal run: 
## In terminal: bash = > modal run hello.py
## Build the Docker image with requests installed.

## Package the function and upload it.

## Start a fresh, isolated cloud container.

## Run hello().

## Print the output (e.g., "Hello from Ashburn, Virginia, US!!").

## Shut down the container (ephemeral compute).


import modal
from modal import App, Image

# a simple Modal Labs app that uses ephemeral cloud compute to run a Python function remotely.

# Setup

# Creates a Modal App named "hello".

# This acts like a namespace or container for all the remote functions and resources.

app = modal.App("hello")

# Defines a custom cloud execution environment (based on a minimal Debian Linux image).

# Installs the Python package requests into that environment.

# This image is used to run the function in Modal’s cloud.

image = Image.debian_slim().pip_install("requests")

# Hello!

# Decorates the hello() function to run in the cloud, using the image defined above.

# Modal will package this function, send it to the cloud, and execute it inside an ephemeral container.

@app.function(image=image)

def hello() -> str:

# Uses the requests package to call the ipinfo.io API, which returns geolocation data based on the IP address of the compute instance (i.e., where Modal is running your code).
    
# Parses the response to extract location info.
    
# Returns a friendly message with the city, region, and country.
    
    import requests
    
    response = requests.get('https://ipinfo.io/json')
    data = response.json()
    city, region, country = data['city'], data['region'], data['country']
    return f"Hello from {city}, {region}, {country}!!"

# New - added thanks to student Tue H.!

@app.function(image=image, region="eu")
def hello_europe() -> str:
    import requests
    
    response = requests.get('https://ipinfo.io/json')
    data = response.json()
    city, region, country = data['city'], data['region'], data['country']
    return f"Hello from {city}, {region}, {country}!!"
