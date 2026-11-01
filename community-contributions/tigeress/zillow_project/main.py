# ─────────────────────────────────────────
# main.py
# Main program - imports all modules
# ─────────────────────────────────────────

# Import all modules
from modules import (
    fetch_by_url,
    fetch_by_address,
    extract_house_info,
    display_results
)
from modules.display import display_raw_data

# ─────────────────────────────────────────
# Main Program
# ─────────────────────────────────────────
def main():
    print("╔══════════════════════════════════════════════╗")
    print("║       🏠 ZILLOW HOUSE INFO FINDER             ║")
    print("║       Powered by RapidAPI + OpenAI 🤖         ║")
    print("╚══════════════════════════════════════════════╝")
    
    print("\nHow would you like to search?")
    print("1. 🌐 Search by Zillow URL")
    print("2. 📍 Search by Address")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        url = input("\nEnter Zillow URL: ").strip()
        property_data = fetch_by_url(url)
        
    elif choice == "2":
        address = input("\nEnter Address: ").strip()
        property_data = fetch_by_address(address)
        
    else:
        print("❌ Invalid choice!")
        return
    
    if property_data:
        # Show raw data option
        show_raw = input("\n👀 Show raw API data? (y/n): ").strip().lower()
        if show_raw == 'y':
            display_raw_data(property_data)
        
        # Extract and display with OpenAI
        house_info = extract_house_info(property_data)
        
        if house_info:
            display_results(house_info)
    else:
        print("\n⚠️ Could not fetch property data!")
        print("💡 Tips:")
        print("   - Check your RapidAPI key")
        print("   - Check your internet connection")
        print("   - Try a different search")

# ─────────────────────────────────────────
# Run Program
# ─────────────────────────────────────────
if __name__ == "__main__":
    main()