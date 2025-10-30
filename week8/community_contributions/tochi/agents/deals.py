import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict, Self
import feedparser
from tqdm import tqdm
import time
from openai import OpenAI
from typing import Optional
import json


load_dotenv(override=True)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-key-if-not-using-env")

openai = OpenAI()

feeds = [
    "https://www.dealnews.com/c142/Electronics/?rss=1",
    "https://www.dealnews.com/c39/Computers/?rss=1",
    "https://www.dealnews.com/c238/Automotive/?rss=1",
    "https://www.dealnews.com/f1912/Smart-Home/?rss=1",
    "https://www.dealnews.com/c196/Home-Garden/?rss=1",
    "https://www.reddit.com/r/buildapcsales.rss",
    "https://www.reddit.com/r/deals.rss",
]

SYSTEM_PROMPT = """
You are an RSS feed parser specializing in extracting deal information. Your task is to analyze content and extract structured data.

# INPUT TYPES
You will receive one of two input types:

**TYPE 1: RSS Feed Entry Data**
- May contain fields like: title, summary, description, link
- Summary/description often contains HTML with deal details
- Multiple URL fields may exist (link, links array, etc.)

**TYPE 2: HTML Page Content** 
- Raw HTML from a deal webpage
- Contains product information, pricing, and purchase links

# TASK
Extract and structure the following information:
1. **title**: The deal's headline or main title
   - For RSS entries: Use the entry's title field directly
   - For HTML: Extract the main product/deal title
   
2. **summary**: A concise summary of the deal (2-3 sentences max), focusing on:
   - What is being offered (product name, specs)
   - Key terms (price, discount percentage, original price)
   - Important conditions (promo codes, shipping, availability, refurb/new condition)
   - Strip ALL HTML tags and formatting
   
3. **url**: The primary link where users can access the deal
   - Prioritize direct product/deal purchase links
   - Avoid tracking links, RSS links with "?rss=1" or "?iref=rss"
   - For RSS entries, use the "link" field or first link in "links" array

# EXTRACTION RULES
- **From RSS entries**: Parse the 'summary' or 'description' HTML to extract deal details
- **Clean all HTML**: Remove <img>, <div>, <p>, <ul>, <li>, and all other tags
- **Extract pricing**: Include specific dollar amounts, percentages, and comparisons
- **Extract conditions**: Note promo codes, refurb status, warranty info, shipping details
- **URL priority**: Direct deal link > product page > category page
- **Handle missing data**: Use null for any truly missing required field

# OUTPUT FORMAT
Return ONLY valid JSON with this exact structure:
{
  "title": "string",
  "summary": "string", 
  "url": "string"
}

Do not include any additional text, explanations, or markdown formatting - only the JSON object.

# EXAMPLES

**Input (RSS Entry)**:
```
title: "Sony Headphones for $99 + free shipping"
summary: "<p>Was $199, now $99. Use code SAVE50.</p>"
link: "https://example.com/deal?iref=rss-c142"
```

**Output**:
```json
{
  "title": "Sony Headphones for $99 + free shipping",
  "summary": "Sony Headphones originally priced at $199, now available for $99 with free shipping. Use promo code SAVE50 at checkout.",
  "url": "https://example.com/deal"
}
```
"""


def gpt_parse(soup: str) -> Optional[Dict[str, str]]:
    """
    Parse RSS feed content using GPT to extract title, summary, and URL.
    
    Args:
        soup: Raw RSS feed content (HTML/text)
        
    Returns:
        Dictionary with title, summary, url keys or None if parsing fails
    """
    
    text_to_summarize = soup
    if not text_to_summarize:
        return None

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text_to_summarize},
            ],
        )
        res_text = response.choices[0].message.content
        parsed_data = json.loads(res_text)
        
        if all(
            key in parsed_data and parsed_data[key]
            for key in ["title", "summary", "url"]
        ):
            return {
                "title": parsed_data["title"],
                "summary": parsed_data["summary"],
                "url": parsed_data["url"],
            }
        else:
            print(f"Missing or empty required fields in response: {parsed_data}")
            return None
            
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from OpenAI response: {e}")
        return None
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return None

class ScrapedDeal:
    """
    A class to represent a Deal retrieved from an RSS feed
    """

    category: str
    title: str
    summary: str
    url: str
    details: str
    features: str

    def __init__(self, entry: Dict[str, str]):
        """
        Populate this instance based on the provided dict
        """

        self.title = entry["title"]
        self.summary = entry["summary"]
        self.url = entry["url"]
        self.details = self.summary
        self.features = ""

    def __repr__(self):
        """
        Return a string to describe this deal
        """
        return f"<{self.title}>"

    def describe(self):
        """
        Return a longer string to describe this deal for use in calling a model
        """
        return f"Title: {self.title}\nDetails: {self.details.strip()}\nFeatures: {self.features.strip()}\nURL: {self.url}"

    @classmethod
    def fetch(cls, show_progress: bool = False) -> List[Self]:
        """
        Retrieve all deals from the selected RSS feeds
        """
        deals = []
        skipped = 0
        
        feed_iter = tqdm(feeds) if show_progress else feeds
        for feed_url in feed_iter:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                try:
                    parsed_deal = gpt_parse(json.dumps(entry))
                    deals.append(cls(parsed_deal))
                    deals.append(cls(entry))
                    time.sleep(0.5)
                except Exception as e:
                    skipped += 1
                    print(f"Skipping deal: {str(e)}")
                    continue
        
        print(f"Fetched {len(deals)} deals successfully, skipped {skipped}")
        return deals


class Deal(BaseModel):
    """
    A class to Represent a Deal with a summary description
    """

    product_description: str
    price: float
    url: str


class DealSelection(BaseModel):
    """
    A class to Represent a list of Deals
    """

    deals: List[Deal]


class Opportunity(BaseModel):
    """
    A class to represent a possible opportunity: a Deal where we estimate
    it should cost more than it's being offered
    """

    deal: Deal
    estimate: float
    discount: float

