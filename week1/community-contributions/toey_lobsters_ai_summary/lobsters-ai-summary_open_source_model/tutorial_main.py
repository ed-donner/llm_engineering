from lobsters_scraper import scrape_lobsters


def main():
    active_data, comments_data = scrape_lobsters()

    print("\n=== Active Page Data ===")
    for item in active_data:
        print(f"{item['number']}. {item['title']}")
        print(f"   Link: {item['link']}")

    print("\n=== Comments Page Data ===")
    for item in comments_data:
        print(f"{item['number']}. {item['title']}")
        print(f"   Comment: {item['comment'][:300]}")
        print()


if __name__ == "__main__":
    main()