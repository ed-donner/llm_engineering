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
        try:
            country = st.session_state.selected_country
            data = stock_fetcher.fetch_stock_data(symbol, period="1y")
            stock_info = stock_fetcher.get_stock_info(symbol, country)
            analysis = stock_analyzer.analyze_stock(data)
            trading_decision = trading_engine.get_trading_recommendation(symbol, analysis, stock_info)
            sharia_compliance = sharia_checker.check_sharia_compliance(symbol, stock_info, analysis)
            
            st.session_state.stock_data[symbol] = {
                'data': data,
                'stock_info': stock_info,
                'analysis': analysis,
                'trading_decision': trading_decision,
                'sharia_compliance': sharia_compliance
            }
        except Exception as e:
            st.error(f"Error loading analysis for {symbol}: {str(e)}")
    
    def render_chat_page(self):
        st.header("💬 AI Stock Analysis Chat")
        
        if not st.session_state.selected_stock:
            st.warning("⚠️ Please select a stock from the sidebar to start chatting.")
            return
        
        symbol = st.session_state.selected_stock
        st.info(f"💬 Chatting about: **{symbol}**")
        
        if symbol not in st.session_state.stock_data:
            with st.spinner("Loading stock data and analysis..."):
                self.load_stock_analysis(symbol)
        
        self.render_chat_interface()
    
    def render_chat_interface(self):
        symbol = st.session_state.selected_stock
        
        if st.session_state.chat_history:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.chat_message("user").write(message['content'])
                else:
                    st.chat_message("assistant").write(message['content'])
        else:
            welcome_msg = f"""
            👋 Hello! I'm your AI stock analysis assistant. I can help you with:
            
            • **Technical Analysis** of {symbol}
            • **Trading Recommendations** (Buy/Hold/Sell)
            • **Sharia Compliance** assessment
            • **Risk Analysis** and market insights
            
            What would you like to know about {symbol}?
            """
            st.chat_message("assistant").write(welcome_msg)
        
        user_input = st.chat_input("Ask me anything about this stock...")
        
        if user_input:
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            
            with st.spinner("Analyzing..."):
                ai_response = self.generate_ai_response(user_input, symbol)
            
            st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
            st.rerun()
        
        st.subheader("🚀 Quick Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 Get Analysis"):
                self.add_analysis_to_chat(symbol)
                st.rerun()
        
        with col2:
            if st.button("💰 Trading Rec"):
                self.add_trading_to_chat(symbol)
                st.rerun()
        
        with col3:
            if st.button("☪️ Sharia Check"):
                self.add_sharia_to_chat(symbol)
                st.rerun()
        
        with col4:
            if st.button("🎯 Price Target"):
                self.add_target_to_chat(symbol)
                st.rerun()
    
    def generate_ai_response(self, user_input: str, symbol: str) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Check if user is asking about Sharia compliance
            sharia_keywords = ['sharia', 'halal', 'haram', 'islamic', 'muslim', 'compliant', 'permissible', 'forbidden']
            is_sharia_query = any(keyword in user_input.lower() for keyword in sharia_keywords)
            
            stock_data = st.session_state.stock_data.get(symbol, {})
            analysis = stock_data.get('analysis', {})
            trading_decision = stock_data.get('trading_decision', {})
            stock_info = stock_data.get('stock_info', {})
            country = st.session_state.selected_country
            
            # Format price with proper currency
            current_price = analysis.get('current_price', 0)
            formatted_price = stock_fetcher.format_price_with_currency(current_price, country)
            
            # Base context without Sharia info
            context = f"""
            You are analyzing {symbol} ({stock_info.get('company_name', 'N/A')}).
            
            Current Price: {formatted_price}
            Return: {analysis.get('total_return_pct', 0):.2f}%
            Recommendation: {trading_decision.get('recommendation', 'N/A')}
            Sector: {stock_info.get('sector', 'N/A')}
            
            User Question: {user_input}
            
            Provide helpful analysis based on the available data.
            """
            
            # Add Sharia context only if user asks about it
            if is_sharia_query:
                # Load Sharia compliance if not already loaded
                if symbol not in st.session_state.stock_data or 'sharia_compliance' not in st.session_state.stock_data[symbol]:
                    with st.spinner("Loading Sharia compliance analysis..."):
                        self.load_stock_analysis(symbol)
                
                sharia_compliance = st.session_state.stock_data.get(symbol, {}).get('sharia_compliance', {})
                context += f"""
                
                SHARIA COMPLIANCE ANALYSIS:
                Ruling: {sharia_compliance.get('ruling', 'N/A')}
                Confidence: {sharia_compliance.get('confidence', 0)*100:.0f}%
                Reasoning: {sharia_compliance.get('reasoning', 'N/A')}
                
                Focus your response on Islamic finance principles and Sharia compliance.
                """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a financial advisor and Islamic finance expert."},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=400
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Sorry, I'm having trouble right now. Error: {str(e)}"
    
    def add_analysis_to_chat(self, symbol: str):
        stock_data = st.session_state.stock_data.get(symbol, {})
        analysis = stock_data.get('analysis', {})
        
        if analysis:
            summary = stock_analyzer.get_analysis_summary(analysis)
            st.session_state.chat_history.append({
                'role': 'assistant', 
                'content': f"📊 **Analysis Summary for {symbol}:**\n\n{summary}"
            })
    
    def add_trading_to_chat(self, symbol: str):
        stock_data = st.session_state.stock_data.get(symbol, {})
        trading_decision = stock_data.get('trading_decision', {})
        stock_info = stock_data.get('stock_info', {})
        country = st.session_state.selected_country
        
        if trading_decision:
            rec = trading_decision.get('recommendation', 'HOLD')
            conf = trading_decision.get('confidence', 0)
            
            # Handle confidence as percentage if it's already 0-100, or as decimal if 0-1
            if conf <= 1.0:
                conf_pct = conf * 100
            else:
                conf_pct = conf
            
            reason = trading_decision.get('reasoning', 'No reasoning available')
            price_target = trading_decision.get('price_target')
            stop_loss = trading_decision.get('stop_loss')
            time_horizon = trading_decision.get('time_horizon', 'medium')
            risk_level = trading_decision.get('risk_level', 'medium')
            
            # Clean reasoning - remove JSON artifacts
            if reason.startswith('```json') or reason.startswith('{'):
                # Extract readable content from malformed JSON
                if 'reasoning' in reason:
                    try:
                        import re
                        reasoning_match = re.search(r'"reasoning"\s*:\s*"([^"]+)"', reason)
                        if reasoning_match:
                            reason = reasoning_match.group(1)
                        else:
                            reason = "Technical analysis suggests this recommendation based on current market conditions."
                    except:
                        reason = "Technical analysis suggests this recommendation based on current market conditions."
            
            # Format the message professionally
            message_parts = [
                f"💰 **Trading Recommendation: {rec}**",
                f"📊 **Confidence Level:** {conf_pct:.0f}%",
                f"⏱️ **Time Horizon:** {time_horizon.title()}-term",
                f"⚠️ **Risk Level:** {risk_level.title()}",
                "",
                f"**Analysis:**",
                reason
            ]
            
            # Add price targets if available
            if price_target:
                formatted_target = stock_fetcher.format_price_with_currency(price_target, country)
                message_parts.append(f"🎯 **Price Target:** {formatted_target}")
            
            if stop_loss:
                formatted_stop = stock_fetcher.format_price_with_currency(stop_loss, country)
                message_parts.append(f"🛡️ **Stop Loss:** {formatted_stop}")
            
            message_parts.append("")
            message_parts.append("*This is not financial advice. Please do your own research and consult with a financial advisor.*")
            
            message = "\n".join(message_parts)
            st.session_state.chat_history.append({'role': 'assistant', 'content': message})
    
    def add_sharia_to_chat(self, symbol: str):
        stock_data = st.session_state.stock_data.get(symbol, {})
        sharia_compliance = stock_data.get('sharia_compliance', {})
        
        if sharia_compliance:
            summary = sharia_checker.get_compliance_summary(sharia_compliance)
            st.session_state.chat_history.append({
                'role': 'assistant', 
                'content': f"☪️ **Sharia Compliance:**\n\n{summary}"
            })
    
    def add_target_to_chat(self, symbol: str):
        stock_data = st.session_state.stock_data.get(symbol, {})
        trading_decision = stock_data.get('trading_decision', {})
        analysis = stock_data.get('analysis', {})
        
        current = analysis.get('current_price', 0)
        target = trading_decision.get('price_target')
        stop = trading_decision.get('stop_loss')
        
        message = f"🎯 **Current Price:** ${current:.2f}\n"
        if target:
            upside = ((target - current) / current) * 100
            message += f"**Target:** ${target:.2f} ({upside:+.1f}%)\n"
        if stop:
            downside = ((stop - current) / current) * 100
            message += f"**Stop Loss:** ${stop:.2f} ({downside:+.1f}%)"
        
        st.session_state.chat_history.append({'role': 'assistant', 'content': message})
    
    def render_dashboard_page(self):
        st.header("📊 Dashboard")
        
        if not st.session_state.selected_stock:
            st.warning("⚠️ Please select a stock from the sidebar.")
            return
        
        symbol = st.session_state.selected_stock
        country = st.session_state.selected_country
        
        if symbol not in st.session_state.stock_data:
            with st.spinner("Loading analysis..."):
                self.load_stock_analysis(symbol)
        
        stock_data = st.session_state.stock_data.get(symbol, {})
        if not stock_data:
            st.error("Failed to load data.")
            return
        
        analysis = stock_data.get('analysis', {})
        trading_decision = stock_data.get('trading_decision', {})
        sharia_compliance = stock_data.get('sharia_compliance', {})
        data = stock_data.get('data')
        
        # KPIs at the top
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            current_price = data['Close'].iloc[-1]
            formatted_price = stock_fetcher.format_price_with_currency(current_price, country)
            st.metric("💰 Current Price", formatted_price)
        
        with col2:
            total_return = analysis.get('total_return_pct', 0)
            st.metric("Total Return", f"{total_return:.2f}%")
        
        with col3:
            rec = trading_decision.get('recommendation', 'HOLD')
            conf = trading_decision.get('confidence', 0) * 100
            st.metric("Recommendation", rec, f"{conf:.0f}% confidence")
        
        with col4:
            ruling = sharia_compliance.get('ruling', 'UNCERTAIN')
            sharia_conf = sharia_compliance.get('confidence', 0) * 100
            st.metric("Sharia Status", ruling, f"{sharia_conf:.0f}% confidence")
        
        with col5:
            volatility = analysis.get('volatility_annualized', 0)
            st.metric("Volatility", f"{volatility:.1f}%")
        
        st.divider()
        
        # Charts section
        
        # First row: Risk Analysis and Trading Signals
        col1, col2 = st.columns(2)
        
        with col1:
            risk_fig = chart_generator.create_risk_analysis_chart(analysis, symbol)
            st.plotly_chart(risk_fig, use_container_width=True)
        
        with col2:
            signals_fig = chart_generator.create_trading_signals_chart(data, analysis, trading_decision, symbol)
            st.plotly_chart(signals_fig, use_container_width=True)
        
        # Second row: Price Chart (full width)
        price_fig = chart_generator.create_price_chart(data, symbol, analysis)
        st.plotly_chart(price_fig, use_container_width=True)
    


def main():
    app = StockTradingApp()
    app.run()

if __name__ == "__main__":
    main()
