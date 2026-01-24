#!/usr/bin/env python3
"""
Google Maps Review Summarizer - Week 1 Day 2
Scrapes REAL reviews from Google Maps and analyzes with Llama 3.2
"""

import asyncio
import ollama
from playwright.async_api import async_playwright


async def scroll_reviews_panel(page, max_scrolls=50, max_reviews=10):
    """Scrolls through the reviews panel to lazy load all reviews."""
    scrollable_div = page.locator('div[role="main"] div[jslog$="mutable:true;"]').first
    previous_review_count = 0
    scroll_attempts = 0
    no_change_count = 0
    
    print("📜 Starting to scroll and load reviews...")
    
    while scroll_attempts < max_scrolls:
        review_elements = page.locator("div[data-review-id][jsaction]")
        current_review_count = await review_elements.count()
        
        if current_review_count >= max_reviews:
            break
        
        print(f"   Scroll attempt {scroll_attempts + 1}: Found {current_review_count} reviews")
        
        await scrollable_div.evaluate("""
            (element) => {
                element.scrollTo(0, element.scrollHeight + 100);
            }
        """)
        
        await asyncio.sleep(2)
        
        if current_review_count == previous_review_count:
            no_change_count += 1
            if no_change_count >= 3:
                print(f"   No new reviews loaded after {no_change_count} attempts. Finished loading.")
                break
        else:
            no_change_count = 0
        
        previous_review_count = current_review_count
        scroll_attempts += 1
    
    final_count = await review_elements.count()
    print(f"✅ Finished scrolling. Total reviews loaded: {final_count}\n")
    return final_count


async def scrape_google_reviews(url, max_reviews=20):
    """Scrape REAL reviews from Google Maps URL."""
    reviews = []
    
    async with async_playwright() as p:
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=False)  # Set to True to hide browser
        context = await browser.new_context()
        page = await context.new_page()
        
        print(f"🔗 Navigating to Google Maps page...")
        await page.goto(url)
        
        print("⏳ Waiting for initial reviews to load...")
        review_html_elements = page.locator("div[data-review-id][jsaction]")
        
        try:
            await review_html_elements.first.wait_for(state="visible", timeout=10000)
        except Exception as e:
            print(f"❌ Could not find reviews: {e}")
            await browser.close()
            return []
        
        # Scroll to load more reviews
        total_reviews = await scroll_reviews_panel(page, max_scrolls=100, max_reviews=max_reviews)
        
        print(f"📥 Starting to scrape {total_reviews} reviews...")
        
        # Get all review elements after scrolling
        review_html_elements = page.locator("div[data-review-id][jsaction]")
        all_reviews = await review_html_elements.all()
        
        # Iterate and scrape each review
        for idx, review_html_element in enumerate(all_reviews, 1):
            try:
                # Extract rating
                stars_element = review_html_element.locator("[aria-label*=\"star\"]")
                
                try:
                    stars_label = await stars_element.get_attribute("aria-label", timeout=3000)
                except:
                    stars_label = None
                
                stars = None
                if stars_label:
                    for i in range(1, 6):
                        if str(i) in stars_label:
                            stars = i
                            break
                
                # Click "More" button if present
                try:
                    more_element = review_html_element.locator("button[aria-label=\"See more\"]").first
                    if await more_element.is_visible(timeout=1000):
                        await more_element.click()
                        await asyncio.sleep(0.3)
                except:
                    pass
                
                # Extract review text
                try:
                    text_element = review_html_element.locator("div[tabindex=\"-1\"][id][lang]")
                    text = await text_element.text_content(timeout=3000)
                except:
                    text = ""
                
                if text and text.strip():
                    reviews.append({
                        'rating': stars,
                        'text': text.strip()
                    })
                
                if idx % 10 == 0:
                    print(f"   Scraped {idx}/{total_reviews} reviews...")
            
            except Exception as e:
                print(f"   Error scraping review {idx}: {str(e)[:50]}")
                continue
        
        print(f"\n✅ Successfully scraped {len(reviews)} reviews!")
        await browser.close()
    
    return reviews


def analyze_reviews(reviews, model="llama3.2"):
    """Analyze REAL reviews using Llama 3.2."""
    
    if not reviews:
        return "No reviews to analyze."
    
    # Prepare reviews text
    reviews_text = "\n\n".join([
        f"Rating: {r['rating']}/5\n{r['text']}" 
        for r in reviews
    ])
    
    reviews_text = reviews_text[:8000]
    
    prompt = f"""Analyze the following REAL Google Maps reviews and provide:

1. **Overall Sentiment**: Positive, Negative, or Mixed
2. **Key Themes**: Main topics mentioned (quality, service, atmosphere, etc.)
3. **Pros**: What customers love (3-5 bullet points)
4. **Cons**: What customers dislike (3-5 bullet points)
5. **Summary**: A 2-3 sentence overall summary based on actual customer feedback

REVIEWS:
{reviews_text}
"""
    
    print("\n🧠 Analyzing reviews with Llama 3.2...")
    print("   (This may take a moment...)\n")
    
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at analyzing customer reviews and extracting insights from REAL user feedback."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response["message"]["content"]
    
    except Exception as e:
        return f"❌ Analysis error: {e}"


async def main():
    """Main function."""
    print("\n" + "="*60)
    print("🗺️  Google Maps Review Summarizer (REAL Reviews)")
    print("    Powered by Llama 3.2 via Ollama")
    print("="*60 + "\n")
    
    print("📖 How it works:")
    print("  1. Scrapes REAL reviews from Google Maps")
    print("  2. Analyzes them with Llama 3.2")
    print("  3. Provides insights based on actual customer feedback\n")
    
    # Get Google Maps URL
    url = input("🔗 Enter Google Maps URL: ").strip()
    
    if not url or "google.com/maps" not in url:
        print("❌ Invalid Google Maps URL.")
        return
    
    # Get number of reviews
    try:
        max_reviews_input = input("\n📊 How many reviews to analyze? (default: 20): ").strip()
        max_reviews = int(max_reviews_input) if max_reviews_input else 20
        max_reviews = min(max_reviews, 50)
    except:
        max_reviews = 20
    
    print(f"\n{'='*60}\n")
    
    # Scrape REAL reviews
    reviews = await scrape_google_reviews(url, max_reviews=max_reviews)
    
    if not reviews:
        print("\n❌ Could not extract reviews.")
        print("\nPossible reasons:")
        print("  • The place has no reviews")
        print("  • Google detected automated access")
        print("  • The URL is incorrect")
        return
    
    # Show sample of REAL reviews
    print(f"\n📝 Sample of REAL Reviews ({min(3, len(reviews))} of {len(reviews)}):")
    print("="*60)
    for i, review in enumerate(reviews[:3], 1):
        rating_stars = "⭐" * (review['rating'] or 0)
        print(f"\n{i}. {rating_stars}")
        print(f"   {review['text'][:150]}...")
    
    print(f"\n{'='*60}\n")
    
    # Analyze REAL reviews
    analysis = analyze_reviews(reviews)
    
    # Display analysis
    print("="*60)
    print("📊 ANALYSIS OF REAL REVIEWS")
    print("="*60 + "\n")
    print(analysis)
    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())
