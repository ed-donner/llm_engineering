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

# Load_env variables from .env file
load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("OPENAI_API_KEY is not set. Please set it in your environment variables or .env file.")
else:
    print("OpenAI API key loaded successfully.")

openai = OpenAI()

SYSTEM_PROMPT = """
    You are a specialist in extracting deal information in RSS.
    You main task is to review, analyze content and exract a structured data.

    You will receive one of tow input types:

    1. Type 1: RSS feed entry data which may contain
       - fields like: (title, links, array etc.)
       - Summary or decription often contains HTML with deal detail
       - Multiple URL fields like link, links
    
    2. Type 2: HTML page contents which may contain:
         - Raw HTML from a deal webpage 
         - Product infomation, pricing, and purchase links.
           
    # TASK: Extract and structure the following information:
    1. Title: The deals's headline or main title for
         - RSS entries, Use the entry's title field directly
         - HTML: Extract the main prodict deal title

    2. Summary: A concise sumary of the deal 2-3 sentences max, focusing on the following:
        - What is being offered the product, the product spec
        - Key terms like (price, discount, percentage, original price)
        - Important conditions like (prono codes, shipping, availability, refund/new condition)
        - Remove ALL HTML tags and formatting

    3. URL: The primary links where users can access the deal:
        - Proritize direct product deal purchae links
        - Avoid tracking links, RSS links with "?=rss=1" or "?ref=rss 
        - RSS entries, Use the link field or first link in "links  array

    # EXTRACTION RUSES:       
      - **From RSS entries**: Parse the summary or decrion HTML to extract deal details
      - **Clean all HTML tags**: Remove <img>, <div>, <p>, <ul>, <li>. and all other tags
      - **Extract price**: Include specific dollar amounts, percentages, and comparisons
      - **Extract conditions**: Not promo codes, refund status, warranty info, shipping deatils
      - **URL priority**: Direct deal link > prodict page > category page
      - **Handle missing information**: Use null for any truely missing required field

    # OUTPUT FORMAT:
      Return ONLY valid JSON with this exact structure:
      {
        "title": "string",
        "summary": "string",
        "url": "string"
        }

        DO NOT include any addtional text, explanations, or markdown formatting - ONLY the JSON object.

        # EXAMPLE:
          **INPUT (RSS ENTRY)**:
          ```
           title: "Sony Microphones for $200 + free shipping"
           summary: "<p>Was $400, now $200. Use code SAVE50.</p>"
           link: "https://example.com/deal?iref=rss-c142"
          ```

        **OUTPUT**:
        ```json
            {
                "title": "Sony Microphone for $200 + free shipping",
                "summary": "Sony Microphone originally priced at $400, now available for just $200 with free shipping, Use promo code SAVE50 at checkout.",
                "url": "https://example.com/deal"
            } 
          ```

                                            -    

"""    

feeds = [
    "https://www.dealnews.com/c142/Electronics/?rss=1",
    "https://www.dealnews.com/c39/Computers/?rss=1",
    "https://www.dealnews.com/c238/Automotive/?rss=1",
    "https://www.dealnews.com/f1912/Smart-Home/?rss=1",
    "https://www.dealnews.com/c196/Home-Garden/?rss=1",
    "https://www.reddit.com/r/buildapcsales.rss",
    "https://www.reddit.com/r/deals.rss",
]

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

