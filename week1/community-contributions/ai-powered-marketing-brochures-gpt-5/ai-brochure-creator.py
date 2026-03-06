from ai_core import AICore
from ai_brochure_config import AIBrochureConfig
from extractor_of_relevant_links import ExtractorOfRelevantLinks
from website import Website
from openai.types.responses import Response
from rich.console import Console
from rich.markdown import Markdown
from requests import Session
from concurrent.futures import ThreadPoolExecutor, as_completed
from json import loads

class BrochureCreator(AICore[str]):
    """
    Builds a short Markdown brochure for a company or individual by:
    - extracting relevant links from the website,
    - inferring the entity name and status,
    - and prompting the model using the collected page content.
    """

    @property
    def _website(self) -> Website:
        """Return the main Website instance to analyze."""
        return self.__website

    @property
    def _extractor(self) -> ExtractorOfRelevantLinks:
        """Return the helper responsible for extracting relevant links."""
        return self.__extractor

    def __init__(self, config: AIBrochureConfig, website: Website) -> None:
        """
        Initialize the brochure creator with configuration and target website.

        Parameters:
            config: AI and runtime configuration.
            website: The root website to analyze and summarize.
        """
        system_behavior: str = ("You are an assistant that analyzes the contents of several relevant pages from a company website "
                                "and creates a short brochure about the company for prospective customers, investors and recruits. "
                                "Include details of company culture, customers and careers/jobs if information is available. ")
        super().__init__(config, system_behavior)
        self.__website: Website = website
        self.__extractor: ExtractorOfRelevantLinks = ExtractorOfRelevantLinks(config, website)

    def create_brochure(self) -> str:
        """
        Create a short Markdown brochure based on the website's content.

        Returns:
            A Markdown string with the brochure, or a fallback message if no relevant pages were found.
        """
        relevant_pages: list[dict[str, str | Website]] = self._get_relevant_pages()
        if not relevant_pages:
            return "No relevant pages found to create a brochure."

        brochure_prompt_part: str = self._form_brochure_prompt(relevant_pages)
        inferred_company_name, inferred_status = self._infer_entity(brochure_prompt_part)

        full_brochure_prompt: str = self._form_full_prompt(inferred_company_name, inferred_status)
        response: str = self.ask(full_brochure_prompt)
        return response

    def _get_relevant_pages(self) -> list[dict[str, str | Website]]:
        """
        Resolve relevant links into Website objects using a shared session and concurrency.
        """
        relevant_pages: list[dict[str, str | Website]] = []
        relevant_links: list[dict[str, str]] = self._extractor.extract_relevant_links()["links"]
        # Limit the number of pages to fetch to keep latency and token usage reasonable.
        MAX_PAGES: int = 6
        links_subset = relevant_links[:MAX_PAGES]

        def build_page(item: dict[str, str], session: Session) -> dict[str, str | Website] | None:
            try:
                url = str(item["url"])
                page_type = str(item["type"])
                return {"type": page_type, "page": Website(url, session=session)}
            except Exception:
                return None

        with Session() as session, ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(build_page, link, session) for link in links_subset]
            for fut in as_completed(futures):
                res = fut.result()
                if res:
                    relevant_pages.append(res)

        return relevant_pages

    def _truncate_text(self, text: str, limit: int) -> str:
        """
        Truncate text to 'limit' characters to reduce tokens and latency.
        """
        if len(text) <= limit:
            return text
        return text[: max(0, limit - 20)] + "... [truncated]"

    def _form_brochure_prompt(self, relevant_pages: list[dict[str, str | Website]]) -> str:
        """
        Assemble a prompt that includes the main page and relevant pages' titles and text.

        Parameters:
            relevant_pages: List of page descriptors returned by _get_relevant_pages.

        Returns:
            A prompt string containing quoted sections per page.
        """
        QUOTE_DELIMITER: str = "\n\"\"\"\n"
        MAX_MAIN_CHARS = 6000
        MAX_PAGE_CHARS = 3000
        prompt: str = (
            f"Main page:{QUOTE_DELIMITER}"
            f"Title: {self._website.title}\n"
            f"Text:\n{self._truncate_text(self._website.text, MAX_MAIN_CHARS)}{QUOTE_DELIMITER}\n"
        )

        for page in relevant_pages:
            if isinstance(page['page'], Website) and not page['page'].fetch_failed:
                prompt += (
                    f"{page['type']}:{QUOTE_DELIMITER}"
                    f"Title: {page['page'].title}\n"
                    f"Text:\n{self._truncate_text(page['page'].text, MAX_PAGE_CHARS)}{QUOTE_DELIMITER}\n"
                )

        return prompt

    def _infer_entity(self, brochure_prompt_part: str) -> tuple[str, str]:
        """
        Infer both the entity name and status in a single model call to reduce latency.
        Returns:
            (name, status) where status is 'company' or 'individual'.
        """
        prompt = (
            "From the following website excerpts, infer the entity name and whether it is a company or an individual. "
            "Respond strictly as JSON with keys 'name' and 'status' (status must be 'company' or 'individual').\n"
            f"{brochure_prompt_part}"
        )
        raw = self.ask(prompt)
        try:
            data: dict[str, str] = loads(raw)
            name: str = str(data.get("name", "")).strip() or "Unknown"
            status: str = str(data.get("status", "")).strip().lower()
            if status not in ("company", "individual"):
                status = "company"
            return name, status
        except Exception:
            # Fallback: use entire output as name, assume company
            return raw.strip() or "Unknown", "company"

    def _form_full_prompt(self, inferred_company_name: str, inferred_status: str) -> str:
        """
        Build the final brochure-generation prompt using the inferred entity and prior history.

        Parameters:
            inferred_company_name: The inferred entity name.
            inferred_status: Either 'company' or 'individual'.

        Returns:
            A final prompt instructing the model to produce a Markdown brochure.
        """
        full_prompt: str = (f"You are looking at a {inferred_status} called {inferred_company_name}, to whom website {self._website.website_url} belongs.\n"
                            f"Build a short brochure about the {inferred_status}. Use the information from the website that is already stored in the history.\n"
                            "Your response must be in a Markdown format.")
        return full_prompt

    def ask(self, question: str) -> str:
        """
        Send a question to the model, update chat history, and return the text output.

        Parameters:
            question: The user prompt.

        Returns:
            The model output text.
        """
        self.history_manager.add_user_message(question)
        response: Response = self._ai_api.responses.create(
            model=self.config.model_name,
            instructions=self.history_manager.system_behavior,
            input=self.history_manager.chat_history,
            reasoning={ "effort": "low" }
        )
        self.history_manager.add_assistant_message(response)
        return response.output_text    

console: Console = Console()

def display_markdown(content: str) -> None:
    """
    Render Markdown content to the console using rich.
    """
    console.print(Markdown(content))

def show_summary(summary: str) -> None:
    """
    Print a Markdown summary if provided; otherwise print a fallback message.
    """
    if summary:
        display_markdown(summary)
    else:
        console.print("No summary found.")

if __name__ == "__main__":
    website: Website = Website("<put your site address here>")
    brochure_creator: BrochureCreator = BrochureCreator(AIBrochureConfig(), website)
    brochure: str = brochure_creator.create_brochure()
    display_markdown(brochure)