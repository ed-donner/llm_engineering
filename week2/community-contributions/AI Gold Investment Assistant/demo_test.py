#!/usr/bin/env python3
"""
Demo test script for AI Investment Estimations assistant
Test individual components before running the full Gradio interface
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test if OpenAI API key is set
openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    print(f"✅ OpenAI API Key exists and begins with: {openai_api_key[:8]}")
else:
    print("❌ OpenAI API Key not set - add OPENAI_API_KEY to your .env file")

# Test if Metal Price API key is set (optional)
metal_api_key = os.getenv('METAL_PRICE_API_KEY')
if metal_api_key and metal_api_key != 'demo':
    print(f"✅ Metal Price API Key exists and begins with: {metal_api_key[:8]}")
else:
    print("⚠️  Metal Price API Key not set - using demo mode (sign up at https://metalpriceapi.com/)")

print("\n" + "="*50)
print("Testing Gold Price Functions...")
print("="*50)

# Import the functions from the notebook (you'd need to copy them to a .py file)
# For now, let's test with a simple demo

demo_countries = ['USA', 'UK', 'Saudi Arabia', 'UAE', 'Japan']

for country in demo_countries:
    print(f"\nTesting gold price for: {country}")
    # This would call your get_gold_price function
    print(f"  Currency mapping would convert '{country}' to appropriate currency code")
    print(f"  Would fetch real-time price and provide investment advice")

print("\n" + "="*50)
print("Demo Purchase Simulation...")
print("="*50)

print("Simulating purchase of 2.5 ounces of gold in USD...")
print("This would:")
print("  1. Get current gold price")
print("  2. Calculate total cost")
print("  3. Generate transaction ID")
print("  4. Save to gold_purchases.json file")
print("  5. Return confirmation with details")

print("\n" + "="*50)
print("Next Steps:")
print("="*50)
print("1. Make sure you have all required packages installed:")
print("   pip install -r requirements_ai_investment.txt")
print("2. Set up your .env file with API keys")
print("3. Run the ai_investment_estimations.ipynb notebook")
print("4. Test with example queries like:")
print("   - 'What's the gold price in USA?'")
print("   - 'Should I invest in gold now?'")
print("   - 'Buy 3 ounces of gold'") 