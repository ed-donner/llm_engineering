# ─────────────────────────────────────────
# modules/openai_analyzer.py
# All OpenAI analysis functions
# ─────────────────────────────────────────
import json
import sys
import os

# Fix path issue
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))

from config import client, MODEL_GPT


# ─────────────────────────────────────────
# Extract house info using OpenAI
# ─────────────────────────────────────────
def extract_house_info(property_data):
    """
    Use OpenAI to extract and format house info
    
    Args:
        property_data (dict): Raw property data from API
        
    Returns:
        str: Formatted house information
    """
    print("\n🤖 Sending to OpenAI for analysis...")
    
    data_str = json.dumps(property_data, indent=2)
    
    prompt = f"""
    From the following Zillow property data, 
    please extract and display in this exact format:

    🏠 HOUSE DETAILS
    ================
    📍 Address      : [full address]
    💰 Price        : [current price]
    🛏️  Bedrooms     : [number]
    🚿 Bathrooms    : [number]
    📐 Square Feet  : [square footage]
    🏗️  Year Built   : [year]
    🏡 Property Type : [type]
    
    📈 SELLING HISTORY
    ==================
    [Date] : [Price]
    (list all available history)
    
    💰 TAX HISTORY
    ==============
    [Year] : [Tax Amount]
    (list all available history)

    📊 ADDITIONAL INFO
    ==================
    📊 Zestimate    : [zestimate value]
    🏘️  HOA Fee      : [hoa fee]
    🅿️  Parking      : [parking info]
    
    If any information is not available, write "Not Available"

    Here is the property data:
    {data_str[:4000]}
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL_GPT,
            messages=[
                {
                    "role": "system",
                    "content": "You are a real estate data extraction expert. "
                               "Extract and present house information clearly."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        return None