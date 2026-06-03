"""
Stock Data Fetching Module

This module handles fetching stock data from various sources including yfinance
and provides enhanced data retrieval capabilities for different markets.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
from typing import Dict, List, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')

class StockDataFetcher:
    """Enhanced stock data fetcher with multi-market support"""
    
    # Stock symbols for different markets
    STOCK_SYMBOLS = {
        'USA': {
            # Technology
            'Apple Inc.': 'AAPL',
            'Microsoft Corporation': 'MSFT',
            'NVIDIA Corporation': 'NVDA',
            'Alphabet Inc. (Class A)': 'GOOGL',
            'Alphabet Inc. (Class C)': 'GOOG',
            'Meta Platforms Inc.': 'META',
            'Tesla Inc.': 'TSLA',
            'Amazon.com Inc.': 'AMZN',
            'Netflix Inc.': 'NFLX',
            'Adobe Inc.': 'ADBE',
            'Salesforce Inc.': 'CRM',
            'Oracle Corporation': 'ORCL',
            'Cisco Systems Inc.': 'CSCO',
            'Intel Corporation': 'INTC',
            'Advanced Micro Devices': 'AMD',
            'Qualcomm Inc.': 'QCOM',
            'Texas Instruments': 'TXN',
            'Broadcom Inc.': 'AVGO',
            'ServiceNow Inc.': 'NOW',
            'Palantir Technologies': 'PLTR',
            
            # Financial Services
            'JPMorgan Chase & Co.': 'JPM',
            'Bank of America Corp': 'BAC',
            'Wells Fargo & Company': 'WFC',
            'Goldman Sachs Group': 'GS',
            'Morgan Stanley': 'MS',
            'Citigroup Inc.': 'C',
            'American Express Company': 'AXP',
            'Berkshire Hathaway Inc.': 'BRK.B',
            'BlackRock Inc.': 'BLK',
            'Charles Schwab Corporation': 'SCHW',
            'Visa Inc.': 'V',
            'Mastercard Inc.': 'MA',
            
            # Healthcare & Pharmaceuticals
            'Johnson & Johnson': 'JNJ',
            'UnitedHealth Group': 'UNH',
            'Pfizer Inc.': 'PFE',
            'AbbVie Inc.': 'ABBV',
            'Merck & Co Inc.': 'MRK',
            'Eli Lilly and Company': 'LLY',
            'Abbott Laboratories': 'ABT',
            'Thermo Fisher Scientific': 'TMO',
            'Danaher Corporation': 'DHR',
            'Gilead Sciences Inc.': 'GILD',
            
            # Consumer & Retail
            'Walmart Inc.': 'WMT',
            'Procter & Gamble Co': 'PG',
            'Coca-Cola Company': 'KO',
            'PepsiCo Inc.': 'PEP',
            'Home Depot Inc.': 'HD',
            'McDonald\'s Corporation': 'MCD',
            'Nike Inc.': 'NKE',
            'Costco Wholesale Corp': 'COST',
            'TJX Companies Inc.': 'TJX',
            'Lowe\'s Companies Inc.': 'LOW',
            
            # Industrial & Energy
            'Exxon Mobil Corporation': 'XOM',
            'Chevron Corporation': 'CVX',
            'ConocoPhillips': 'COP',
            'Caterpillar Inc.': 'CAT',
            'Boeing Company': 'BA',
            'General Electric': 'GE',
            'Honeywell International': 'HON',
            'Deere & Company': 'DE',
            'Union Pacific Corporation': 'UNP',
            'Lockheed Martin Corp': 'LMT',
            
            # Communication & Media
            'AT&T Inc.': 'T',
            'Verizon Communications': 'VZ',
            'T-Mobile US Inc.': 'TMUS',
            'Comcast Corporation': 'CMCSA',
            'Walt Disney Company': 'DIS'
        },
        'Egypt': {
            # Banking & Financial Services
            'Commercial International Bank': 'COMI.CA',
            'QNB Alahli Bank': 'QNBE.CA',
            'Housing and Development Bank': 'HDBK.CA',
            'Abu Dhabi Islamic Bank Egypt': 'ADIB.CA',
            'Egyptian Gulf Bank': 'EGBE.CA',
            
            # Real Estate & Construction
            'Talaat Moustafa Group Holding': 'TMGH.CA',
            'Palm Hills Developments': 'PHDC.CA',
            'Orascom Construction': 'ORAS.CA',
            'Orascom Development Holding': 'ORHD.CA',
            'Six of October Development': 'SCTS.CA',
            'Heliopolis Housing': 'HELI.CA',
            'Rooya Group': 'RMDA.CA',
            
            # Industrial & Manufacturing
            'Eastern Company': 'EAST.CA',
            'El Sewedy Electric Company': 'SWDY.CA',
            'Ezz Steel': 'ESRS.CA',
            'Iron and Steel Company': 'IRON.CA',
            'Alexandria Containers': 'ALCN.CA',
            'Sidi Kerir Petrochemicals': 'SKPC.CA',
            
            # Chemicals & Fertilizers
            'Abu Qir Fertilizers and Chemical Industries': 'ABUK.CA',
            'Egyptian Chemical Industries (Kima)': 'KIMA.CA',
            'Misr Fertilizers Production': 'MFPC.CA',
            
            # Telecommunications & Technology
            'Telecom Egypt': 'ETEL.CA',
            'Raya Holding': 'RAYA.CA',
            'E-Finance for Digital Payments': 'EFIH.CA',
            'Fawry for Banking Technology': 'FWRY.CA',
            
            # Food & Beverages
            'Juhayna Food Industries': 'JUFO.CA',
            'Edita Food Industries': 'EFID.CA',
            'Cairo Poultry Company': 'POUL.CA',
            'Upper Egypt Flour Mills': 'UEFM.CA',
            'Ismailia Misr Poultry': 'ISPH.CA',
            
            # Healthcare & Pharmaceuticals
            'Cleopatra Hospital Group': 'CLHO.CA',
            'Cairo Pharmaceuticals': 'PHAR.CA',
            
            # Energy & Utilities
            'Egyptian Natural Gas Company': 'EGAS.CA',
            'Suez Cement Company': 'SCEM.CA',
            'Arabian Cement Company': 'ARCC.CA',
            
            # Investment & Holding Companies
            'Egyptian Financial Group-Hermes': 'HRHO.CA',
            'Citadel Capital': 'CCAP.CA',
            'Beltone Financial Holding': 'BTFH.CA'
        }
    }
    
    # Currency mapping for different markets
    MARKET_CURRENCIES = {
        'USA': 'USD',
        'Egypt': 'EGP'
    }
    
    def __init__(self):
        self.cache = {}
    
    def get_available_stocks(self, country: str) -> Dict[str, str]:
        """Get available stocks for a specific country"""
        return self.STOCK_SYMBOLS.get(country, {})
    
    def get_market_currency(self, country: str) -> str:
        """Get the currency for a specific market"""
        return self.MARKET_CURRENCIES.get(country, 'USD')
    
    def format_price_with_currency(self, price: float, country: str) -> str:
        """Format price with appropriate currency symbol"""
        currency = self.get_market_currency(country)
        if currency == 'EGP':
            return f"{price:.2f} EGP"
        elif currency == 'USD':
            return f"${price:.2f}"
        else:
            return f"{price:.2f} {currency}"
    
    def fetch_stock_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """
        Fetch historical stock data with enhanced error handling
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'COMI.CA')
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: Data interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
        
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"{symbol}_{period}_{interval}"
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                print(f"⚠️ No data found for {symbol}")
                return pd.DataFrame()
            
            # Clean and enhance data
            data = self._clean_data(data)
            
            # Cache the result
            self.cache[cache_key] = data
            
            print(f"✅ Successfully fetched {len(data)} data points for {symbol} ({period})")
            return data
            
        except Exception as e:
            print(f"❌ Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_stock_info(self, symbol: str, country: Optional[str] = None) -> Dict:
        """
        Get comprehensive stock information
        
        Args:
            symbol: Stock symbol
            country: Market country (USA, Egypt) for currency handling
            
        Returns:
            Dictionary with stock information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Detect country if not provided
            if country is None:
                country = self._detect_country_from_symbol(symbol)
            
            # Get market currency
            market_currency = self.get_market_currency(country)
            
            # Extract key information
            stock_info = {
                'symbol': symbol,
                'company_name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'current_price': info.get('currentPrice', 0),
                'currency': market_currency,  # Use detected market currency
                'exchange': info.get('exchange', 'N/A'),
                'country': country,
                'market_country': country  # Add explicit market country
            }
            
            return stock_info
            
        except Exception as e:
            print(f"❌ Error fetching info for {symbol}: {str(e)}")
            return {'symbol': symbol, 'error': str(e)}
    
    def _detect_country_from_symbol(self, symbol: str) -> str:
        """
        Detect country from stock symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Country name (USA or Egypt)
        """
        # Check if symbol exists in any country's stock list
        for country, stocks in self.STOCK_SYMBOLS.items():
            if symbol in stocks.values():
                return country
        
        # Default to USA if not found
        return 'USA'
    
    def fetch_multiple_periods(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple time periods
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with DataFrames for different periods
        """
        periods = ['1mo', '1y', '5y']
        data = {}
        
        for period in periods:
            df = self.fetch_stock_data(symbol, period)
            if not df.empty:
                data[period] = df
        
        return data
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and enhance the stock data
        
        Args:
            data: Raw stock data DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        # Remove rows with all NaN values
        data = data.dropna(how='all')
        
        # Forward fill missing values
        data = data.fillna(method='ffill')
        
        # Add technical indicators
        if len(data) > 0:
            # Simple moving averages
            if len(data) >= 20:
                data['SMA_20'] = data['Close'].rolling(window=20).mean()
            if len(data) >= 50:
                data['SMA_50'] = data['Close'].rolling(window=50).mean()
            
            # Daily returns
            data['Daily_Return'] = data['Close'].pct_change()
            
            # Price change from previous day
            data['Price_Change'] = data['Close'].diff()
            data['Price_Change_Pct'] = (data['Price_Change'] / data['Close'].shift(1)) * 100
        
        return data
    
    def get_real_time_price(self, symbol: str) -> Optional[float]:
        """
        Get real-time stock price
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current stock price or None if error
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if not data.empty:
                return float(data['Close'].iloc[-1])
            return None
            
        except Exception as e:
            print(f"❌ Error fetching real-time price for {symbol}: {str(e)}")
            return None

# Global instance for easy import
stock_fetcher = StockDataFetcher()

# Convenience functions
def fetch_stock_data(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Convenience function to fetch stock data"""
    return stock_fetcher.fetch_stock_data(symbol, period, interval)

def get_available_stocks(country: str) -> Dict[str, str]:
    """Convenience function to get available stocks"""
    return stock_fetcher.get_available_stocks(country)

def get_stock_info(symbol: str) -> Dict:
    """Convenience function to get stock info"""
    return stock_fetcher.get_stock_info(symbol)
