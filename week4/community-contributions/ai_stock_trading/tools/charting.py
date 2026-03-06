"""
Charting Module

This module provides comprehensive charting and visualization capabilities
for stock analysis with interactive dashboards using Plotly.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, List, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')

class StockChartGenerator:
    """Enhanced stock chart generator with interactive dashboards"""
    
    def __init__(self):
        self.color_scheme = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff7f0e',
            'info': '#17a2b8',
            'background': '#f8f9fa'
        }
    
    def create_price_chart(self, data: pd.DataFrame, symbol: str, analysis: Dict = None) -> go.Figure:
        """
        Create comprehensive price chart with technical indicators
        
        Args:
            data: Stock price data
            symbol: Stock symbol
            analysis: Technical analysis results
            
        Returns:
            Plotly figure object
        """
        if data.empty:
            return self._create_empty_chart("No data available")
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=(f'{symbol} Price Chart', 'Volume', 'Technical Indicators'),
            row_heights=[0.6, 0.2, 0.2]
        )
        
        # Main price chart (candlestick)
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Price',
                increasing_line_color=self.color_scheme['success'],
                decreasing_line_color=self.color_scheme['danger']
            ),
            row=1, col=1
        )
        
        # Add moving averages if available
        if 'SMA_20' in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['SMA_20'],
                    mode='lines',
                    name='SMA 20',
                    line=dict(color=self.color_scheme['primary'], width=1)
                ),
                row=1, col=1
            )
        
        if 'SMA_50' in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['SMA_50'],
                    mode='lines',
                    name='SMA 50',
                    line=dict(color=self.color_scheme['secondary'], width=1)
                ),
                row=1, col=1
            )
        
        # Volume chart
        colors = ['red' if close < open else 'green' for close, open in zip(data['Close'], data['Open'])]
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['Volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # Technical indicators (RSI if available in analysis)
        if analysis and 'rsi' in analysis:
            # Create RSI line (simplified - would need full RSI calculation for time series)
            rsi_value = analysis['rsi']
            rsi_line = [rsi_value] * len(data)
            
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=rsi_line,
                    mode='lines',
                    name=f'RSI ({rsi_value:.1f})',
                    line=dict(color=self.color_scheme['info'], width=2)
                ),
                row=3, col=1
            )
            
            # Add RSI reference lines
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)
        
        # Update layout
        fig.update_layout(
            title=f'{symbol} Stock Analysis Dashboard',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            template='plotly_white',
            height=800,
            showlegend=True,
            hovermode='x unified'
        )
        
        # Remove rangeslider for cleaner look
        fig.update_layout(xaxis_rangeslider_visible=False)
        
        return fig
    
    def create_performance_chart(self, data: pd.DataFrame, symbol: str, analysis: Dict) -> go.Figure:
        """
        Create performance analysis chart
        
        Args:
            data: Stock price data
            symbol: Stock symbol
            analysis: Analysis results with performance metrics
            
        Returns:
            Plotly figure object
        """
        if data.empty:
            return self._create_empty_chart("No data available for performance analysis")
        
        # Calculate cumulative returns
        daily_returns = data['Close'].pct_change().fillna(0)
        cumulative_returns = (1 + daily_returns).cumprod() - 1
        
        fig = go.Figure()
        
        # Cumulative returns line
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=cumulative_returns * 100,
                mode='lines',
                name='Cumulative Returns (%)',
                line=dict(color=self.color_scheme['primary'], width=2),
                fill='tonexty',
                fillcolor='rgba(31, 119, 180, 0.1)'
            )
        )
        
        # Add benchmark line (0% return)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Add performance annotations
        if analysis:
            total_return = analysis.get('total_return_pct', 0)
            fig.add_annotation(
                x=data.index[-1],
                y=total_return,
                text=f"Total Return: {total_return:.1f}%",
                showarrow=True,
                arrowhead=2,
                arrowcolor=self.color_scheme['primary'],
                bgcolor="white",
                bordercolor=self.color_scheme['primary']
            )
        
        fig.update_layout(
            title=f'{symbol} Performance Analysis',
            xaxis_title='Date',
            yaxis_title='Cumulative Returns (%)',
            template='plotly_white',
            height=500,
            hovermode='x'
        )
        
        return fig
    
    def create_risk_analysis_chart(self, analysis: Dict, symbol: str) -> go.Figure:
        """
        Create risk analysis visualization
        
        Args:
            analysis: Analysis results with risk metrics
            symbol: Stock symbol
            
        Returns:
            Plotly figure object
        """
        if not analysis or 'error' in analysis:
            return self._create_empty_chart("No risk data available")
        
        # Prepare risk metrics
        risk_metrics = {
            'Volatility (Annual)': analysis.get('volatility_annualized', 0),
            'Max Drawdown': abs(analysis.get('max_drawdown', 0)),
            'VaR 95%': abs(analysis.get('var_95', 0)),
            'VaR 99%': abs(analysis.get('var_99', 0))
        }
        
        # Create radar chart for risk metrics
        categories = list(risk_metrics.keys())
        values = list(risk_metrics.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=f'{symbol} Risk Profile',
            line_color=self.color_scheme['danger'],
            fillcolor='rgba(214, 39, 40, 0.1)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(values) * 1.2] if values else [0, 100]
                )
            ),
            title=f'{symbol} Risk Analysis Chart',
            template='plotly_white',
            height=500
        )
        
        return fig
    
    def create_comparison_chart(self, data_dict: Dict[str, pd.DataFrame], symbols: List[str]) -> go.Figure:
        """
        Create comparison chart for multiple stocks
        
        Args:
            data_dict: Dictionary of stock data {symbol: dataframe}
            symbols: List of stock symbols to compare
            
        Returns:
            Plotly figure object
        """
        fig = go.Figure()
        
        colors = [self.color_scheme['primary'], self.color_scheme['secondary'], 
                 self.color_scheme['success'], self.color_scheme['danger']]
        
        for i, symbol in enumerate(symbols):
            if symbol in data_dict and not data_dict[symbol].empty:
                data = data_dict[symbol]
                # Normalize prices to start at 100 for comparison
                normalized_prices = (data['Close'] / data['Close'].iloc[0]) * 100
                
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=normalized_prices,
                        mode='lines',
                        name=symbol,
                        line=dict(color=colors[i % len(colors)], width=2)
                    )
                )
        
        fig.update_layout(
            title='Stock Price Comparison (Normalized to 100)',
            xaxis_title='Date',
            yaxis_title='Normalized Price',
            template='plotly_white',
            height=600,
            hovermode='x unified'
        )
        
        return fig
    
    def create_sector_analysis_chart(self, sector_data: Dict) -> go.Figure:
        """
        Create sector analysis visualization
        
        Args:
            sector_data: Dictionary with sector analysis data
            
        Returns:
            Plotly figure object
        """
        # This would typically show sector performance, P/E ratios, etc.
        # For now, create a placeholder
        fig = go.Figure()
        
        fig.add_annotation(
            x=0.5, y=0.5,
            text="Sector Analysis<br>Coming Soon",
            showarrow=False,
            font=dict(size=20),
            xref="paper", yref="paper"
        )
        
        fig.update_layout(
            title='Sector Analysis Dashboard',
            template='plotly_white',
            height=400,
            showticklabels=False
        )
        
        return fig
    
    def create_trading_signals_chart(self, data: pd.DataFrame, analysis: Dict, trading_decision: Dict, symbol: str) -> go.Figure:
        """
        Create trading signals visualization
        
        Args:
            data: Stock price data
            analysis: Technical analysis results
            trading_decision: Trading recommendation
            symbol: Stock symbol
            
        Returns:
            Plotly figure object
        """
        if data.empty:
            return self._create_empty_chart("No data available for trading signals")
        
        fig = go.Figure()
        
        # Price line
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['Close'],
                mode='lines',
                name='Price',
                line=dict(color=self.color_scheme['primary'], width=2)
            )
        )
        
        # Add trading signal
        recommendation = trading_decision.get('recommendation', 'HOLD')
        current_price = data['Close'].iloc[-1]
        
        signal_color = {
            'BUY': self.color_scheme['success'],
            'SELL': self.color_scheme['danger'],
            'HOLD': self.color_scheme['warning']
        }.get(recommendation, self.color_scheme['info'])
        
        fig.add_trace(
            go.Scatter(
                x=[data.index[-1]],
                y=[current_price],
                mode='markers',
                name=f'{recommendation} Signal',
                marker=dict(
                    color=signal_color,
                    size=15,
                    symbol='triangle-up' if recommendation == 'BUY' else 
                           'triangle-down' if recommendation == 'SELL' else 'circle'
                )
            )
        )
        
        # Add price target if available
        price_target = trading_decision.get('price_target')
        if price_target:
            fig.add_hline(
                y=price_target,
                line_dash="dash",
                line_color=self.color_scheme['success'],
                annotation_text=f"Target: ${price_target:.2f}"
            )
        
        # Add stop loss if available
        stop_loss = trading_decision.get('stop_loss')
        if stop_loss:
            fig.add_hline(
                y=stop_loss,
                line_dash="dash",
                line_color=self.color_scheme['danger'],
                annotation_text=f"Stop Loss: ${stop_loss:.2f}"
            )
        
        fig.update_layout(
            title=f'{symbol} Trading Signals',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            template='plotly_white',
            height=500,
            hovermode='x'
        )
        
        return fig
    
    def create_dashboard_summary(self, symbol: str, analysis: Dict, trading_decision: Dict, sharia_compliance: Dict) -> Dict:
        """
        Create summary metrics for dashboard display
        
        Args:
            symbol: Stock symbol
            analysis: Technical analysis results
            trading_decision: Trading recommendation
            sharia_compliance: Sharia compliance results
            
        Returns:
            Dictionary with summary metrics
        """
        summary = {
            'symbol': symbol,
            'current_price': analysis.get('current_price', 0),
            'total_return': analysis.get('total_return_pct', 0),
            'volatility': analysis.get('volatility_annualized', 0),
            'trading_recommendation': trading_decision.get('recommendation', 'HOLD'),
            'trading_confidence': trading_decision.get('confidence', 0) * 100,
            'sharia_ruling': sharia_compliance.get('ruling', 'UNCERTAIN'),
            'sharia_confidence': sharia_compliance.get('confidence', 0) * 100,
            'risk_level': trading_decision.get('risk_level', 'medium'),
            'trend_direction': analysis.get('trend_direction', 'unknown'),
            'rsi': analysis.get('rsi', 50),
            'max_drawdown': analysis.get('max_drawdown', 0)
        }
        
        return summary
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create an empty chart with a message"""
        fig = go.Figure()
        
        fig.add_annotation(
            x=0.5, y=0.5,
            text=message,
            showarrow=False,
            font=dict(size=16),
            xref="paper", yref="paper"
        )
        
        fig.update_layout(
            template='plotly_white',
            height=400,
            showticklabels=False
        )
        
        return fig

# Global instance for easy import
chart_generator = StockChartGenerator()

# Convenience functions
def create_price_chart(data: pd.DataFrame, symbol: str, analysis: Dict = None) -> go.Figure:
    """Convenience function to create price chart"""
    return chart_generator.create_price_chart(data, symbol, analysis)

def create_performance_chart(data: pd.DataFrame, symbol: str, analysis: Dict) -> go.Figure:
    """Convenience function to create performance chart"""
    return chart_generator.create_performance_chart(data, symbol, analysis)

def create_trading_signals_chart(data: pd.DataFrame, analysis: Dict, trading_decision: Dict, symbol: str) -> go.Figure:
    """Convenience function to create trading signals chart"""
    return chart_generator.create_trading_signals_chart(data, analysis, trading_decision, symbol)
