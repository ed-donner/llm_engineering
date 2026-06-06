from services.environment_service import EnvironmentService
from services.prompt_service import PromptService
from utils.scraper import Scraper
import json


class ModelService:
    def __init__(self):
        self.environment = EnvironmentService()
        self.client = self.environment.get_client()
        self.model = self.environment.get_model()

    def _select_relevant_links(self, url):
        print(f"Selecting relevant links for {url} by calling {self.model}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system",
                    "content": PromptService.get_links_fetcher_system_prompt()},
                {"role": "user",
                    "content": PromptService.get_links_fetcher_user_prompt(url)}
            ],
            response_format={"type": "json_object"}
        )
        result = response.choices[0].message.content
        links = json.loads(result)
        print(f"Found {len(links['links'])} relevant links")
        return links

    def fetch_page_and_all_relevant_links(self, url):
        contents = Scraper.fetch_website_contents(url)
        relevant_links = self._select_relevant_links(url)
        result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
        for link in relevant_links['links']:
            result += f"\n\n### Link: {link['type']}\n"
            result += Scraper.fetch_website_contents(link["url"])
        return result

    def get_brochure_markdown(self, company_name, url):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system",
                    "content": PromptService.get_brochure_model_system_prompt()},
                {"role": "user", "content": PromptService.get_brochure_model_user_prompt(
                    company_name, self.fetch_page_and_all_relevant_links(url))}
            ],
        )
        result = response.choices[0].message.content
        return result
