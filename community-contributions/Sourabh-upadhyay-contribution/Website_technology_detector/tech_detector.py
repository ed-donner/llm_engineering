import requests
from bs4 import BeautifulSoup

def detect_technologies(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")

        technologies = []

        # HTML version (simple detection)
        if "<!DOCTYPE html>" in response.text.lower():
            technologies.append("HTML5")

        # Detect Bootstrap CSS
        if soup.find("link", href=lambda x: x and "bootstrap" in x.lower()):
            technologies.append("Bootstrap CSS")

        # Detect jQuery
        if soup.find("script", src=lambda x: x and "jquery" in x.lower()):
            technologies.append("jQuery")

        # Detect React / Vue / Angular
        scripts = str(soup)
        if "react" in scripts.lower():
            technologies.append("React JS")
        if "vue" in scripts.lower():
            technologies.append("Vue JS")
        if "angular" in scripts.lower():
            technologies.append("Angular")

        # Detect Font Awesome icons
        if soup.find("link", href=lambda x: x and "fontawesome" in x.lower()):
            technologies.append("FontAwesome Icons")

        # Detect Google Analytics
        if "www.google-analytics.com" in scripts:
            technologies.append("Google Analytics")

        return technologies

    except Exception as e:
        return [f"Error fetching site: {e}"]

if __name__ == "__main__":
    url = input("Enter website URL: ")
    tech = detect_technologies(url)

    print("\nTechnologies Detected:")
    for t in tech:
        print(f"- {t}")