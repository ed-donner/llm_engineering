import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

load_dotenv()

openai_api = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"
openai = OpenAI()

system_prompt = """You are a medical assistant that processes prescription text.
Your goal is to extract medicines, tests, and follow-ups in a structured JSON format.

### **Instructions:**
- Extract **medicines**, **dosages**, and **timings** if available.
- **Convert vague timings** into precise values:
  - **Before breakfast** → `07:30 AM`
  - **After lunch** → `02:00 PM`
  - **Before dinner** → `07:00 PM`
  - **After dinner** → `10:00 PM`
  - **30 minutes before breakfast** → `07:00 AM`
- If **"daily"** is mentioned without a time, **assign a logical time** between **08:00 AM - 10:00 PM**.
- If the prescription says **"every alternate day"**, return `"interval": 2` instead of just `"daily"`.

### **Tests & Follow-ups:**
- Extract **medical tests** and their required dates.
- Convert relative times (e.g., `"after 3 months"`) into **exact calendar dates**, using the prescription date.
- If the prescription date is missing, use today's date.
- Follow-up should **only be included if required**, not just for general check-ups.

### **Output Format:**
Return **only valid JSON**, structured as follows:

{
  "medicines": [
    {
      "name": "<Medicine Name>",
      "dosage": "<Dosage>",
      "timing": "<Time>",
      "interval": <Interval in days (if applicable)>
    }
  ],
  "tests": [
    {
      "name": "<Test Name>",
      "date": "<YYYY-MM-DD>"
    }
  ],
  "follow_ups": [
    {
      "date": "<YYYY-MM-DD>"
    }
  ]
}
"""

def clean_json_string(json_str):
    """Clean and validate JSON string before parsing."""
    try:
        start = json_str.find('{')
        end = json_str.rfind('}') + 1
        if start >= 0 and end > 0:
            json_str = json_str[start:end]
        
        # Remove any extra whitespace
        json_str = json_str.strip()
        
        # Attempt to parse the JSON
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON. Raw response:\n{json_str}")
        print(f"Error: {str(e)}")
        return None

def preprocess_extracted_text(extracted_text):
    """Calls GPT-4o-mini to process prescription text into structured JSON."""
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": f"Process this prescription and return ONLY valid JSON:\n\n{extracted_text}"
                }
            ],
            temperature=0.3  # Lower temperature for more consistent JSON output
        )
        
        # Get the response content
        content = response.choices[0].message.content
        
        # Clean and parse the JSON
        parsed_data = clean_json_string(content)
        
        if parsed_data is None:
            return {
                "medicines": [],
                "tests": [],
                "follow_ups": []
            }
            
        return parsed_data
        
    except Exception as e:
        print(f"Error in API call or processing: {str(e)}")
        return {
            "medicines": [],
            "tests": [],
            "follow_ups": []
        }

def process_dates(data):
    """Adjusts test dates and follow-up based on the prescription date or today's date."""
    try:
        # Extract prescription date (if available) or use today's date
        prescription_date = datetime.strptime("02 JANUARY 2025", "%d %B %Y").date()
        
        # Process test dates
        for test in data.get("tests", []):
            if isinstance(test, dict) and "date" not in test and "after_months" in test:
                test_date = prescription_date + timedelta(days=test["after_months"] * 30)
                test["date"] = test_date.strftime("%Y-%m-%d")
        
        # Process follow-up dates
        follow_ups = data.get("follow_ups", [])
        for follow_up in follow_ups:
            if isinstance(follow_up, dict) and "date" not in follow_up and "after_months" in follow_up:
                follow_up_date = prescription_date + timedelta(days=follow_up["after_months"] * 30)
                follow_up["date"] = follow_up_date.strftime("%Y-%m-%d")
        
        return data
    
    except Exception as e:
        print(f"Error processing dates: {str(e)}")
        return data
