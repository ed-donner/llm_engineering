"""
AI Stock Trading Tools

This package contains all the core tools for the AI Stock Trading platform:
- fetching: Stock data fetching and market data
- analysis: Technical analysis and stock metrics
- trading_decisions: AI-powered trading recommendations
- sharia_compliance: Islamic finance compliance checking
- charting: Interactive charts and visualizations
"""

__version__ = "1.0.0"
__author__ = "AI Stock Trading Platform"

# Import main classes and functions for easy access
from .fetching import StockDataFetcher, stock_fetcher, fetch_stock_data, get_available_stocks
from .analysis import StockAnalyzer, stock_analyzer, analyze_stock
from .trading_decisions import TradingDecisionEngine, trading_engine, get_trading_recommendation
from .sharia_compliance import ShariaComplianceChecker, sharia_checker, check_sharia_compliance
from .charting import StockChartGenerator, chart_generator, create_price_chart

__all__ = [
    'StockDataFetcher', 'stock_fetcher', 'fetch_stock_data', 'get_available_stocks',
    'StockAnalyzer', 'stock_analyzer', 'analyze_stock',
    'TradingDecisionEngine', 'trading_engine', 'get_trading_recommendation',
    'ShariaComplianceChecker', 'sharia_checker', 'check_sharia_compliance',
    'StockChartGenerator', 'chart_generator', 'create_price_chart'
]
