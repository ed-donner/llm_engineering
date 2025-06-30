# 📈 Stock Analysis & Sharia Compliance Tool

A comprehensive Gradio-based web application that provides AI-powered stock analysis with Islamic Sharia compliance assessment. This tool combines real-time financial data, technical analysis, and AI-driven insights to help users make informed investment decisions while adhering to Islamic finance principles.

![Stock Analysis Interface](https://img.shields.io/badge/Interface-Gradio-blue)
![AI Powered](https://img.shields.io/badge/AI-OpenAI%20GPT--4o--mini-green)
![Islamic Finance](https://img.shields.io/badge/Islamic-Sharia%20Compliant-gold)

## 🌟 Features

### 📊 **Multi-Period Stock Analysis**
- Fetches historical data for 1 month, 1 year, and 5 years
- Calculates key financial metrics: returns, volatility, volume, price ranges
- Comprehensive technical analysis with statistical insights

### 🤖 **AI-Powered Trade Recommendations**
- Uses OpenAI GPT-4o-mini for intelligent analysis
- Provides clear BUY/HOLD/SELL recommendations
- Numerical justification based on multi-timeframe data
- Considers risk factors and market trends

### ☪️ **Sharia Compliance Assessment**
- Analyzes company business activities for Islamic compliance
- Provides HALAL/HARAM/DOUBTFUL rulings
- Confidence scores (0-100) for each assessment
- Detailed justification based on Islamic finance principles

### 📈 **Interactive Visualizations**
- Real-time price charts with volume data
- Professional matplotlib-based visualizations
- Price statistics and performance metrics
- Responsive chart interface

### 🖥️ **User-Friendly Interface**
- Clean, modern Gradio web interface
- Two-column layout for optimal user experience
- Example stock buttons for quick testing
- Real-time analysis progress tracking

## 🚀 Quick Start

### Prerequisites

Ensure you have Python 3.8+ installed on your system.

### Installation

1. **Clone or download this project**
```bash
git clone <repository-url>
cd ai_stock_trading
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up OpenAI API Key**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or set it in the notebook:
```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
```

### Running the Application

1. **Open the Jupyter notebook**
```bash
jupyter notebook stock_analysis_sharia_compliance.ipynb
```

2. **Run all cells** to initialize the functions

3. **Launch the interface** by running the final cell

4. **Access the web interface** at `http://localhost:7860`

## 📖 How to Use

1. **Enter a stock ticker** (e.g., AAPL, MSFT, GOOGL) in the input field
2. **Click "Analyze Stock"** to start the analysis
3. **Review the results**:
   - **Trade Advice**: AI-generated BUY/HOLD/SELL recommendation
   - **Sharia Assessment**: Islamic compliance ruling with confidence score
   - **Price Chart**: 1-month interactive price and volume chart

### Example Tickers to Try

| Ticker | Company | Expected Sharia Status |
|--------|---------|----------------------|
| **AAPL** | Apple Inc. | ✅ Likely Halal (Technology) |
| **MSFT** | Microsoft Corp. | ✅ Likely Halal (Technology) |
| **JNJ** | Johnson & Johnson | ✅ Likely Halal (Healthcare) |
| **BAC** | Bank of America | ❌ Likely Haram (Banking/Interest) |
| **KO** | Coca-Cola | ⚠️ May be Doubtful |

## 🛠️ Technical Implementation

### Core Components

1. **Data Fetching Tool** (`fetch_history`)
   - Uses yfinance API for real-time stock data
   - Supports multiple time periods and intervals
   - Error handling for invalid tickers

2. **Analysis Tool** (`summarize`)
   - Calculates financial metrics
   - Annualized volatility calculation
   - Price performance analysis

3. **Trade Decision Tool** (`get_trade_advice`)
   - OpenAI GPT-4o-mini integration
   - Multi-period analysis prompts
   - Structured recommendation format

4. **Sharia Compliance Tool** (`assess_sharia`)
   - Company profile extraction
   - Islamic finance criteria evaluation
   - Confidence scoring system

5. **Charting Tool** (`plot_price`)
   - Matplotlib-based visualizations
   - Price and volume charts
   - Professional styling

### AI Prompts

The application uses carefully crafted prompts for:
- **Financial Analysis**: Multi-timeframe technical analysis with numerical justification
- **Sharia Assessment**: Islamic finance principles evaluation with scholarly approach

## 📊 Sample Analysis Output

### Trade Recommendation Example
```
RECOMMENDATION: BUY

Based on the analysis of AAPL:
• 1Y return of +15.2% shows strong performance
• Volatility of 24.3% indicates manageable risk
• Recent 1M return of +5.8% shows positive momentum
• Strong volume indicates healthy trading activity

Key factors supporting BUY decision:
- Consistent positive returns across timeframes
- Volatility within acceptable range for tech stocks
- Strong market position and fundamentals
```

### Sharia Assessment Example
```json
{
  "ruling": "HALAL",
  "confidence": 85,
  "justification": "Apple Inc. primarily operates in technology hardware and software, which are permissible under Islamic law. The company's main revenue sources (iPhone, Mac, services) do not involve prohibited activities such as gambling, alcohol, or interest-based banking."
}
```

## ⚠️ Important Disclaimers

### Financial Disclaimer
- **This tool is for educational purposes only**
- **Not professional financial advice**
- **Past performance does not guarantee future results**
- **Consult qualified financial advisors before making investment decisions**

### Sharia Compliance Disclaimer
- **Consult qualified Islamic scholars for authoritative rulings**
- **AI assessments are preliminary and may have limitations**
- **Consider multiple sources for Sharia compliance verification**
- **Individual scholarly interpretations may vary**

### Technical Limitations
- **Data accuracy depends on yfinance API availability**
- **OpenAI API calls consume credits/tokens**
- **Network connectivity required for real-time data**
- **Analysis speed depends on API response times**

## 🔧 Customization

### Adding New Analysis Periods
```python
periods = ["1mo", "3mo", "6mo", "1y", "2y", "5y"]  # Modify as needed
```

### Modifying Sharia Criteria
```python
# Update the Sharia assessment prompt with additional criteria
prompt = f"""
Additional criteria:
- Debt-to-market cap ratio analysis
- Revenue source breakdown
- ESG factors consideration
"""
```

### Styling the Interface
```python
demo = create_interface()
demo.launch(theme="huggingface")  # Try different themes
```

## 📚 Dependencies

- **yfinance**: Real-time financial data
- **openai**: AI-powered analysis
- **pandas**: Data manipulation
- **matplotlib**: Chart generation
- **gradio**: Web interface
- **requests**: HTTP requests
- **beautifulsoup4**: Web scraping
- **numpy**: Numerical computations

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Areas for Enhancement
- Additional technical indicators
- More sophisticated Sharia screening
- Portfolio analysis features
- Historical backtesting
- Mobile-responsive design

## 📄 License

This project is for educational purposes. Please ensure compliance with:
- OpenAI API usage terms
- Yahoo Finance data usage policies
- Local financial regulations
- Islamic finance guidelines

## 🙏 Acknowledgments

- **yfinance** for providing free financial data API
- **OpenAI** for GPT-4o-mini language model
- **Gradio** for the intuitive web interface framework
- **Islamic finance scholars** for Sharia compliance frameworks

---

**Made with ❤️ for the Muslim tech community and ethical investing enthusiasts**

*"And Allah knows best" - وَاللَّهُ أَعْلَمُ* 