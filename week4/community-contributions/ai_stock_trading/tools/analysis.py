"""
Stock Analysis Module

This module provides enhanced technical and fundamental analysis capabilities
for stock data with advanced metrics and indicators.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
import warnings

warnings.filterwarnings('ignore')

class StockAnalyzer:
    """Enhanced stock analyzer with comprehensive technical indicators"""
    
    def __init__(self):
        pass
    
    def analyze_stock(self, data: pd.DataFrame) -> Dict:
        """
        Comprehensive stock analysis with enhanced metrics
        
        Args:
            data: DataFrame with OHLCV stock data
            
        Returns:
            Dictionary with analysis results
        """
        if data.empty:
            return {'error': 'No data provided for analysis'}
        
        try:
            analysis = {}
            
            # Basic price metrics
            analysis.update(self._calculate_price_metrics(data))
            
            # Technical indicators
            analysis.update(self._calculate_technical_indicators(data))
            
            # Volatility analysis
            analysis.update(self._calculate_volatility_metrics(data))
            
            # Volume analysis
            analysis.update(self._calculate_volume_metrics(data))
            
            # Trend analysis
            analysis.update(self._calculate_trend_metrics(data))
            
            # Risk metrics
            analysis.update(self._calculate_risk_metrics(data))
            
            # Performance metrics
            analysis.update(self._calculate_performance_metrics(data))
            
            return analysis
            
        except Exception as e:
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _calculate_price_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate basic price metrics"""
        close_prices = data['Close']
        
        return {
            'current_price': float(close_prices.iloc[-1]),
            'start_price': float(close_prices.iloc[0]),
            'max_price': float(close_prices.max()),
            'min_price': float(close_prices.min()),
            'price_range_pct': float(((close_prices.max() - close_prices.min()) / close_prices.min()) * 100),
            'total_return_pct': float(((close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0]) * 100)
        }
    
    def _calculate_technical_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate technical indicators"""
        close_prices = data['Close']
        high_prices = data['High']
        low_prices = data['Low']
        
        indicators = {}
        
        # Moving averages
        if len(data) >= 20:
            sma_20 = close_prices.rolling(window=20).mean()
            indicators['sma_20'] = float(sma_20.iloc[-1])
            indicators['price_vs_sma_20'] = float(((close_prices.iloc[-1] - sma_20.iloc[-1]) / sma_20.iloc[-1]) * 100)
        
        if len(data) >= 50:
            sma_50 = close_prices.rolling(window=50).mean()
            indicators['sma_50'] = float(sma_50.iloc[-1])
            indicators['price_vs_sma_50'] = float(((close_prices.iloc[-1] - sma_50.iloc[-1]) / sma_50.iloc[-1]) * 100)
        
        # Exponential Moving Average
        if len(data) >= 12:
            ema_12 = close_prices.ewm(span=12).mean()
            indicators['ema_12'] = float(ema_12.iloc[-1])
        
        # RSI (Relative Strength Index)
        if len(data) >= 14:
            rsi = self._calculate_rsi(pd.Series(close_prices), 14)
            indicators['rsi'] = float(rsi.iloc[-1])
            indicators['rsi_signal'] = self._interpret_rsi(float(rsi.iloc[-1]))
        
        # MACD
        if len(data) >= 26:
            macd_line, signal_line, histogram = self._calculate_macd(pd.Series(close_prices))
            indicators['macd'] = float(macd_line.iloc[-1])
            indicators['macd_signal'] = float(signal_line.iloc[-1])
            indicators['macd_histogram'] = float(histogram.iloc[-1])
            indicators['macd_trend'] = 'bullish' if float(histogram.iloc[-1]) > 0 else 'bearish'
        
        # Bollinger Bands
        if len(data) >= 20:
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(pd.Series(close_prices), 20, 2)
            indicators['bb_upper'] = float(bb_upper.iloc[-1])
            indicators['bb_middle'] = float(bb_middle.iloc[-1])
            indicators['bb_lower'] = float(bb_lower.iloc[-1])
            indicators['bb_position'] = self._interpret_bollinger_position(float(close_prices.iloc[-1]), float(bb_upper.iloc[-1]), float(bb_lower.iloc[-1]))
        
        return indicators
    
    def _calculate_volatility_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate volatility metrics"""
        close_prices = data['Close']
        daily_returns = close_prices.pct_change().dropna()
        
        return {
            'volatility_daily': float(daily_returns.std() * 100),
            'volatility_annualized': float(daily_returns.std() * np.sqrt(252) * 100),
            'avg_daily_return': float(daily_returns.mean() * 100),
            'max_daily_gain': float(daily_returns.max() * 100),
            'max_daily_loss': float(daily_returns.min() * 100)
        }
    
    def _calculate_volume_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate volume metrics"""
        volume = data['Volume']
        
        metrics: Dict[str, Union[float, str]] = {
            'avg_volume': float(volume.mean()),
            'current_volume': float(volume.iloc[-1]),
            'max_volume': float(volume.max()),
            'min_volume': float(volume.min())
        }
        
        # Volume trend
        if len(volume) >= 10:
            recent_avg = volume.tail(10).mean()
            overall_avg = volume.mean()
            if recent_avg > overall_avg:
                metrics['volume_trend'] = 'increasing'
            else:
                metrics['volume_trend'] = 'decreasing'
            metrics['volume_vs_avg'] = float(((recent_avg - overall_avg) / overall_avg) * 100)
        
        return metrics
    
    def _calculate_trend_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate trend analysis metrics"""
        close_prices = data['Close']
        
        # Linear regression for trend
        x = np.arange(len(close_prices))
        slope, intercept = np.polyfit(x, close_prices, 1)
        
        # Trend strength
        correlation = np.corrcoef(x, close_prices)[0, 1]
        
        return {
            'trend_slope': float(slope),
            'trend_direction': 'upward' if slope > 0 else 'downward',
            'trend_strength': float(abs(correlation)),
            'trend_angle': float(np.degrees(np.arctan(slope))),
            'r_squared': float(correlation ** 2)
        }
    
    def _calculate_risk_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate risk metrics"""
        close_prices = data['Close']
        daily_returns = close_prices.pct_change().dropna()
        
        # Value at Risk (VaR)
        var_95 = np.percentile(daily_returns, 5)
        var_99 = np.percentile(daily_returns, 1)
        
        # Maximum Drawdown
        cumulative_returns = (1 + daily_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Sharpe Ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02 / 252  # Daily risk-free rate
        excess_returns = daily_returns - risk_free_rate
        sharpe_ratio = excess_returns.mean() / daily_returns.std() if daily_returns.std() != 0 else 0
        
        return {
            'var_95': float(var_95 * 100),
            'var_99': float(var_99 * 100),
            'max_drawdown': float(max_drawdown * 100),
            'sharpe_ratio': float(sharpe_ratio * np.sqrt(252)),  # Annualized
            'downside_deviation': float(daily_returns[daily_returns < 0].std() * 100)
        }
    
    def _calculate_performance_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate performance metrics"""
        close_prices = data['Close']
        
        # Different period returns
        periods = {
            '1_week': min(5, len(close_prices) - 1),
            '1_month': min(22, len(close_prices) - 1),
            '3_months': min(66, len(close_prices) - 1),
            '6_months': min(132, len(close_prices) - 1)
        }
        
        performance = {}
        current_price = close_prices.iloc[-1]
        
        for period_name, days_back in periods.items():
            if days_back > 0:
                past_price = close_prices.iloc[-(days_back + 1)]
                return_pct = ((current_price - past_price) / past_price) * 100
                performance[f'return_{period_name}'] = float(return_pct)
        
        return performance
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _interpret_rsi(self, rsi_value: float) -> str:
        """Interpret RSI value"""
        if rsi_value >= 70:
            return 'overbought'
        elif rsi_value <= 30:
            return 'oversold'
        else:
            return 'neutral'
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    def _interpret_bollinger_position(self, current_price: float, upper_band: float, lower_band: float) -> str:
        """Interpret position relative to Bollinger Bands"""
        if current_price > upper_band:
            return 'above_upper_band'
        elif current_price < lower_band:
            return 'below_lower_band'
        else:
            return 'within_bands'
    
    def get_analysis_summary(self, analysis: Dict) -> str:
        """Generate a human-readable analysis summary"""
        if 'error' in analysis:
            return f"Analysis Error: {analysis['error']}"
        
        summary = []
        
        # Price summary
        current_price = analysis.get('current_price', 0)
        total_return = analysis.get('total_return_pct', 0)
        summary.append(f"Current Price: ${current_price:.2f}")
        summary.append(f"Total Return: {total_return:.2f}%")
        
        # Trend
        trend_direction = analysis.get('trend_direction', 'unknown')
        trend_strength = analysis.get('trend_strength', 0)
        summary.append(f"Trend: {trend_direction.title()} (Strength: {trend_strength:.2f})")
        
        # Technical indicators
        if 'rsi' in analysis:
            rsi = analysis['rsi']
            rsi_signal = analysis['rsi_signal']
            summary.append(f"RSI: {rsi:.1f} ({rsi_signal})")
        
        if 'macd_trend' in analysis:
            macd_trend = analysis['macd_trend']
            summary.append(f"MACD: {macd_trend}")
        
        # Risk
        volatility = analysis.get('volatility_annualized', 0)
        max_drawdown = analysis.get('max_drawdown', 0)
        summary.append(f"Volatility: {volatility:.1f}% (Annual)")
        summary.append(f"Max Drawdown: {max_drawdown:.1f}%")
        
        return "\n".join(summary)

# Global instance for easy import
stock_analyzer = StockAnalyzer()

# Convenience function
def analyze_stock(data: pd.DataFrame) -> Dict:
    """Convenience function to analyze stock data"""
    return stock_analyzer.analyze_stock(data)
