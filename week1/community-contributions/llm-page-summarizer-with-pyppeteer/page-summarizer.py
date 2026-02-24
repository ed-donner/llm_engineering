import dotenv
import asyncio

import os
os.environ['PYPPETEER_CHROMIUM_REVISION'] = '1263111'

from rich.console import Console
from rich.markdown import Markdown
from openai import OpenAI
from openai.types.chat import ChatCompletion
from typing import Optional, Union, Dict, List
from pyppeteer import launch
from pyppeteer_stealth import stealth
from random import randint

console = Console()

class Config:
    def __init__(self, filename: str = ".env"):
        dotenv.load_dotenv(filename)
        self._config = dotenv.dotenv_values(filename)

    def get(self, key: str) -> str:
        return self._config.get(key, None)

    def get_int(self, key: str) -> int:
        value = self.get(key)
        if value is not None:
            return int(value)
        return None

    def get_bool(self, key: str) -> bool:
        value = self.get(key)
        if value is not None:
            return value.lower() in ("true", "1", "yes")
        return None

    @property
    def openai_api_key(self) -> str:
        return self.get("OPENAI_API_KEY")

class Website:

    __url: str
    __title: str
    __text: str

    @property
    def url(self) -> str:
        return self.__url

    @property
    def title(self) -> str:
        return self.__title

    @property
    def text(self) -> str:
        return self.__text

    @url.setter
    def url(self, url: str) -> None:
        self.__url = url
        self.__scrape()

    def __scrape(self) -> None:
        """
        Scrape the website using pyppeteer.
        """
        import asyncio
        async def main() -> None:
            browser = await launch(headless=True)
            page = await browser.newPage()
            await stealth(page)
            
            # randomize user agent
            user_agents: List[str] = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
            ]
            ua = user_agents[randint(0, len(user_agents) - 1)]
            await page.setUserAgent(ua)
            await page.setRequestInterception(True)
            page.on("request", lambda req: asyncio.ensure_future(
                req.abort() if req.resourceType == "stylesheet" else req.continue_()
            ))
            
            try:
                await page.goto(self.url, {"timeout": 60000})
                self.__title = await page.title()
                self.__text = await page.evaluate('() => document.body.innerText')
            except Exception as e:
                console.print(f"[red]Error scraping {self.url}: {e}[red]")
            finally:
                await page.close()
                await browser.close()

        asyncio.run(main())

    def __init__(self, url: str) -> None:
        self.url = url

    def __str__(self) -> str:
        return f"Website(url={self.url}, title=\"{self.title}\")"

class LlmSummarizer:
    #region Config
    __config: Config
    @property
    def config(self) -> Config:
        if self.__config is None:
            raise ValueError("Config not initialized")
        return self.__config
    #endregion

    #region OpenAI
    __openai: OpenAI = None

    @property
    def openai(self) -> OpenAI:
        """
        Lazy load the OpenAI client. This is done to avoid creating the client if it's not needed.
        """
        if self.__openai is None:
            self.__openai = OpenAI(api_key=self.config.openai_api_key)
        return self.__openai

    #endregion

    #region System behavior
    __system_behavior: Dict[str, str] = None

    @property
    def system_behavior(self) -> Dict[str, str]:
        """
        Lazy load the system behavior. This is done to avoid creating the system behavior if it's not needed.
        """
        if self.__system_behavior is None:
            self.__system_behavior = {
                "role": "system",
                "content": (
                    "You are an assistant that analyzes the contents of a website "
                    "and provides a short summary, ignoring the text that might be navigation-related."
                    "Respond in markdown and be concise."
                )
            }
        return self.__system_behavior

    #endregion

    #region user_prompt_for

    def user_prompt_for(self, website: Website) -> Dict[str, str]:
        user_prompt_content: str = (
            f"You are looking at the website titled \"{website.title}\""
            "The content of this website is as follows; "
            "please provide a short summary of this website in markdown."
            "If it includes news or announcements, then summarize these too.\n\n"
            f"\"\"\"\n{website.text}\n\"\"\"\n\n"
        )
        return {
            "role": "user",
            "content": user_prompt_content
        }
    
    #endregion

    #region messages_for

    def messages_for(self, website: Website) -> List[Dict[str, str]]:
        """
        Create the messages for the OpenAI API.
        """
        return [
            self.system_behavior,
            self.user_prompt_for(website)
        ]
    
    #endregion

    #region summarize

    def summarize(self, website: Union[Website, str]) -> Optional[str]:
        """
        Summarize the website using the OpenAI API.
        """
        if isinstance(website, str):
            website = Website(website)
        messages: List[Dict[str, str]] = self.messages_for(website)
        try:
            response: ChatCompletion = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2,
                max_tokens=512,
            )
            return response.choices[0].message.content
        except Exception as e:
            console.print(f"[red]Error summarizing {website if isinstance(website, str) else website.url}: {e}[red]")
            return None
    
    #endregion
    
    def __init__(self, config: Config) -> None:
        self.__config = config

def display_markdown(content: str) -> None:
    """
    Display the markdown content using rich.
    """
    console.print(Markdown(content))

def show_summary(summary: str) -> None:
    """
    Show the summary of the website using rich.
    """
    if summary:
        display_markdown(summary)
    else:
        console.print("No summary found.")

if __name__ == "__main__":
    summarizer = LlmSummarizer(Config())
    summary = summarizer.summarize("https://cnn.com")
    show_summary(summary)