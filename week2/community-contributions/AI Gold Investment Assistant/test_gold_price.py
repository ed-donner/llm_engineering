import os
import json
import requests
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Free API key for gold prices
GOLD_API_KEY = os.getenv('METAL_PRICE_API_KEY', 'demo')
GOLD_API_URL = 'https://api.metalpriceapi.com/v1/latest'

def get_gold_price(country='USD'):
    """Get current gold price for a specific country/currency"""
    print(f'Tool get_gold_price called for {country}')
    
    # Currency mapping for different countries
    currency_map = {
        'usa': 'USD', 'united states': 'USD', 'us': 'USD',
        'uk': 'GBP', 'britain': 'GBP', 'england': 'GBP',
        'europe': 'EUR', 'germany': 'EUR', 'france': 'EUR',
        'japan': 'JPY', 'canada': 'CAD', 'australia': 'AUD',
        'india': 'INR', 'china': 'CNY', 'saudi arabia': 'SAR',
        'uae': 'AED', 'egypt': 'EGP'
    }
    
    currency = currency_map.get(country.lower(), country.upper())
    
    # Demo prices (realistic current gold prices as fallback)
    demo_prices = {
        'USD': 2350.50, 'GBP': 1890.25, 'EUR': 2180.75, 'JPY': 345000.00,
        'CAD': 3200.80, 'AUD': 3580.90, 'INR': 195000.50, 'CNY': 17200.25,
        'SAR': 8800.75, 'AED': 8650.30, 'EGP': 115000.80
    }
    
    price_per_ounce = None
    api_success = False
    
    try:
        # API call to get gold price
        params = {
            'api_key': GOLD_API_KEY,
            'base': 'XAU',  # Gold symbol
            'currencies': currency
        }
        
        response = requests.get(GOLD_API_URL, params=params, timeout=10)
        print(f'API Response Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'API Response Data: {data}')
            
            if 'rates' in data and currency in data['rates']:
                rate = data['rates'][currency]
                if rate > 0:  # Ensure valid rate
                    price_per_ounce = round(rate, 2)  # Rate is already price per ounce
                    api_success = True
                    print(f'Successfully got price from API: {price_per_ounce}')
                else:
                    print(f'Invalid rate from API: {rate}')
            else:
                print(f'Currency {currency} not found in API response')
        else:
            print(f'API request failed with status {response.status_code}: {response.text}')
            
    except Exception as e:
        print(f'Error fetching gold price from API: {e}')
    
    # Use demo data if API failed
    if price_per_ounce is None:
        price_per_ounce = demo_prices.get(currency, 2350.50)
        print(f'Using demo price: {price_per_ounce}')
    
    # Generate enhanced fallback advice
    advice = generate_enhanced_fallback_advice(price_per_ounce, currency)
    
    return {
        'price': price_per_ounce,
        'currency': currency,
        'country': country,
        'advice': advice,
        'timestamp': datetime.datetime.now().isoformat(),
        'data_source': 'API' if api_success else 'Demo'
    }

def generate_enhanced_fallback_advice(price, currency):
    """Enhanced fallback advice with currency-specific considerations"""
    
    # Currency-specific price thresholds (approximate)
    thresholds = {
        'USD': {'low': 2000, 'moderate': 2300, 'high': 2500},
        'EUR': {'low': 1850, 'moderate': 2150, 'high': 2350},
        'GBP': {'low': 1600, 'moderate': 1850, 'high': 2100},
        'JPY': {'low': 300000, 'moderate': 340000, 'high': 380000},
        'CAD': {'low': 2700, 'moderate': 3100, 'high': 3500},
        'AUD': {'low': 3000, 'moderate': 3500, 'high': 4000},
        'INR': {'low': 160000, 'moderate': 190000, 'high': 220000},
        'CNY': {'low': 14000, 'moderate': 16500, 'high': 19000},
        'SAR': {'low': 7500, 'moderate': 8500, 'high': 9500},
        'AED': {'low': 7300, 'moderate': 8300, 'high': 9300},
        'EGP': {'low': 95000, 'moderate': 110000, 'high': 125000}
    }
    
    # Get thresholds for currency or use USD as default
    thresh = thresholds.get(currency, thresholds['USD'])
    
    if price < thresh['low']:
        return f'Excellent buying opportunity! Gold is undervalued at {price} {currency}. Consider accumulating positions while prices are low.'
    elif price < thresh['moderate']:
        return f'Good entry point at {price} {currency}. Moderate pricing with growth potential. Consider dollar-cost averaging for this market.'
    elif price < thresh['high']:
        return f'Fair pricing at {price} {currency}. Market is fairly valued. Consider smaller purchases or wait for pullbacks.'
    else:
        return f'Premium pricing at {price} {currency}. Consider waiting for market corrections or focus on smaller strategic purchases.'

if __name__ == "__main__":
    # Run the test
    print('Testing updated get_gold_price function:')
    test_result = get_gold_price('USA')
    print(json.dumps(test_result, indent=2))

    print('\n' + '='*50)
    print('Testing different currencies:')

    # Test multiple currencies
    test_currencies = ['USA', 'UK', 'EUR', 'JPY', 'Saudi Arabia']
    for currency in test_currencies:
        result = get_gold_price(currency)
        print(f'\n{currency}: {result["price"]} {result["currency"]}')
        advice_text = result["advice"][:100] + '...' if len(result["advice"]) > 100 else result["advice"]
        print(f'Advice: {advice_text}')
        print(f'Data Source: {result.get("data_source", "Unknown")}') 