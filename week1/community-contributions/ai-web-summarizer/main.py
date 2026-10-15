from summarizer.fetcher import fetch_web_content
from summarizer.summarizer import summarize_text
from utils.logger import logger

def main():
    url = input("Enter a URL to summarize: ")
    
    logger.info(f"Fetching content from: {url}")
    content = fetch_web_content(url)

    if content:
        logger.info("Content fetched successfully. Sending to OpenAI for summarization...")
        # summary = summarize_text(content,'gpt-4o-mini', engine="openai")
        # summary = summarize_text(content, 'deepseek-r1:1.5B', engine="ollama-lib")
        summary = summarize_text(content, 'deepseek-r1:1.5B', engine="ollama-api")


        if summary:
            logger.info("Summary generated successfully.")
            print("\nSummary of the page:\n")
            print(summary)
        else:
            logger.error("Failed to generate summary.")
    else:
        logger.error("Failed to fetch web content.")

if __name__ == "__main__":
    main()
