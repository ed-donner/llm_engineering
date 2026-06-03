# 📈 AI Stock Trading & Sharia Compliance Platform

A comprehensive **Streamlit-based** web application that provides AI-powered stock analysis with Islamic Sharia compliance assessment. This professional-grade platform combines real-time financial data from USA and Egyptian markets, advanced technical analysis, and institutional-quality AI-driven insights to help users make informed investment decisions while adhering to Islamic finance principles.

## 📸 Application Screenshots

### Home View
![Home View](screenshots/home.png)
*Main application interface with market selection and stock input*

### Chat Interface
![Chat Interface](screenshots/chat.png)
*Interactive chat for trading advice, Sharia compliance, and stock analysis*

### Dashboard View
![Dashboard View](screenshots/dashboard.png)
*Comprehensive dashboard with KPIs, charts, and real-time metrics*

## 🎯 Key Features

### 📊 **Comprehensive Stock Analysis**
- Real-time data fetching from multiple markets (USA, Egypt)
- Advanced technical indicators (RSI, MACD, Bollinger Bands, Moving Averages)
- Risk assessment and volatility analysis
- Performance metrics across multiple time periods

### 🤖 **AI-Powered Trading Decisions**
- GPT-4 powered investment recommendations
- Buy/Hold/Sell signals with confidence scores
- Price targets and stop-loss suggestions
- Algorithmic + AI combined decision making

### ☪️ **Sharia Compliance Checking**
- Islamic finance principles assessment
- Halal/Haram rulings with detailed reasoning
- Business activity and financial ratio screening
- Alternative investment suggestions

### 💬 **Natural Language Interface**
- Interactive chat interface for stock discussions
- Ask questions in plain English
- Context-aware responses about selected stocks
- Quick action buttons for common queries

### 📈 **Interactive Dashboards**
- Comprehensive metrics dashboard
- Multiple chart types (Price, Performance, Risk, Trading Signals)
- Real-time data visualization with Plotly
- Exportable analysis reports
- Real-time price charts with volume data
- Professional matplotlib-based visualizations
- Price statistics and performance metrics
- Responsive chart interface

### 🖥️ **Professional Interface**
- Clean, modern Streamlit web interface
- Multi-market support (USA & Egyptian stocks)
- Interactive chat interface with context awareness
- Real-time KPI dashboard with currency formatting
- Quick action buttons for common analysis tasks

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

3. **Set up environment variables**
Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=your-api-key-here
```

### Running the Application

1. **Launch the Streamlit app**
```bash
streamlit run main_app.py
```

2. **Access the web interface** at `http://localhost:8501`

3. **Select your market** (USA or Egypt) from the sidebar

4. **Enter a stock symbol** and start analyzing!

## 📖 How to Use

1. **Select Market**: Choose between USA or Egypt from the sidebar
2. **Enter Stock Symbol**: Input a ticker (e.g., AAPL for USA, ABUK.CA for Egypt)
3. **View Dashboard**: See real-time KPIs, price charts, and key metrics
4. **Use Chat Interface**: Ask questions or request specific analysis:
   - "Give me trading advice for AAPL"
   - "Is this stock Sharia compliant?"
   - "What's the price target?"
5. **Review Professional Analysis**:
   - **Trading Recommendations**: Institutional-grade BUY/HOLD/SELL advice
   - **Sharia Compliance**: Comprehensive Islamic finance screening
   - **Technical Analysis**: Advanced indicators and risk assessment

### Example Tickers to Try

#### USA Market
| Ticker | Company | Sector | Expected Sharia Status |
|--------|---------|--------|-----------------------|
| **AAPL** | Apple Inc. | Technology | ✅ Likely Halal |
| **MSFT** | Microsoft Corp. | Technology | ✅ Likely Halal |
| **GOOGL** | Alphabet Inc. | Technology | ✅ Likely Halal |
| **JNJ** | Johnson & Johnson | Healthcare | ✅ Likely Halal |
| **BAC** | Bank of America | Banking | ❌ Likely Haram |
| **JPM** | JPMorgan Chase | Banking | ❌ Likely Haram |

#### Egypt Market
| Ticker | Company | Sector | Expected Sharia Status |
|--------|---------|--------|-----------------------|
| **ABUK.CA** | Abu Qir Fertilizers | Industrial | ✅ Likely Halal |
| **ETEL.CA** | Egyptian Telecom | Telecom | ✅ Likely Halal |
| **HRHO.CA** | Hassan Allam Holding | Construction | ✅ Likely Halal |
| **CIB.CA** | Commercial Intl Bank | Banking | ❌ Likely Haram |

## 🔧 Technical Implementation

### Modular Architecture

The platform is built with a clean, modular architecture using separate tool modules:

#### 1. **Stock Fetching Module** (`tools/fetching.py`)
- **Multi-Market Support**: USA (75+ stocks) and Egypt (50+ stocks) with proper currency handling
- **Real-Time Data**: Uses yfinance API with robust error handling
- **Currency Formatting**: Automatic USD/EGP formatting based on market
- **Stock Info Enrichment**: Company details, market cap, sector classification

#### 2. **Technical Analysis Module** (`tools/analysis.py`)
- **Advanced Indicators**: RSI, MACD, Bollinger Bands, Moving Averages
- **Risk Metrics**: Volatility analysis, Sharpe ratio, maximum drawdown
- **Performance Analysis**: Multi-timeframe returns and trend analysis
- **Professional Calculations**: Annualized metrics and statistical analysis

#### 3. **Trading Decisions Module** (`tools/trading_decisions.py`)
- **Institutional-Grade AI**: Senior analyst persona with 15+ years experience
- **Professional Standards**: BUY/HOLD/SELL with confidence, price targets, stop-loss
- **Risk Management**: Risk-reward ratios, time horizons, risk assessment
- **Robust JSON Parsing**: Handles malformed AI responses with fallback logic

#### 4. **Sharia Compliance Module** (`tools/sharia_compliance.py`)
- **Comprehensive Screening**: Business activities, financial ratios, trading practices
- **AAOIFI Standards**: Debt-to-assets < 33%, interest income < 5%
- **Prohibited Activities**: 50+ categories including banking, gambling, alcohol
- **User-Triggered Analysis**: Only shows when specifically requested

#### 5. **Charting Module** (`tools/charting.py`)
- **Professional Visualizations**: Plotly-based interactive charts
- **Multiple Chart Types**: Price, volume, technical indicators
- **Responsive Design**: Mobile-friendly chart rendering
- **Export Capabilities**: PNG/HTML export functionality

#### 6. **Main Application** (`main_app.py`)
- **Streamlit Interface**: Modern, responsive web application
- **Chat Integration**: Context-aware conversational interface
- **Real-Time KPIs**: Live dashboard with key metrics
- **Session Management**: Persistent data across user interactions

### AI Integration

The platform leverages OpenAI's GPT-4o-mini with specialized prompts:

#### Trading Analysis Prompts
- **Senior Analyst Persona**: 15+ years institutional experience
- **Professional Standards**: Risk-reward ratios, logical price targets
- **Structured Output**: JSON format with validation and error handling
- **Technical Focus**: Based on RSI, MACD, trend analysis, volume patterns

#### Sharia Compliance Prompts
- **Islamic Scholar Approach**: Follows AAOIFI and DSN standards
- **Comprehensive Screening**: Business activities, financial ratios, trading practices
- **Scholarly Reasoning**: Detailed justification with Islamic finance principles
- **Confidence Scoring**: Quantified certainty levels for rulings

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

### 🔮 Future Work: MCP Integration

We plan to implement a **Model Context Protocol (MCP) layer** to make all trading tools accessible as standardized MCP tools:

#### Planned MCP Tools:
- **`stock_fetcher`** - Real-time market data retrieval for USA/Egypt markets
- **`technical_analyzer`** - Advanced technical analysis with 20+ indicators
- **`sharia_checker`** - Islamic finance compliance screening
- **`trading_advisor`** - AI-powered institutional-grade recommendations
- **`risk_assessor`** - Portfolio risk analysis and management
- **`chart_generator`** - Professional financial visualizations

#### Benefits of MCP Integration:
- **Standardized Interface**: Consistent tool access across different AI systems
- **Interoperability**: Easy integration with other MCP-compatible platforms
- **Scalability**: Modular architecture for adding new financial tools
- **Reusability**: Tools can be used independently or combined
- **Professional Integration**: Compatible with institutional trading platforms

This will enable the platform to serve as a comprehensive financial analysis toolkit that can be integrated into various AI-powered trading systems and workflows.

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