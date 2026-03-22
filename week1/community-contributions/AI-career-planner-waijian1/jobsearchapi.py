import requests
import os
from dotenv import load_dotenv
load_dotenv(override=True)

API_URL = "https://jsearch.p.rapidapi.com/search"

RAPID_API_KEY = os.getenv('X_RAPID_API_KEY')
if not RAPID_API_KEY:
    print('X_RAPID_API_KEY not found.')

HEADERS = {
    "X-RapidAPI-Key": RAPID_API_KEY,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
}

def search_job(query, num_pages=5):
    params = {
        "query": query,
        "page": "1",
        "num_pages": str(num_pages),
        "country": "sg",
        "date_posted": "week"
    }

    response = requests.get(API_URL, headers=HEADERS, params=params)

    data = response.json()

    jobs = []

    for job in data["data"]:
        jobs.append({
            "title": job.get("job_title"),
            "company": job.get("employer_name"),
            # "country": job.get("job_country"),
            "description": job.get("job_description")
        })

    return jobs

if __name__ == "__main__":
    jobs = search_job('machine learning engineer in singapore')
    print(jobs)
 