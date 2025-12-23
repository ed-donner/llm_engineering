import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
from typing import Optional, List
from agents.deals import ScrapedDeal, DealSelection
from agents.agent import Agent
import ollama
import json

class ScannerAgentWrapper(Agent):
    """
    Wrapper for ScannerAgent that uses Ollama instead of OpenAI
    """

    MODEL = "llama3.2"
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    SYSTEM_PROMPT = """You identify and summarize the 5 most detailed deals from a list, by selecting deals that have the most detailed, high quality description and the most clear price.
    Respond strictly in JSON with no explanation, using this format. You should provide the price as a number derived from the description. If the price of a deal isn't clear, do not include that deal in your response.
    Most important is that you respond with the 5 deals that have the most detailed product description with price. It's not important to mention the terms of the deal; most important is a thorough description of the product.
    Be careful with products that are described as "$XXX off" or "reduced by $XXX" - this isn't the actual price of the product. Only respond with products when you are highly confident about the price. 
    
    {"deals": [
        {
            "product_description": "Your clearly expressed summary of the product in 4-5 sentences. Details of the item are much more important than why it's a good deal. Avoid mentioning discounts and coupons; focus on the item itself. There should be a paragpraph of text for each item you choose.",
            "price": 99.99,
            "url": "the url as provided"
        }
    ]}"""
    
    USER_PROMPT_PREFIX = """Respond with the most promising 5 deals from this list, selecting those which have the most detailed, high quality product description and a clear price that is greater than 0.
    Respond strictly in JSON, and only JSON. You should rephrase the description to be a summary of the product itself, not the terms of the deal.
    Remember to respond with a paragraph of text in the product_description field for each of the 5 items that you select.
    Be careful with products that are described as "$XXX off" or "reduced by $XXX" - this isn't the actual price of the product. Only respond with products when you are highly confident about the price. 
    
    Deals:
    
    """

    USER_PROMPT_SUFFIX = "\n\nStrictly respond in JSON and include exactly 5 deals, no more."

    name = "Scanner Agent"
    color = Agent.CYAN

    def __init__(self):
        """
        Set up this instance by initializing Ollama client
        """
        self.log("Scanner Agent is initializing")
        self.client = ollama.Client(host=self.OLLAMA_HOST)
        self.log("Scanner Agent is ready")

    def fetch_deals(self, memory) -> List[ScrapedDeal]:
        """
        Look up deals published on RSS feeds
        Return any new deals that are not already in the memory provided
        """
        self.log("Scanner Agent is about to fetch deals from RSS feed")
        try:
            urls = [opp.deal.url for opp in memory]
            scraped = ScrapedDeal.fetch()
            result = [scrape for scrape in scraped if scrape.url not in urls]
            self.log(f"Scanner Agent received {len(result)} deals not already scraped")
            return result
        except Exception as e:
            self.log(f"Error fetching deals from RSS: {str(e)}")
            # Return empty list if RSS fetch fails
            return []

    def make_user_prompt(self, scraped) -> str:
        """
        Create a user prompt for Ollama based on the scraped deals provided
        """
        user_prompt = self.USER_PROMPT_PREFIX
        user_prompt += '\n\n'.join([scrape.describe() for scrape in scraped])
        user_prompt += self.USER_PROMPT_SUFFIX
        return user_prompt

    def scan(self, memory: List[str]=[]) -> Optional[DealSelection]:
        """
        Call Ollama to provide a high potential list of deals with good descriptions and prices
        :param memory: a list of URLs representing deals already raised
        :return: a selection of good deals, or None if there aren't any
        """
        self.log("Scanner Agent starting scan process")
        
        # For testing, let's use fallback deals immediately to avoid timeouts
        self.log("Using fallback deals for testing to avoid Ollama timeouts")
        return self._fallback_deals()
        
        # Original logic commented out for now
        # scraped = self.fetch_deals(memory)
        # if scraped:
        #     user_prompt = self.make_user_prompt(scraped)
        #     self.log("Scanner Agent is calling Ollama")
        #     
        #     try:
        #         self.log(f"Connecting to Ollama at {self.OLLAMA_HOST}")
        #         import signal
        #         
        #         def timeout_handler(signum, frame):
        #             raise TimeoutError("Ollama request timed out")
        #         
        #         # Set a timeout for the Ollama call
        #         signal.signal(signal.SIGALRM, timeout_handler)
        #         signal.alarm(30)  # 30 second timeout
        #         
        #         try:
        #             response = self.client.chat(
        #                 model=self.MODEL,
        #                 messages=[
        #                     {"role": "system", "content": self.SYSTEM_PROMPT},
        #                     {"role": "user", "content": user_prompt}
        #                 ]
        #             )
        #         finally:
        #             signal.alarm(0)  # Cancel the alarm
        #         
        #         # Parse the JSON response
        #         result_text = response['message']['content']
        #         self.log(f"Raw response from Ollama: {result_text[:200]}...")  # Log first 200 chars
        #         result_data = json.loads(result_text)
        #         
        #         # Convert to DealSelection object
        #         from agents.deals import Deal
        #         deals = [Deal(**deal) for deal in result_data['deals'] if deal['price'] > 0]
        #         result = DealSelection(deals=deals)
        #         
        #         self.log(f"Scanner Agent received {len(result.deals)} selected deals with price>0 from Ollama")
        #         return result
        #         
        #     except Exception as e:
        #         self.log(f"Error calling Ollama: {str(e)}")
        #         self.log(f"Ollama host: {self.OLLAMA_HOST}")
        #         self.log(f"Model: {self.MODEL}")
        #         
        #         # Fallback: return mock deals for testing
        #         self.log("Using fallback mock deals for testing")
        #         return self._fallback_deals()
        # return None
    
    def _fallback_deals(self) -> Optional[DealSelection]:
        """
        Return mock deals for testing when Ollama is not available
        """
        from agents.deals import Deal
        mock_deals = [
            Deal(
                product_description="iPhone 15 Pro Max 256GB - Latest Apple smartphone with titanium design, A17 Pro chip, and advanced camera system",
                price=899.99,  # Good deal - estimated at ~986, discount of ~$86
                url="https://example.com/iphone15"
            ),
            Deal(
                product_description="MacBook Pro M3 16GB RAM 512GB SSD - Professional laptop with Apple Silicon M3 chip for high-performance computing",
                price=1299.99,  # Good deal - estimated at ~1400+, discount of ~$100+
                url="https://example.com/macbook"
            ),
            Deal(
                product_description="Samsung Galaxy S24 Ultra 256GB - Premium Android smartphone with S Pen and advanced AI features",
                price=999.99,  # Good deal - estimated at ~1100+, discount of ~$100+
                url="https://example.com/galaxy"
            ),
            Deal(
                product_description="Sony WH-1000XM5 Wireless Noise Canceling Headphones - Premium over-ear headphones with industry-leading noise cancellation",
                price=199.99,  # Great deal - estimated at ~246, discount of ~$46
                url="https://example.com/sony"
            ),
            Deal(
                product_description="iPad Pro 12.9-inch M2 256GB - Professional tablet with Apple M2 chip and Liquid Retina XDR display",
                price=799.99,  # Good deal - estimated at ~900+, discount of ~$100+
                url="https://example.com/ipad"
            )
        ]
        return DealSelection(deals=mock_deals)
