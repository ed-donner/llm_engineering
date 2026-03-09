import requests
from bs4 import BeautifulSoup

class ScannerAgent:
    """
    A simple ScannerAgent that fetches the top titles from Hacker News.
    """
    def __init__(self, count=5):
        self.count = count
        self.url = "https://news.ycombinator.com/"

    def scan(self) -> str:
        """
        Scans Hacker News for the top `count` articles and returns them as a single string.
        """
        print(f"Scanning the internet for top {self.count} tech news articles...")
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            titles = soup.find_all('span', class_='titleline')
            scraped_news = []
            for i, title_span in enumerate(titles[:self.count]):
                link = title_span.find('a')
                if link:
                    article_title = link.text
                    article_url = link.get('href')
                    scraped_news.append(f"{i+1}. {article_title} ({article_url})")
            
            if not scraped_news:
                return "Failed to parse Hacker News titles."
                
            return "Top Tech News:\\n" + "\\n".join(scraped_news)
            
        except requests.RequestException as e:
            return f"Error connecting to Hacker News: {e}"
        except Exception as e:
            return f"An unexpected error occurred during scanning: {e}"

if __name__ == "__main__":
    scanner = ScannerAgent()
    print(scanner.scan())
