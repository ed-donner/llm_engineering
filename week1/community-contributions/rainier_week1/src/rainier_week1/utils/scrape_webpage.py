from playwright.sync_api import Page

website = "https://edwarddonner.com"


def get_page(page: Page):
    page.goto(website)
    content = page.content()

    return content


def get_page_body(page: Page):
    page.goto(website)
    cleaned_content = page.locator("body").inner_text()

    return cleaned_content
