from playwright.sync_api import sync_playwright

def run_tutorial():
    with sync_playwright() as p:
        # 1. Setup: Launch browser (Visible mode)
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        print("--- 1. Opened Browser ---")

        # 2. Navigation: Go to a site
        page.goto("https://playwright.dev/")
        print(f"Current Title: {page.title()}")

        # 3. Finding & Scraping: Get Header text
        header = page.locator("h1").inner_text()
        print(f"Scraped Header: {header}")

        # 4. Interaction: Clicking a link
        page.get_by_role("link", name="Get started").click()
        print("Navigated to: Get Started page")

        # 5. Input: Searching in a search bar
        search_box = page.locator(".DocSearch-Button")
        search_box.click() # Open search modal
        page.locator(".DocSearch-Input").fill("locators")
        page.keyboard.press("Enter")
        print("Performed search for: 'locators'")

        # 6. Advanced Scraping: Get a list of items
        # Let's get the side navigation menu items
        items = page.locator(".menu__list-item-link")
        print(f"Found {items.count()} navigation items:")
        for i in range(min(5, items.count())): # Print first 5
            print(f" - {items.nth(i).inner_text()}")

        # 7. Multi-tab handling
        # Open a new tab
        page2 = browser.new_page()
        page2.goto("https://www.google.com")
        print(f"Opened second tab: {page2.title()}")
        page2.close()

        # 8. Cleanup
        browser.close()
        print("--- Tutorial Finished ---")

if __name__ == "__main__":
    run_tutorial()