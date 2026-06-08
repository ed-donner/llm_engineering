from utils.scraper import Scraper


class PromptService:
    @staticmethod
    def get_links_fetcher_system_prompt():
        return """
            You are provided with a list of links found on a webpage.
            You are able to decide which of the links would be most relevant to include in a brochure about the company,
            such as links to an About page, or a Company page, or Careers/Jobs pages.
            You should respond in JSON as in this example:

            {
                "links": [
                    {"type": "about page", "url": "https://full.url/goes/here/about"},
                    {"type": "careers page", "url": "https://another.full.url/careers"}
                ]
            }
        """

    @staticmethod
    def get_links_fetcher_user_prompt(url):
        user_prompt = f"""
            Here is the list of links on the website {url} -
            Please decide which of these are relevant web links for a brochure about the company, 
            respond with the full https URL in JSON format.
            Do not include Terms of Service, Privacy, email links.

            Links (some might be relative links):

        """
        links = Scraper.fetch_website_links(url)
        user_prompt += "\n".join(links)
        return user_prompt

    @staticmethod
    def get_brochure_model_system_prompt():
        return """
            You are an assistant that analyzes the contents of several relevant pages from a company website
            and creates a short brochure about the company for prospective customers, investors and recruits.
            Respond in markdown without code blocks.
            Include details of company culture, customers and careers/jobs if you have the information.
        """

    @staticmethod
    def get_brochure_model_user_prompt(company_name, relevant_links):
        user_prompt = f"""
            You are looking at a company called: {company_name}
            Here are the contents of its landing page and other relevant pages;
            use this information to build a short brochure of the company in markdown without code blocks.\n\n
        """
        user_prompt += relevant_links
        return user_prompt
