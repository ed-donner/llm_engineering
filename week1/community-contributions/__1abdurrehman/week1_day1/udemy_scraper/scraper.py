

import asyncio
import json
import argparse
from playwright.async_api import async_playwright


async def scrape(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"
        )

        print(f"Loading: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)

        # Scroll to trigger lazy loading
        for _ in range(5):
            await page.keyboard.press("End")
            await page.wait_for_timeout(500)
        await page.keyboard.press("Home")
        await page.wait_for_timeout(1000)

        # Expand all collapsed sections
        print("Expanding sections...")
        while True:
            buttons = await page.query_selector_all("button[aria-expanded='false'].js-panel-toggler")
            if not buttons:
                break
            for btn in buttons:
                await btn.scroll_into_view_if_needed()
                await btn.click()
                await page.wait_for_timeout(200)

        # Course title
        title_el = await page.query_selector("h1")
        course_title = (await title_el.inner_text()).strip() if title_el else "Unknown Course"

        # Scrape sections and lectures
        sections = []
        for section in await page.query_selector_all("._panel_xk1nn_16"):
            # Section heading
            h = await section.query_selector(".ud-accordion-panel-heading")
            if not h:
                continue
            section_title = (await h.inner_text()).strip().split("\n")[0]

            # Lecture titles
            lectures = []
            for li in await section.query_selector_all("li"):
                el = await li.query_selector(".curriculum-section-module-scss-module__9JCrHq__course-lecture-title")
                if el:
                    lectures.append((await el.inner_text()).strip())

            if lectures:
                sections.append({"section": section_title, "lectures": lectures})

        await browser.close()

        result = {"course": course_title, "sections": sections}

        # Print
        print(f"\n📚 {course_title}\n")
        for s in sections:
            print(f"  ▶ {s['section']}")
            for lec in s["lectures"]:
                print(f"      - {lec}")

        # Save
        with open("udemy_outline.json", "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\nSaved to udemy_outline.json")

