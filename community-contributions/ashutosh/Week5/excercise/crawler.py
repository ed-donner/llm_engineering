import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
from collections import deque
import re
import time


class DocCrawler:
    def __init__(self, start_url, output_dir):

        self.start_url = self.normalize_url(start_url)

        self.allowed_prefix = self.start_url

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.domain = urlparse(self.start_url).netloc

        self.visited = set()

    def normalize_url(self, url):
        """
        Normalize URLs to avoid duplicate crawling.

        Examples:
        /page
        /page/
        /page#section

        all become:

        /page
        """

        parsed = urlparse(url)

        normalized_path = parsed.path.rstrip("/")

        if not normalized_path:
            normalized_path = "/"

        return parsed._replace(
            path=normalized_path,
            query="",
            fragment=""
        ).geturl()

    def clean_text(self, text):

        text = re.sub(r"\n\s*\n+", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    def url_to_filename(self, url):

        parsed = urlparse(url)

        path = parsed.path.strip("/")

        if not path:
            path = "index"

        filename = path.replace("/", "_")

        filename = re.sub(
            r'[<>:"/\\|?*]',
            "_",
            filename
        )

        return f"{filename}.md"

    def extract_content(self, soup):

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside"
        ]):
            tag.decompose()

        content = (
            soup.find("main")
            or soup.find("article")
            or soup.body
        )

        if not content:
            return None

        text = content.get_text(
            "\n",
            strip=True
        )

        return self.clean_text(text)

    def extract_links(self, soup, current_url):

        links = []

        for a in soup.find_all(
            "a",
            href=True
        ):

            href = a["href"]

            full_url = urljoin(
                current_url,
                href
            )

            full_url = self.normalize_url(
                full_url
            )

            parsed = urlparse(full_url)

            # Same domain only
            if parsed.netloc != self.domain:
                continue

            # Stay within selected docs section
            if not full_url.startswith(
                self.allowed_prefix
            ):
                continue

            links.append(full_url)

        return links

    def save_page(self, url, text):

        filename = self.url_to_filename(url)

        filepath = (
            self.output_dir
            / filename
        )

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(text)

    def crawl(self, max_pages=500):

        queue = deque([
            self.start_url
        ])

        # Tracks URLs already discovered
        seen = {
            self.start_url
        }

        while (
            queue
            and len(self.visited) < max_pages
        ):

            url = queue.popleft()

            print(
                f"[{len(self.visited)+1}] {url}"
            )

            try:

                response = requests.get(
                    url,
                    timeout=30,
                    headers={
                        "User-Agent":
                        "Mozilla/5.0"
                    }
                )

                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(
                    response.text,
                    "html.parser"
                )

                text = self.extract_content(
                    soup
                )

                if text:
                    self.save_page(
                        url,
                        text
                    )

                self.visited.add(url)

                links = self.extract_links(
                    soup,
                    url
                )

                for link in links:

                    if link not in seen:

                        seen.add(link)

                        queue.append(
                            link
                        )

                time.sleep(0.5)

            except Exception as e:

                print(f"ERROR: {url}")
                print(e)

        print(
            f"\nFinished: "
            f"{len(self.visited)} pages "
            f"saved to {self.output_dir}\n"
        )


if __name__ == "__main__":

    base_output = (
        r"community-contributions\ashutosh\Week5\excercise\docs"
    )

    sites = [

        # LangChain
        "https://docs.langchain.com/oss/python/langchain",

        # LlamaIndex
        "https://developers.llamaindex.ai/python/framework",

        # Hugging Face
        "https://huggingface.co/learn/llm-course"
    ]

    for site in sites:

        folder_name = (
            urlparse(site)
            .path.strip("/")
            .replace("/", "_")
        )

        if not folder_name:

            folder_name = (
                urlparse(site)
                .netloc
                .replace(".", "_")
            )

        output_dir = (
            Path(base_output)
            / folder_name
        )

        print("\n" + "=" * 80)
        print(f"Crawling: {site}")
        print("=" * 80)

        crawler = DocCrawler(
            start_url=site,
            output_dir=output_dir
        )

        crawler.crawl(max_pages=300)