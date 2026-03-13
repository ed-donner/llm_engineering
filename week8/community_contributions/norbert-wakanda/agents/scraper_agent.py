"""
ScraperAgent — scrapes a Jumia URL and returns 5 structured product listings.
"""

import json
import logging
import os
import re
import sys

from dotenv import load_dotenv
from openai import OpenAI

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from tools import scrape_url, SCRAPE_URL_TOOL

load_dotenv(override=True)


class ScraperAgent:
    """
    An agent that scrapes an e-commerce URL and returns exactly 5 structured
    product listings using a tool-calling LLM loop.

    The agent asks the LLM to choose the right Jumia URL based on the user
    query, calls the scrape_url tool, then instructs the model to parse the
    raw page text and return a clean JSON list of products.
    """

    name = "Scraper Agent"
    color = "\033[36m"   # cyan
    BG_BLACK = "\033[40m"
    RESET = "\033[0m"

    MODEL = "gpt-4o-mini"
    MAX_TURNS = 10

    SYSTEM_PROMPT = """\
You are a product research assistant.

When the user asks for products:
  1. Call the scrape_url tool with a relevant Jumia Kenya URL.
     Use URLs like: https://www.jumia.co.ke/phones-tablets/?q=phones
     Adjust the path and query string to match what the user wants.
  2. Read through the scraped text and identify real product listings.
     A product listing has a name and a price (KSh).
  3. Pick the 5 most relevant, clearly priced products.
  4. Convert all prices from KSh to USD by dividing by 130 and rounding to the nearest whole number.
  5. Respond with ONLY a valid JSON array — no extra text, no markdown fences.

Each object in the array must have exactly these fields:
  - "title"       : the full product name as it appears on the page
  - "category"    : product category (e.g. "Mobile Phones", "Laptops", "Tablets")
  - "brand"       : brand name extracted from the title
  - "description" : one clear sentence about what the product is and its key specs
  - "price"       : USD price as a plain whole-number string, e.g. "101"

Rules:
  - Return EXACTLY 5 items.
  - No text before or after the JSON array.
  - "price" must be a plain number string like "101" — never "KSh 13,180" or "$101".
  - "description" must be one factual sentence — no marketing language.

Example of one correct item:
{
  "title": "Samsung Galaxy A06, 6.7\\" , 4GB RAM+ 64GB (Dual SIM), 5000mAh, Black",
  "category": "Mobile Phones",
  "brand": "Samsung",
  "description": "The Samsung Galaxy A06 features a 6.7\\" display, 4GB RAM, 64GB storage, and a 5000mAh battery.",
  "price": "78"
}
"""

    def __init__(self):
        """
        Initialise the ScraperAgent by setting up the OpenAI client and logger.
        """
        self.logger = logging.getLogger(self.name)
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )
        self.log("ScraperAgent initialised")

    def log(self, message: str) -> None:
        """
        Log an info message prefixed with the agent name and coloured output.

        Args:
            message: The message to log.
        """
        styled = f"{self.BG_BLACK}{self.color}[{self.name}] {message}{self.RESET}"
        self.logger.info(styled)

    def _handle_tool_call(self, tool_call) -> dict:
        """
        Execute a single tool call and return the formatted result message.

        Args:
            tool_call: A ToolCall object from the OpenAI response.

        Returns:
            A dict formatted as an OpenAI tool result message.
        """
        args = json.loads(tool_call.function.arguments)

        if tool_call.function.name == "scrape_url":
            self.log(f"Calling scrape_url with URL: {args.get('url', '')}")
            result = scrape_url(url=args["url"])
        else:
            result = f"Unknown tool: {tool_call.function.name}"

        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        }

    def _parse_response(self, raw: str) -> list:
        """
        Parse and validate the model's final JSON response.

        Strips markdown code fences if present, parses the JSON, and
        validates that the result is a list of exactly 5 items.

        Args:
            raw: Raw string content from the model's final message.

        Returns:
            A validated list of 5 product dicts.

        Raises:
            ValueError: If the content is not valid JSON or not exactly 5 items.
        """
        if raw.startswith("```"):
            raw = re.sub(r"^```[\w]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw).strip()

        try:
            products = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Model returned invalid JSON: {exc}\nRaw response:\n{raw}"
            ) from exc

        if not isinstance(products, list) or len(products) != 5:
            raise ValueError(
                f"Expected a JSON array of 5 items, got {type(products).__name__} "
                f"with {len(products) if isinstance(products, list) else '?'} items."
            )

        return products

    def scrape(self, user_query: str) -> list:
        """
        Run the tool-calling agent loop for a given product query.

        Sends the query to the LLM, executes any tool calls it requests,
        and returns the final structured list of 5 products.

        Args:
            user_query: Natural-language product request, e.g. "I want phones".

        Returns:
            A list of exactly 5 product dicts, each with title, category,
            brand, description, and price (USD).

        Raises:
            ValueError: If the model returns malformed JSON or not 5 items.
            RuntimeError: If the agent does not finish within MAX_TURNS.
        """
        self.log(f"Starting scrape for query: '{user_query}'")

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user",   "content": user_query},
        ]

        for turn in range(1, self.MAX_TURNS + 1):
            self.log(f"Turn {turn}/{self.MAX_TURNS}")

            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                tools=[SCRAPE_URL_TOOL],
                tool_choice="auto",
            )

            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason
            messages.append(message)

            if finish_reason == "tool_calls":
                for tool_call in message.tool_calls:
                    messages.append(self._handle_tool_call(tool_call))

            else:
                products = self._parse_response(message.content.strip())
                self.log(f"Scrape complete — returning {len(products)} products")
                return products

        raise RuntimeError(
            f"ScraperAgent did not complete within {self.MAX_TURNS} turns."
        )
