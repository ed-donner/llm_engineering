import streamlit as st
from typing import Dict, Any, Optional
from tools.fetching import stock_fetcher
from tools.analysis import stock_analyzer
from tools.trading_decisions import trading_engine
from tools.sharia_compliance import sharia_checker


class DataService:
    """Centralized data service for efficient stock data management"""
    
    @staticmethod
    def get_basic_info(symbol: str, country: str) -> Dict[str, Any]:
        """Get only basic stock info - no heavy analysis"""
        cache_key = f"{symbol}_basic"
        
        if cache_key not in st.session_state:
            try:
                stock_info = stock_fetcher.get_stock_info(symbol, country)
                st.session_state[cache_key] = stock_info
            except Exception as e:
                st.session_state[cache_key] = {
                    'company_name': symbol, 
                    'error': str(e)
                }
        
        return st.session_state[cache_key]
    
    @staticmethod
    def get_price_data(symbol: str, period: str = "1y") -> Dict[str, Any]:
        """Get price data for specific period"""
        cache_key = f"{symbol}_data_{period}"
        
        if cache_key not in st.session_state:
            try:
                data = stock_fetcher.fetch_stock_data(symbol, period=period)
                st.session_state[cache_key] = data
            except Exception as e:
                st.session_state[cache_key] = None
                st.error(f"Failed to load {period} data: {str(e)}")
        
        return st.session_state[cache_key]
    
    @staticmethod
    def get_analysis(symbol: str, period: str = "1y") -> Dict[str, Any]:
        """Get technical analysis for specific period"""
        cache_key = f"{symbol}_analysis_{period}"
        
        if cache_key not in st.session_state:
            data = DataService.get_price_data(symbol, period)
            if data is not None and hasattr(data, 'empty') and not data.empty:
                try:
                    analysis = stock_analyzer.analyze_stock(data)
                    analysis['period'] = period
                    st.session_state[cache_key] = analysis
                except Exception as e:
                    st.session_state[cache_key] = {'error': f"Analysis failed: {str(e)}"}
            else:
                st.session_state[cache_key] = {'error': 'No data available'}
        
        return st.session_state[cache_key]
    
    @staticmethod
    def get_trading_recommendation(symbol: str, country: str) -> Dict[str, Any]:
        """Get trading recommendation"""
        cache_key = f"{symbol}_trading"
        
        if cache_key not in st.session_state:
            try:
                analysis = DataService.get_analysis(symbol)
                stock_info = DataService.get_basic_info(symbol, country)
                
                if 'error' not in analysis and 'error' not in stock_info:
                    trading = trading_engine.get_trading_recommendation(symbol, analysis, stock_info)
                    st.session_state[cache_key] = trading
                else:
                    st.session_state[cache_key] = {'error': 'Cannot generate recommendation'}
            except Exception as e:
                st.session_state[cache_key] = {'error': f"Trading analysis failed: {str(e)}"}
        
        return st.session_state[cache_key]
    
    @staticmethod
    def get_sharia_compliance(symbol: str, country: str) -> Dict[str, Any]:
        """Get Sharia compliance analysis"""
        cache_key = f"{symbol}_sharia"
        
        if cache_key not in st.session_state:
            try:
                stock_info = DataService.get_basic_info(symbol, country)
                analysis = DataService.get_analysis(symbol)
                
                if 'error' not in stock_info:
                    sharia = sharia_checker.check_sharia_compliance(symbol, stock_info, analysis)
                    st.session_state[cache_key] = sharia
                else:
                    st.session_state[cache_key] = {'error': 'Cannot check compliance'}
            except Exception as e:
                st.session_state[cache_key] = {'error': f"Sharia check failed: {str(e)}"}
        
        return st.session_state[cache_key]
    
    @staticmethod
    def clear_cache(symbol: Optional[str] = None):
        """Clear cached data"""
        if symbol:
            keys_to_remove = [key for key in st.session_state.keys() if isinstance(key, str) and key.startswith(f"{symbol}_")]
            for key in keys_to_remove:
                del st.session_state[key]
        else:
            # Clear all cache
            keys_to_remove = [key for key in st.session_state.keys() 
                            if isinstance(key, str) and ('_data_' in key or '_analysis_' in key or '_trading' in key or '_sharia' in key or '_basic' in key)]
            for key in keys_to_remove:
                del st.session_state[key]


# Global instance
data_service = DataService()
