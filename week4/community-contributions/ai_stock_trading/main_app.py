"""
Main Streamlit Application for AI Stock Trading with Sharia Compliance
"""

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Import our custom tools
from tools.fetching import stock_fetcher, get_available_stocks
from tools.analysis import stock_analyzer
from tools.trading_decisions import trading_engine
from tools.sharia_compliance import sharia_checker
from tools.charting import chart_generator

# Import new modular components
from core.data_service import data_service
from core.ai_assistant import ai_assistant
from components.chat_interface import ChatInterface

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Stock Trading & Sharia Compliance",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

class StockTradingApp:
    def __init__(self):
        self.initialize_session_state()
        self.setup_sidebar()
    
    def initialize_session_state(self):
        if 'selected_country' not in st.session_state:
            st.session_state.selected_country = 'USA'
        if 'selected_stock' not in st.session_state:
            st.session_state.selected_stock = None
        if 'stock_data' not in st.session_state:
            st.session_state.stock_data = {}
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'home'
    
    def setup_sidebar(self):
        with st.sidebar:
            st.title("🏛️ Navigation")
            
            page = st.radio(
                "Select Page:",
                ["🏠 Home", "💬 Chat Interface", "📊 Dashboard"],
                key="page_selector"
            )
            
            page_mapping = {
                "🏠 Home": "home",
                "💬 Chat Interface": "chat", 
                "📊 Dashboard": "dashboard"
            }
            st.session_state.current_page = page_mapping[page]
            
            st.divider()
            self.render_stock_selector()
            st.divider()
            self.show_api_status()
    
    def render_stock_selector(self):
        st.subheader("🌍 Stock Selection")
        
        countries = ['USA', 'Egypt']
        selected_country = st.selectbox(
            "Select Country:",
            countries,
            index=countries.index(st.session_state.selected_country),
            key="country_selector"
        )
        
        if selected_country != st.session_state.selected_country:
            st.session_state.selected_country = selected_country
            st.session_state.selected_stock = None
        
        available_stocks = get_available_stocks(selected_country)
        
        if available_stocks:
            stock_names = list(available_stocks.keys())
            current_index = 0
            
            if st.session_state.selected_stock:
                current_symbol = st.session_state.selected_stock
                for i, (name, symbol) in enumerate(available_stocks.items()):
                    if symbol == current_symbol:
                        current_index = i
                        break
            
            selected_stock_name = st.selectbox(
                "Select Stock:",
                stock_names,
                index=current_index,
                key="stock_selector"
            )
            
            selected_symbol = available_stocks[selected_stock_name]
            
            if selected_symbol != st.session_state.selected_stock:
                st.session_state.selected_stock = selected_symbol
                st.session_state.stock_data = {}
                st.session_state.chat_history = []
            
            if st.session_state.selected_stock:
                st.success(f"Selected: {selected_stock_name} ({selected_symbol})")
        else:
            st.error(f"No stocks available for {selected_country}")
    
    def show_api_status(self):
        st.subheader("API Used")
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            st.success("✅ OpenAI Connected")
        else:
            st.error("❌ Not Connected")
    
    def run(self):
        st.title("🤖 AI Stock Trading")
        st.markdown("*Intelligent stock analysis with Islamic finance compliance*")
        
        if st.session_state.current_page == 'home':
            self.render_home_page()
        elif st.session_state.current_page == 'chat':
            self.render_chat_page()
        elif st.session_state.current_page == 'dashboard':
            self.render_dashboard_page()
    
    def render_home_page(self):
        st.header("🏠 Welcome to AI Stock Trading Platform")
        
        st.markdown("""        
        Get intelligent stock analysis with Islamic finance compliance checking. 
        Select a country and stock from the sidebar to begin.
        
        **Key Features:**
        - 📊 Real-time stock analysis with advanced indicators
        - 🤖 AI-powered trading recommendations  
        - ☪️ Sharia compliance assessment
        - 💬 Natural language chat interface
        
        **Supported Markets:** 🇺🇸 USA | 🇪🇬 Egypt
        
        *Disclaimer: For educational purposes only. Not financial advice.*
        """)
        
        if st.session_state.selected_stock:
            st.divider()
            st.subheader(f"📊 Quick Analysis: {st.session_state.selected_stock}")
            with st.spinner("Loading quick analysis..."):
                self.show_quick_analysis()
    
    def show_quick_analysis(self):
        symbol = st.session_state.selected_stock
        country = st.session_state.selected_country
        try:
            data = stock_fetcher.fetch_stock_data(symbol, period="1mo")
            stock_info = stock_fetcher.get_stock_info(symbol, country)
            
            if not data.empty:
                col1, col2, col3, col4 = st.columns(4)
                
                current_price = data['Close'].iloc[-1]
                price_change = data['Close'].iloc[-1] - data['Close'].iloc[-2] if len(data) > 1 else 0
                price_change_pct = (price_change / data['Close'].iloc[-2] * 100) if len(data) > 1 else 0
                
                with col1:
                    formatted_price = stock_fetcher.format_price_with_currency(current_price, country)
                    price_change_str = f"{price_change:+.2f} ({price_change_pct:+.1f}%)"
                    st.metric("Current Price", formatted_price, price_change_str)
                
                with col2:
                    high_52w = stock_info.get('fifty_two_week_high', 0)
                    formatted_high = stock_fetcher.format_price_with_currency(high_52w, country)
                    st.metric("52W High", formatted_high)
                
                with col3:
                    low_52w = stock_info.get('fifty_two_week_low', 0)
                    formatted_low = stock_fetcher.format_price_with_currency(low_52w, country)
                    st.metric("52W Low", formatted_low)
                
                with col4:
                    market_cap = stock_info.get('market_cap', 0)
                    currency = stock_fetcher.get_market_currency(country)
                    if market_cap > 1e9:
                        if currency == 'EGP':
                            market_cap_str = f"{market_cap/1e9:.1f}B EGP"
                        else:
                            market_cap_str = f"${market_cap/1e9:.1f}B"
                    elif market_cap > 1e6:
                        if currency == 'EGP':
                            market_cap_str = f"{market_cap/1e6:.1f}M EGP"
                        else:
                            market_cap_str = f"${market_cap/1e6:.1f}M"
                    else:
                        if currency == 'EGP':
                            market_cap_str = f"{market_cap:,.0f} EGP"
                        else:
                            market_cap_str = f"${market_cap:,.0f}"
                    st.metric("Market Cap", market_cap_str)
                
                st.info(f"**{stock_info.get('company_name', 'N/A')}** | "
                       f"Sector: {stock_info.get('sector', 'N/A')} | "
                       f"Industry: {stock_info.get('industry', 'N/A')}")
        
        except Exception as e:
            st.error(f"Error loading quick analysis: {str(e)}")
    
    def load_stock_analysis(self, symbol: str):
        """Load complete analysis using data service"""
        country = st.session_state.selected_country
        # Pre-load all analysis components
        data_service.get_analysis(symbol)
        data_service.get_trading_recommendation(symbol, country)
        data_service.get_sharia_compliance(symbol, country)
    
    def render_chat_page(self):
        st.header("💬 AI Stock Analysis Chat")
        
        symbol = st.session_state.selected_stock
        country = st.session_state.selected_country
        
        ChatInterface.render(symbol, country)
    
    def render_dashboard_page(self):
        st.header("📊 Dashboard")
        
        if not st.session_state.selected_stock:
            st.warning("⚠️ Please select a stock from the sidebar.")
            return
        
        symbol = st.session_state.selected_stock
        country = st.session_state.selected_country
        
        # Load data using new data service
        with st.spinner("Loading dashboard data..."):
            basic_info = data_service.get_basic_info(symbol, country)
            data = data_service.get_price_data(symbol, "1y")
            analysis = data_service.get_analysis(symbol, "1y")
            trading_decision = data_service.get_trading_recommendation(symbol, country)
            sharia_compliance = data_service.get_sharia_compliance(symbol, country)
        
        # Check if data loaded successfully
        if data is None or analysis.get('error') or trading_decision.get('error'):
            st.error("Failed to load dashboard data. Please try again.")
            return
        
        # KPIs at the top
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if data is not None and hasattr(data, 'iloc') and len(data) > 0:
                current_price = data['Close'].iloc[-1]
                formatted_price = stock_fetcher.format_price_with_currency(current_price, country)
                st.metric("💰 Current Price", formatted_price)
            else:
                st.metric("💰 Current Price", "N/A")
        
        with col2:
            total_return = analysis.get('total_return_pct', 0)
            st.metric("Total Return", f"{total_return:.2f}%")
        
        with col3:
            rec = trading_decision.get('recommendation', 'HOLD')
            conf = trading_decision.get('confidence', 0.5)
            if conf <= 1.0:
                conf_pct = conf * 100
            else:
                conf_pct = conf
            st.metric("Recommendation", rec, f"{conf_pct:.0f}% confidence")
        
        with col4:
            ruling = sharia_compliance.get('ruling', 'UNCERTAIN')
            sharia_conf = sharia_compliance.get('confidence', 0.5)
            if sharia_conf <= 1.0:
                sharia_conf_pct = sharia_conf * 100
            else:
                sharia_conf_pct = sharia_conf
            st.metric("Sharia Status", ruling, f"{sharia_conf_pct:.0f}% confidence")
        
        with col5:
            volatility = analysis.get('volatility_annualized', 0)
            st.metric("Volatility", f"{volatility:.1f}%")
        
        
        # Charts section (only if data is available)
        if data is not None and hasattr(data, 'iloc') and len(data) > 0:
            st.divider()
            
            # First row: Risk Analysis and Trading Signals
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    risk_fig = chart_generator.create_risk_analysis_chart(analysis, symbol)
                    st.plotly_chart(risk_fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Risk chart error: {str(e)}")
            
            with col2:
                try:
                    signals_fig = chart_generator.create_trading_signals_chart(data, analysis, trading_decision, symbol)
                    st.plotly_chart(signals_fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Signals chart error: {str(e)}")
            
            # Second row: Price Chart (full width)
            try:
                price_fig = chart_generator.create_price_chart(data, symbol, analysis)
                st.plotly_chart(price_fig, use_container_width=True)
            except Exception as e:
                st.error(f"Price chart error: {str(e)}")
        else:
            st.warning("📊 Charts unavailable - no price data loaded.")
    


def main():
    app = StockTradingApp()
    app.run()

if __name__ == "__main__":
    main()
