"""
Clean, professional chat interface component
"""

import streamlit as st
from core.ai_assistant import ai_assistant
from core.data_service import data_service


class ChatInterface:
    """Professional chat interface for stock analysis"""
    
    @staticmethod
    def render(symbol: str, country: str):
        """Render the chat interface"""
        if not symbol:
            st.warning("⚠️ Please select a stock from the sidebar.")
            return
        
        # Display chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if st.session_state.chat_history:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.chat_message("user").write(message['content'])
                else:
                    st.chat_message("assistant").write(message['content'])
        else:
            # Clean welcome message
            basic_info = data_service.get_basic_info(symbol, country)
            company_name = basic_info.get('company_name', symbol)
            welcome_msg = f"👋 Hello! I'm your AI assistant for **{company_name} ({symbol})**. Ask me anything!"
            st.chat_message("assistant").write(welcome_msg)
        
        # Chat input
        user_input = st.chat_input("Ask about price, trends, analysis, trading recommendations...")
        
        if user_input:
            # Add user message
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            
            # Generate AI response (only loads data if tools are called)
            with st.spinner("Thinking..."):
                ai_response = ai_assistant.generate_response(user_input, symbol, country)
            
            # Add AI response
            st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
            st.rerun()
        
        # Quick actions (collapsed by default)
        ChatInterface._render_quick_actions(symbol, country)
    
    @staticmethod
    def _render_quick_actions(symbol: str, country: str):
        """Render quick action buttons"""
        with st.expander("🚀 Quick Actions", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📈 Price Info", use_container_width=True):
                    ChatInterface._add_price_info(symbol, country)
                    st.rerun()
            
            with col2:
                if st.button("📊 30-Day Analysis", use_container_width=True):
                    ChatInterface._add_medium_term_analysis(symbol)
                    st.rerun()
            
            with col3:
                if st.button("💰 Trading Rec", use_container_width=True):
                    ChatInterface._add_trading_recommendation(symbol, country)
                    st.rerun()
            
            with col4:
                if st.button("☪️ Sharia", use_container_width=True):
                    ChatInterface._add_sharia_compliance(symbol, country)
                    st.rerun()
    
    @staticmethod
    def _add_price_info(symbol: str, country: str):
        """Add current price info to chat"""
        basic_info = data_service.get_basic_info(symbol, country)
        
        current_price = basic_info.get('current_price', 0)
        market_cap = basic_info.get('market_cap', 0)
        sector = basic_info.get('sector', 'N/A')
        
        message = f"""📈 **Current Price Info for {symbol}:**

💰 **Price:** ${current_price:.2f}
🏢 **Market Cap:** ${market_cap:,.0f}
🏭 **Sector:** {sector}"""
        
        st.session_state.chat_history.append({'role': 'assistant', 'content': message})
    
    @staticmethod
    def _add_medium_term_analysis(symbol: str):
        """Add 30-day analysis to chat"""
        analysis = data_service.get_analysis(symbol, "1mo")
        
        if 'error' in analysis:
            message = f"❌ **30-Day Analysis:** {analysis['error']}"
        else:
            return_pct = analysis.get('total_return_pct', 0)
            volatility = analysis.get('volatility_annualized', 0)
            trend = analysis.get('trend_direction', 'neutral')
            
            message = f"""📊 **30-Day Analysis for {symbol}:**

📈 **Return:** {return_pct:.2f}%
📉 **Volatility:** {volatility:.1f}% (annualized)
🎯 **Trend:** {trend.title()}"""
        
        st.session_state.chat_history.append({'role': 'assistant', 'content': message})
    
    @staticmethod
    def _add_trading_recommendation(symbol: str, country: str):
        """Add trading recommendation to chat"""
        trading = data_service.get_trading_recommendation(symbol, country)
        
        if 'error' in trading:
            message = f"❌ **Trading Recommendation:** {trading['error']}"
        else:
            rec = trading.get('recommendation', 'HOLD')
            conf = trading.get('confidence', 0.5) * 100
            reasoning = trading.get('reasoning', 'No reasoning available')
            
            message = f"""💰 **Trading Recommendation for {symbol}:**

🎯 **Action:** {rec}
📊 **Confidence:** {conf:.0f}%
💭 **Reasoning:** {reasoning[:200]}..."""
        
        st.session_state.chat_history.append({'role': 'assistant', 'content': message})
    
    @staticmethod
    def _add_sharia_compliance(symbol: str, country: str):
        """Add Sharia compliance to chat"""
        sharia = data_service.get_sharia_compliance(symbol, country)
        
        if 'error' in sharia:
            message = f"❌ **Sharia Compliance:** {sharia['error']}"
        else:
            ruling = sharia.get('ruling', 'UNCERTAIN')
            conf = sharia.get('confidence', 0.5) * 100
            
            status_emoji = "✅" if ruling == "HALAL" else "❌" if ruling == "HARAM" else "⚠️"
            
            message = f"""☪️ **Sharia Compliance for {symbol}:**

{status_emoji} **Ruling:** {ruling}
📊 **Confidence:** {conf:.0f}%"""
        
        st.session_state.chat_history.append({'role': 'assistant', 'content': message})
