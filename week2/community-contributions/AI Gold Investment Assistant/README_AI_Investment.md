# 🏆 AI Investment Estimations - Gold Assistant

A comprehensive AI assistant for gold investment analysis featuring multiple specialized agents, real-time price data, and multi-language support.

## 🌟 Features

### Multiple AI Agents
- **Gold Price Agent**: Fetches real-time gold prices from MetalpriceAPI
- **Investment Advisor Agent**: Provides timing recommendations based on market conditions
- **Purchase Simulation Agent**: Records fake gold purchases to JSON file
- **Translation Agent**: Translates all responses to Arabic using OpenAI
- **Speech-to-Text Agent**: Converts voice input to text using OpenAI Whisper

### Multi-Panel Interface
- **Left Panel**: English chat with text and voice input
- **Right Panel**: Real-time Arabic translations
- **Bottom Panel**: Feature descriptions and supported currencies

### Supported Countries/Currencies
USA (USD), UK (GBP), Europe (EUR), Japan (JPY), Canada (CAD), Australia (AUD), India (INR), China (CNY), Saudi Arabia (SAR), UAE (AED), Egypt (EGP)

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_ai_investment.txt
```

### 2. Set Up API Keys
Create a `.env` file in the week2 directory with:
```env
OPENAI_API_KEY=your_openai_api_key_here
METAL_PRICE_API_KEY=your_metal_price_api_key_here
```

#### Getting API Keys:
- **OpenAI API Key**: Sign up at [OpenAI](https://platform.openai.com/)
- **Metal Price API Key**: Sign up at [MetalpriceAPI](https://metalpriceapi.com/) (free tier available)

### 3. Run the Assistant
Open `ai_investment_estimations.ipynb` in Jupyter Lab and run all cells.

### 4. Test Your Setup
Run the demo test script first:
```bash
python demo_test.py
```

## 💬 Usage Examples

Try these example queries in the assistant:

### Gold Price Queries
- "What's the current gold price in USA?"
- "Show me gold prices in Saudi Arabia"
- "How much does gold cost in Europe?"

### Investment Advice
- "Should I invest in gold now?"
- "Is it a good time to buy gold?"
- "What's your investment recommendation for gold?"

### Purchase Simulation
- "Buy 2.5 ounces of gold in USD"
- "Purchase 1 ounce of gold in GBP"
- "I want to buy 5 ounces of gold"

### Voice Input
Use the microphone button to speak any of the above queries.

## 🔧 How It Works

### Gold Price Agent
1. Maps country names to currency codes
2. Calls MetalpriceAPI for real-time prices
3. Falls back to demo data if API unavailable
4. Generates investment advice based on price ranges

### Purchase Simulation Agent
1. Gets current gold price
2. Calculates total cost for requested ounces
3. Generates unique transaction ID
4. Saves purchase record to `gold_purchases.json`
5. Returns confirmation with details

### Translation Agent
Uses OpenAI's GPT model to translate responses to Arabic while maintaining meaning and tone.

### Speech-to-Text Agent
Uses OpenAI's Whisper model to convert voice input to text for seamless voice interaction.

## 📊 Purchase Tracking

All simulated purchases are saved to `gold_purchases.json` with:
- Purchase date and time
- Number of ounces
- Price per ounce
- Total cost
- Currency
- Unique transaction ID

Use the `view_purchase_history()` function to see all your transactions.

## 🛠️ File Structure

```
week2/
├── ai_investment_estimations.ipynb  # Main notebook
├── requirements_ai_investment.txt   # Python dependencies
├── demo_test.py                    # Test script
├── README_AI_Investment.md         # This file
├── gold_purchases.json            # Auto-generated purchase history
└── .env                          # Your API keys (create this)
```

## 🎯 Advanced Features

### Investment Logic
The assistant uses intelligent price-based recommendations:
- **USD < $2000**: Excellent buying opportunity
- **USD $2000-2300**: Good time to buy
- **USD $2300-2500**: Fair pricing, consider dollar-cost averaging
- **USD > $2500**: High price zone, consider waiting

### Error Handling
- Graceful API failure handling with demo data
- Speech-to-text error reporting
- Purchase validation and error messages

### Multi-Language Support
- Real-time Arabic translation of all responses
- Right-to-left text display for Arabic
- Maintains context and tone in translations

## 🔍 Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   - Ensure your API key is valid and has credits
   - Check the `.env` file format

2. **Audio Input Not Working**
   - Grant microphone permissions to your browser
   - Ensure you're using HTTPS or localhost

3. **Gold Price API Issues**
   - The system will fall back to demo data
   - Sign up for a free MetalpriceAPI key for real data

4. **Arabic Text Not Displaying**
   - Ensure your browser supports Arabic fonts
   - The text should display right-to-left automatically

### Demo Mode
If you don't have a MetalpriceAPI key, the system will use demo data with realistic prices for testing.

## 🚀 Extending the Assistant

You can easily extend this assistant by:
- Adding more currencies/countries to the mapping
- Implementing more sophisticated investment logic
- Adding historical price analysis
- Integrating with real broker APIs
- Adding more language translations
- Including silver, platinum, and other precious metals

## 📝 License

This project is for educational purposes. Make sure to comply with API terms of service for production use.

---

Created as part of the LLM Engineering course Week 2 project, transforming the airline assistant into a comprehensive investment tool. 