# 💰 LLM-Powered Financial Asset Comparison Agent

A Jupyter notebook that uses yfinance to download financial data and OpenAI's GPT-4o-mini to analyze and compare asset classes (Bitcoin, S&P 500, and Gold) over a 3-year period.

**Author:** [Febryan](https://www.linkedin.com/in/febryanmughni/)  
**Project Type:** Financial Analysis with LLM

---

## 📊 Features

- **Data Collection**: Automatically downloads 3 years of historical data for:
  - Bitcoin (BTC-USD)
  - S&P 500 (^GSPC)
  - Gold Futures (GC=F)

- **Statistical Analysis**: Calculates key metrics:
  - Total returns
  - Price ranges (high/low)
  - Volatility
  - Start and end prices

- **LLM Analysis**: Uses GPT-4o-mini to provide:
  - Performance comparisons
  - Risk and volatility assessment
  - Investment recommendations
  - Market trend insights

---

## 🚀 How to Run

### 1. Install Dependencies

```bash
pip install yfinance pandas openai python-dotenv ipykernel beautifulsoup4 requests
```

### 2. Setup Environment Variables

Create a `.env` file in your project root with:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the Notebook

1. Open `day1_ClassAssets_Project.ipynb` in Jupyter Lab/Notebook
2. Run all cells in order (Shift+Enter)
3. The LLM will analyze the data and display formatted results

---

## 📁 Project Structure

```
fbrynmghni/
├── README.md                      # This file
├── day1_ClassAssets_Project.ipynb # Main notebook
```

---

## 🔍 What the Notebook Does

### Step-by-Step Process:

1. **Data Collection**: Downloads financial data using yfinance
2. **Statistical Analysis**: Calculates returns, volatility, and price metrics
3. **Data Formatting**: Creates a summary string for the LLM
4. **LLM Setup**: Initializes OpenAI client
5. **Prompt Engineering**: Creates system and user prompts for financial analysis
6. **API Call**: Sends data to GPT-4o-mini for analysis
7. **Results Display**: Shows formatted markdown output with insights

---

## 📈 Sample Output

The LLM provides:
- **Performance Comparison**: Which asset performed best
- **Risk Analysis**: Volatility and risk assessment for each asset
- **Investment Recommendations**: Tailored advice for different risk tolerances
- **Market Insights**: Trends and context over the 3-year period

---

## 🛠️ Extensions & Ideas

- Add more asset classes (bonds, real estate, commodities)
- Calculate Sharpe ratios and other advanced metrics
- Create visualizations (charts, graphs)
- Build a Streamlit/Gradio web app
- Add historical correlation analysis
- Implement portfolio optimization suggestions
- Compare different time periods

---

## 📝 Notes

- Uses `gpt-4o-mini` for faster and more economical analysis
- Data is fetched from Yahoo Finance via yfinance
- All prompts and analysis are in English
- Results are formatted in Markdown for readability

---

## 🙏 Credits

Built as part of the LLM Engineering course. Thanks to Ed Donner and the community for inspiration and learning resources!
