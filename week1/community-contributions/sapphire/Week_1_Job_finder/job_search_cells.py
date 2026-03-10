# =============================================================================
# 🔍 Job Search using LinkedIn Job Search API
# =============================================================================
# Copy these code blocks into your Jupyter notebook as new cells
# Run them after the cell that extracts keywords from Gemini

# =============================================================================
# CELL 1: Parse Keywords
# =============================================================================
import json
import requests

# Parse the keywords from Gemini response
try:
    keywords_list = json.loads(raw_keywords)
    print("✅ Extracted Keywords:")
    for i, keyword in enumerate(keywords_list, 1):
        print(f"   {i}. {keyword}")
except json.JSONDecodeError as e:
    print(f"❌ Error parsing keywords: {e}")
    keywords_list = []

# =============================================================================
# CELL 2: Build Job Query
# =============================================================================
# Build the job title filter from keywords
# Select the most relevant job-related keywords for the title filter
job_titles = [kw for kw in keywords_list if any(role in kw.lower() for role in ['developer', 'engineer', 'stack', 'full'])]

# If no job titles found, use the first 3 technical skills
if not job_titles:
    job_titles = keywords_list[:3]

# Create the title filter with OR logic
title_filter = ' OR '.join([f'"{title}"' for title in job_titles])

# Indian tech hub locations (Bangalore, Mumbai, Hyderabad, Pune, Chennai)
location_filter = '"Bangalore" OR "Mumbai" OR "Hyderabad" OR "Pune" OR "Chennai" OR "India"'

print(f"📋 Title Filter: {title_filter}")
print(f"📍 Location Filter: {location_filter}")

# =============================================================================
# CELL 3: Fetch Jobs from RapidAPI
# =============================================================================
# RapidAPI LinkedIn Job Search API
url = "https://linkedin-job-search-api.p.rapidapi.com/active-jb-24h"

querystring = {
    "limit": "10",
    "offset": "0",
    "title_filter": title_filter,
    "location_filter": location_filter,
    "description_type": "text"
}

headers = {
    "x-rapidapi-key": "120d73581dmshfd7b2521bde8785p1d5f15jsn58106923ff0b",
    "x-rapidapi-host": "linkedin-job-search-api.p.rapidapi.com"
}

print("🔄 Fetching jobs from LinkedIn Job Search API...")
print(f"   Query: {querystring}")

try:
    response = requests.get(url, headers=headers, params=querystring)
    response.raise_for_status()
    jobs_data = response.json()
    print(f"\n✅ API Response received successfully!")
except requests.exceptions.RequestException as e:
    print(f"❌ Error fetching jobs: {e}")
    jobs_data = []

# =============================================================================
# CELL 4: Display Job Results
# =============================================================================
# Display the job results in a nice format
from IPython.display import Markdown, display

if isinstance(jobs_data, list) and len(jobs_data) > 0:
    print(f"\n🎯 Found {len(jobs_data)} job(s) matching your profile!\n")
    print("=" * 80)
    
    for i, job in enumerate(jobs_data, 1):
        title = job.get('title', 'N/A')
        company = job.get('company_name', job.get('company', 'N/A'))
        location = job.get('location', 'N/A')
        posted_date = job.get('posted_date', job.get('date', 'N/A'))
        job_url = job.get('linkedin_job_url', job.get('url', job.get('link', 'N/A')))
        description = job.get('description', '')[:300] + '...' if len(job.get('description', '')) > 300 else job.get('description', 'No description available')
        
        print(f"\n📌 Job #{i}")
        print(f"   🏷️  Title: {title}")
        print(f"   🏢 Company: {company}")
        print(f"   📍 Location: {location}")
        print(f"   📅 Posted: {posted_date}")
        print(f"   🔗 Link: {job_url}")
        print(f"   📝 Description: {description}")
        print("-" * 80)
else:
    print("\n⚠️ No jobs found matching your criteria.")
    print("   Try adjusting the keywords or location filter.")
    print(f"\n📊 Raw API Response: {jobs_data}")

# =============================================================================
# CELL 5: Summary Statistics
# =============================================================================
# Summary Statistics
if isinstance(jobs_data, list) and len(jobs_data) > 0:
    companies = [job.get('company_name', job.get('company', 'Unknown')) for job in jobs_data]
    locations = [job.get('location', 'Unknown') for job in jobs_data]
    
    print("\n📊 Job Search Summary")
    print("=" * 40)
    print(f"   🔢 Total Jobs Found: {len(jobs_data)}")
    print(f"   🏢 Companies: {', '.join(set(companies))}")
    print(f"   📍 Locations: {', '.join(set(locations))}")
    print(f"   🔑 Keywords Used: {', '.join(keywords_list[:5])}...")
    print("\n✨ Good luck with your job search!")
