from bs4 import BeautifulSoup 
from playwright.async_api import async_playwright

headers = {
    "User-agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/117.0.0.0 Safari/537.36")
}

async def fetch_rendered_html(url):
    "Open a website in a real browswer ,run the javascript and then render the html"

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless = True)
        page = await browser.new_page(
            user_agent = headers['User-agent']
        )
        try:
            await page.goto(
                url, 
                wait_until= "domcontentloaded",
                timeout=60_000,

            )
            #allow dynamically loaded document some time to appear.
            await page.wait_for_timeout(3_000) 
            html = await page.content() 
            return html 

        
        finally:
            await browser.close()

async def fetch_website_contents(url):
     '''Return the title and the visible content of Java-script rendered website"
     Truncate the content to under 2000 characters'''

     html = await fetch_rendered_html(url)
     soup = BeautifulSoup(html, "html.parser")

     title = soup.title.get_text(strip = True) if soup.title else "No title found"

     if soup.body:
        for irrelevant in soup.body(
            ["script", "style", "img", "input", "noscript", "svg"]
        ):
            irrelevant.decompose()
        text = soup.body.get_text(separator = "\n", strip = True)
     else:
        text= ""

     return (title + "\n\n" + text) [:2_000]
        