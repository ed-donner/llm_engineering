# ─────────────────────────────────────────
# modules/display.py
# All display/formatting functions
# ─────────────────────────────────────────
import json

# ─────────────────────────────────────────
# Display formatted results
# ─────────────────────────────────────────
def display_results(info):
    """
    Display house info in nice format
    
    Args:
        info (str): Formatted house information
    """
    print("\n")
    print("╔══════════════════════════════════════════════╗")
    print("║         🏠 ZILLOW PROPERTY REPORT             ║")
    print("╚══════════════════════════════════════════════╝")
    print(info)
    print("═" * 46)
    print("║  Powered by RapidAPI Zillow + OpenAI 🤖      ║")
    print("═" * 46)

# ─────────────────────────────────────────
# Display raw JSON data
# ─────────────────────────────────────────
def display_raw_data(data):
    """
    Display raw API data in formatted JSON
    
    Args:
        data (dict): Raw API response data
    """
    print("\n📦 Raw API Data:")
    print(json.dumps(data, indent=2))