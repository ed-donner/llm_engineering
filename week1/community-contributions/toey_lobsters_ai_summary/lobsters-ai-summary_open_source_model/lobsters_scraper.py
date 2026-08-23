from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

# Define base URL and specific endpoints for scraping
BASE_URL = "https://lobste.rs"
ACTIVE_URL = "https://lobste.rs/active"
COMMENTS_URL = "https://lobste.rs/comments"


def scrape_active_links(page):
    """
    Function to scrape data from the 'Active' page.
    Stores: number, title, and full link.
    """

    # Initialize a list to hold the scraped data
    active_data = []

    # Navigate to the Active page and wait until the DOM is loaded
    page.goto(ACTIVE_URL, wait_until="domcontentloaded")

    # Locate all link elements with class 'u-url'
    links = page.locator("a.u-url")
    count = links.count()

    # Loop through all found links
    for i in range(count):
        link_element = links.nth(i)

        # Extract the visible text (title) and the href attribute
        title = link_element.inner_text().strip()
        href = link_element.get_attribute("href")
        
        # Combine base URL with relative path to get the full absolute URL
        full_link = urljoin(BASE_URL, href)

        # Append the structured data to the list
        active_data.append({
            "number": i + 1,
            "title": title,
            "link": full_link
        })

    return active_data

def scrape_latest_comments(page):
    """
    Extracts data from the Comments page.
    Stores: number, title, and comment text.
    """

    # Initialize an empty list to store the scraped comment dictionaries
    comments_data = []

    # Navigate to the target URL and wait for the DOM content to be fully loaded
    page.goto(COMMENTS_URL, wait_until="domcontentloaded")

    # Locate all elements with the 'comment' class and count them
    comments = page.locator("div.comment")
    count = comments.count()

    # Print the total number of comments found to the console for debugging
    print(f"Found comments: {count}")

    # Iterate through each comment element found on the page
    for i in range(count):
        # Select the specific comment element at the current index
        comment_element = comments.nth(i)

        # Locate the story title link using a CSS selector and get its inner text
        title = comment_element.locator(".details a[href^='/s/']").last.inner_text().strip()
        
        # Locate the comment content area and extract its text
        comment_text = comment_element.locator(".comment_text").inner_text().strip()

        # Append the extracted data to the list as a dictionary
        comments_data.append({
            "number": i + 1,
            "title": title,
            "comment": comment_text
        })

    # Return the completed list of comment data
    return comments_data
def scrape_lobsters():
    """
    Main execution function.
    Launches the browser once and orchestrates scraping from both pages.
    """

    # Start the Playwright context
    with sync_playwright() as p:
        # Launch Chromium browser with slow motion enabled for visualization
        browser = p.chromium.launch(
            headless=True,
            slow_mo=20
        )

        # Create a new browser page (tab)
        page = browser.new_page()

        # Execute scraping functions
        active_data = scrape_active_links(page)
        comments_data = scrape_latest_comments(page)

        # Close the browser instance
        browser.close()

    # Return the collected data from both sources
    return active_data, comments_data