from ai_brochure_config import AIBrochureConfig
from website import Website
from ai_core import AICore
from openai.types.responses import Response
from json import loads

RelevantLinksDict = dict[str, list[dict[str, str]]]

class ExtractorOfRelevantLinks(AICore[RelevantLinksDict]):
    """
    Extractor for relevant links from a website.
    """

    @property
    def website(self) -> Website:
        """Return the root Website whose links are being analyzed."""
        return self.__website

    def __init__(self, config: AIBrochureConfig, website: Website) -> None:
        """
        Initialize the extractor with configuration and target website.

        Parameters:
            config: AI and runtime configuration.
            website: The Website from which links were collected.
        """
        system_behavior: str = ("You are an expert in creation of online advertisement materials."
                                  "You are going to be provided with a list of links found on a website."
                                  "You are able to decide which of the links would be most relevant to include in a brochure about the company,"
                                  "such as links to an About page or a Company page or Careers/Jobs pages.\n"
                                  "You should respond in JSON as in this example:")
        system_behavior += """
        {
            "links": [
                {"type": "about page", "url": "https://www.example.com/about"},
                {"type": "company page", "url": "https://www.another_example.net/company"},
                {"type": "careers page", "url": "https://ex.one_more_example.org/careers"}
            ]
        }
        """
        super().__init__(config, system_behavior)
        self.__website: Website = website

    def get_links_user_prompt(self) -> str:
        """
        Build a user prompt listing discovered links and instructions for relevance filtering.

        Returns:
            A string to send to the model listing links and guidance.
        """
        starter_part: str = (f"Here is a list of links found on the website of {self.website.website_url} - "
                             "please decide which of these links are relevant web links for a brochure about company."
                             "Respond with full HTTPS URLs. Avoid including Terms of Service, Privacy, email links.\n"
                             "Links (some might be relative links):\n")

        links_part: str = "\n".join(f"- {link}" for link in self.website.links_on_page) if self.website.links_on_page else "No links found."

        return starter_part + links_part

    def extract_relevant_links(self) -> RelevantLinksDict:
        """
        Request the model to select relevant links for brochure creation.

        Returns:
            A dictionary with a 'links' array containing objects with 'type' and 'url'.
        """
        user_prompt = self.get_links_user_prompt()
        response = self.ask(user_prompt)
        return response

    def ask(self, question: str) -> RelevantLinksDict:
        """
        Send a question to the model and parse the JSON response.

        Parameters:
            question: The prompt to submit.

        Returns:
            RelevantLinksDict: Parsed JSON containing selected links.
        """
        self.history_manager.add_user_message(question)
        
        response: Response = self._ai_api.responses.create(
            model=self.config.model_name,
            instructions=self.history_manager.system_behavior,
            reasoning={ "effort": "low" },
            input=self.history_manager.chat_history
        )

        self.history_manager.add_assistant_message(response)
        return loads(response.output_text)