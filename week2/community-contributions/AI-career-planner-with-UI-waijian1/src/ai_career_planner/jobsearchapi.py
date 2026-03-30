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

def search_job(query, country_code, num_pages=5):
    params = {
        "query": query,
        "page": "1",
        "num_pages": str(num_pages),
        "country": country_code.lower(),
        "date_posted": "week"
    }

    response = requests.get(API_URL, headers=HEADERS, params=params)

    data = response.json()

    jobs = []

    for job in data["data"]:
        jobs.append({
            "title": job.get("job_title"),
            "company": job.get("employer_name"),
            "website": job.get("employer_website"),
            "job_apply_link": job.get("job_apply_link"),
            "description": job.get("job_description")
        })

    return jobs

def extract_job_details(job_title, country, country_code):
    search_result = []

    query = job_title + 'in ' + country

    jobs = search_job(query, country_code)

    for each in jobs:
        if each['description']:
            search_result.append(each['title'] + 'in ' + each['company'])
            search_result.append(each['description'])

    print(f'Total job found from active job posting: {len(jobs) // 2}')

    active_job = '\n'.join(search_result)

    return active_job

if __name__ == "__main__":
    jobs = search_job('machine learning engineer in singapore')
    print(jobs)
 