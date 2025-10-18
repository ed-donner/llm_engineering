import os
import time
import sys
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI

import random
import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

load_dotenv()

class WebsiteScrapper:
    def __init__(self, url, max_retries=2, headless=True, wait_selector="body", wait_timeout=10):
        self.url = url
        self.__text = ""
        self.__title = ""
        self.headless = headless
        self.max_retries = max_retries
        self.wait_selector = wait_selector
        self.wait_timeout = wait_timeout

    def __log_html(self, html, filename="last_scraped.html"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Saved page HTML to {filename} for debugging.")
        except Exception as e:
            print(f"!!! Could not save page HTML: {e}")

    def parse(self):
        attempt = 0
        while attempt < self.max_retries:
            try:
                options = uc.ChromeOptions()
                options.headless = self.headless  # Set to False if you want to see the browser
                options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.page_load_strategy = 'normal'  # wait until fully loaded
                options.add_argument("--disable-blink-features=AutomationControlled")

                with uc.Chrome(options=options) as driver:
                    print("[Browser] Chrome started.")
                    driver.get(self.url)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(1, 3))
                    WebDriverWait(driver, self.wait_timeout).until(
                        ec.presence_of_element_located((By.CSS_SELECTOR, self.wait_selector))
                    )

                    time.sleep(1)
                    page_source = driver.page_source
                    self.__log_html(page_source)

                if "enable javascript" in page_source.lower() or "checking your browser" in page_source.lower():
                    self.__title = "Blocked by Bot Protection"
                    self.__text = "This website uses advanced protection (e.g., Cloudflare). Content not accessible."
                    return

                soup = BeautifulSoup(page_source, 'html.parser')
                self.__title = soup.title.string if soup.title else "No title found"

                for irrelevant in soup(["script", "style", "img", "input"]):
                    irrelevant.decompose()

                self.__text = soup.body.get_text(separator="\n", strip=True)
                try:
                    os.remove("last_scraped.html")
                    print("Cleaned up debug HTML file.")
                except Exception as e:
                    print(f"Could not delete debug HTML file: {e}")
                return  # Success

            except Exception as e:
                print(f"!!! Attempt {attempt + 1} failed: {e}")
                attempt += 1
                time.sleep(2)

        # All retries failed
        self.__title = "Failed to load"
        self.__text = "Website could not be scraped after several attempts."

    def get_text(self):
        return self.__text

    def get_title(self):
        return self.__title


class JSWebsiteSummarizer:
    def __init__(self, url, headless=True):
        self.url = url
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'your-key-if-not-using-env')
        self.openai = OpenAI()
        self.website_scrapper = WebsiteScrapper(url, headless=headless)
        self.system_prompt = "You are an assistant that analyzes the contents of a website \
                            and provides a short summary, ignoring text that might be navigation related. \
                            Respond in markdown."

    @staticmethod
    def __user_prompt_for(title, content):
        user_prompt = f"You are looking at a website titled {title}"
        user_prompt += "The contents of this website is as follows; \
                        please provide a short summary of this website in markdown. \
                        If it includes news or announcements, then summarize that too.\n\n"
        user_prompt += content
        return user_prompt

    def __messages_for(self, title, content):
        return [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": JSWebsiteSummarizer.__user_prompt_for(title, content)}]

    def __summarize(self):
        self.website_scrapper.parse()
        chat_config = self.__messages_for(self.website_scrapper.get_title(), self.website_scrapper.get_text())
        response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=chat_config)
        return response.choices[0].message.content

    def display_summary(self):
        summary = self.__summarize()
        if 'ipykernel' in sys.modules:
            from IPython.display import Markdown, display
            display(Markdown(summary))
        else:
            print("=== Website Summary ===\n")
            print(summary)

# Use headless true for non JS/Bot/Secured website to avoid overhead
# Use headless False for JS/Bot/Secured website so as to bypass security

if __name__ == "__main__":
    url1 = "https://cnn.com"
    url2 = "https://openai.com"
    url3 = "https://anthropic.com"

    # web_summariser = JSWebsiteSummarizer(url=url1, headless=True)
    #
    # print("Starting website summary...")
    # web_summariser.display_summary()

    web_summariser = JSWebsiteSummarizer(url=url3, headless=False)
    print("Starting website summary...")
    web_summariser.display_summary()
    print("Done!")