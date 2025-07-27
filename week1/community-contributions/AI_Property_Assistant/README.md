# AI Property Rental Assistant

A Python tool that scrapes UK property rental listings and uses OpenAI's GPT-4o-mini to provide personalized property recommendations based on your requirements.

## What It Does

- Scrapes property listings from OnTheMarket.com
- Uses AI to analyze properties against your specific needs
- Provides smart recommendations with reasons why properties match
- Works for any UK location (currently configured for Durham)

## Quick Start

### Prerequisites
- Python 3.7+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Install required packages:**
   ```bash
   pip install requests beautifulsoup4 openai python-dotenv ipython
   ```

2. **Set up your API key:**
   
   Create a `.env` file in the same directory as your script:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Run the script:**
   ```bash
   python your_script_name.py
   ```

## How to Use

### Basic Usage

The script is pre-configured to search for student housing in Durham. Just run it and you'll get AI-powered recommendations!

### Customizing Your Search

**Change the location:**
```python
website_url = "https://www.onthemarket.com/to-rent/property/manchester/"
```

**Update your requirements:**
```python
user_needs = "I'm a young professional looking for a 1-bedroom flat in Manchester under £1,000/month"
```

### Example Requirements You Can Use:
- `"Student looking for shared accommodation under £600/month"`
- `"Family needing 3-bedroom house with garden under £1,500/month"`
- `"Professional couple wanting modern 2-bed apartment near city center"`

## Configuration

### Supported Cities
Replace `durham` in the URL with any UK city:
- `london` - London properties
- `manchester` - Manchester properties  
- `birmingham` - Birmingham properties
- `leeds` - Leeds properties
- `bristol` - Bristol properties

### AI Behavior
The system prompt is configured for UK rentals but you can modify it in the `system_prompt` variable to:
- Focus on specific property types
- Emphasize certain features (parking, garden, etc.)
- Target different tenant types (students, families, professionals)

## Example Output

```
Website Title: Properties to rent in Durham - OnTheMarket
Content Length: 15847 characters

==================================================
RENTAL RECOMMENDATIONS:
==================================================

# Property Recommendations for Durham

Based on your requirements for a 2-bedroom student property under £2,000/month, here are my top recommendations:

## 1. **Student House on North Road** - £1,600/month
- **Bedrooms:** 2
- **Perfect because:** Well within budget, popular student area
- **Features:** Close to university, furnished, bills included

## 2. **Modern Apartment City Centre** - £1,400/month  
- **Bedrooms:** 2
- **Perfect because:** Great location, modern amenities
- **Features:** Parking space, balcony, near shops
```

## Requirements

Create a `requirements.txt` file:
```
requests>=2.28.0
beautifulsoup4>=4.11.0
openai>=1.0.0
python-dotenv>=0.19.0
ipython>=8.0.0
```

Install with: `pip install -r requirements.txt`

## Important Notes

### API Costs
- Uses GPT-4o-mini model (very affordable - ~$0.001 per request)
- Monitor usage at: https://platform.openai.com/usage

### Rate Limits
- Free OpenAI accounts: 3 requests per minute
- The script makes 1 request per run

## How It Works

1. **Web Scraping:** Downloads the property listing page
2. **Text Extraction:** Cleans HTML and extracts property information  
3. **AI Analysis:** Sends your requirements + property data to GPT-4
4. **Smart Recommendations:** AI filters and ranks properties with explanations

## Troubleshooting

**"No API key found"**
- Make sure `.env` file exists in the same folder as your script
- Check the API key has no extra spaces
- Verify it starts with `sk-proj-`

**"Error fetching website"**
- Check your internet connection
- Try a different city URL
- Some websites may temporarily block requests

**No good recommendations**
- Try adjusting your budget or requirements
- Check if the website loaded properly (look at content length)
- Try a different city with more properties

## Possible Improvements

- Make it interactive (ask for user input)
- Support multiple property websites
- Add price tracking over time
- Include property images in analysis
- Create a simple web interface

## Disclaimer

This tool is for educational purposes. Always verify property information directly with landlords or estate agents. Respect website terms of service.

---

**Need help?** Check that your `.env` file is set up correctly and you have an active internet connection. The script will tell you if there are any issues with your API key!