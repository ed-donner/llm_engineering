import re
from playwright.sync_api import sync_playwright
import time

def scrape_travelwings_prices(origin: str, destination: str, date: str, cabin_class: str = "Economy", adults: int = 1) -> str:
    """
    Scrapes the Travelwings site for an exact flight route. 
    Returns the extracted text focusing on common currency symbols (NGN, $, €, £).
    
    origin: e.g. 'ABV'
    destination: e.g. 'LOS'
    date: 'YYYY-MM-DD'
    cabin_class: 'Economy', 'PremiumEconomy', 'Business', 'FirstClass'
    adults: int, usually 1
    """
    
    # Build the specialized URL
    url = f"https://www.travelwings.com/ng/en/flight-search/oneway/{origin}-{destination}/{date}/{cabin_class}/{adults}Adult"
    
    try:
        with sync_playwright() as p:
            # Launch the browser in headless mode
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Go to the url and wait until there are no more than 2 network connections for at least 500ms
            # This ensures heavy JS on the travelwings page has finished loading flight results.
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # We can optionally add an explicit wait for an element that indicates prices are loaded, 
            # like a flight card. But networkidle is usually sufficient.
            page.wait_for_timeout(5000) # Give an extra 5 seconds just to be safe for React rendering
            
            # Extract all readable text from the body
            # We'll use JavaScript's innerText to get the structured text as you would read it on the screen
            text = page.evaluate("() => document.body.innerText")
            
            browser.close()
            
            # Split lines and filter out empty ones
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            currency_symbols = ['$', '€', '£', '₦', 'USD', 'EUR', 'GBP', 'NGN']
            relevant_lines = []
            
            # We'll include 2 lines before and 2 lines after any matching currency symbol 
            # or any line mentioning the airline itself.
            for i, line in enumerate(lines):
                if any(sym in line for sym in currency_symbols) or "Air Peace" in line or "Airline" in line or "Economy" in line or "Business" in line:
                    start_idx = max(0, i - 3)
                    end_idx = min(len(lines), i + 4)
                    context_chunk = " | ".join(lines[start_idx:end_idx])
                    
                    if context_chunk not in relevant_lines:
                        relevant_lines.append(context_chunk)
            
            # If our strict filter missed it (maybe structure is weird), just dump the first few thousand characters
            if not relevant_lines:
                 # fallback to raw dump of the whole text body if filters were too strict
                 return f"Raw scraped text from Travelwings:\\n{text[:10000]}"
            
            return f"Here is the scraped pricing information from {url}:\\n\\n" + "\\n".join(relevant_lines)
            
    except Exception as e:
        return f"An error occurred while fetching Travelwings: {str(e)}"

if __name__ == "__main__":
    # Test example using the user's url
    print("Testing Travelwings Scraper...")
    sample_result = scrape_travelwings_prices("ABV", "LOS", "2026-03-03", "Economy", 1)
    print(sample_result)
