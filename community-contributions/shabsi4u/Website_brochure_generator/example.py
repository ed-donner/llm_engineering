#!/usr/bin/env python3
"""
Example usage of the Website Brochure Generator
"""

from website_brochure_generator import create_brochure, stream_brochure, get_links, translate_brochure

def main():
    # Example website URL
    url = "https://example.com"
    
    print("=== Website Brochure Generator Example ===\n")
    
    # Example 1: Get relevant links
    print("1. Analyzing website links...")
    links = get_links(url)
    print(f"Found {len(links['links'])} relevant pages:")
    for link in links['links']:
        print(f"  - {link['type']}: {link['url']}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Create brochure (complete output)
    print("2. Creating brochure (complete output)...")
    brochure = create_brochure(url)
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: Stream brochure (real-time generation)
    print("3. Streaming brochure generation...")
    streamed_brochure = stream_brochure(url)
    
    print("\n" + "="*50 + "\n")
    
    # Example 4: Translate brochure to Spanish (complete output)
    print("4. Translating brochure to Spanish (complete output)...")
    spanish_brochure = translate_brochure(url, "Spanish", stream_mode=False)
    
    print("\n" + "="*50 + "\n")
    
    # Example 5: Translate brochure to French (streaming output)
    print("5. Translating brochure to French (streaming output)...")
    french_brochure = translate_brochure(url, "French", stream_mode=True)
    
    print("\n=== Example Complete ===")

if __name__ == "__main__":
    main()
