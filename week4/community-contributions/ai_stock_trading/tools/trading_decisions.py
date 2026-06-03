"""
Trading Decisions Module

This module provides AI-powered trading recommendations using OpenAI
and advanced algorithmic decision-making based on technical analysis.
"""

import os
import json
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TradingDecisionEngine:
    """Enhanced trading decision engine with AI and algorithmic analysis"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Trading signal weights
        self.signal_weights = {
            'trend': 0.25,
            'momentum': 0.20,
            'volume': 0.15,
            'volatility': 0.15,
            'technical': 0.25
        }
    
    def get_trading_recommendation(self, symbol: str, analysis: Dict, stock_info: Dict) -> Dict:
        """
        Get comprehensive trading recommendation
        
        Args:
            symbol: Stock symbol
            analysis: Technical analysis results
            stock_info: Stock information
            
        Returns:
            Dictionary with trading recommendation
        """
        try:
            # Get algorithmic score
            algo_decision = self._get_algorithmic_decision(analysis)
            
            # Get AI-powered recommendation
            ai_decision = self._get_ai_recommendation(symbol, analysis, stock_info)
            
            # Combine decisions
            final_decision = self._combine_decisions(algo_decision, ai_decision)
            
            return {
                'symbol': symbol,
                'recommendation': final_decision['action'],
                'confidence': final_decision['confidence'],
                'price_target': final_decision.get('price_target'),
                'stop_loss': final_decision.get('stop_loss'),
                'reasoning': final_decision['reasoning'],
                'algorithmic_score': algo_decision['score'],
                'ai_recommendation': ai_decision['recommendation'],
                'risk_level': self._assess_risk_level(analysis),
                'time_horizon': final_decision.get('time_horizon', 'medium'),
                'key_factors': final_decision.get('key_factors', [])
            }
            
        except Exception as e:
            return {
                'symbol': symbol,
                'recommendation': 'HOLD',
                'confidence': 0.5,
                'reasoning': f'Error in analysis: {str(e)}',
                'error': str(e)
            }
    
    def _get_algorithmic_decision(self, analysis: Dict) -> Dict:
        """
        Generate algorithmic trading decision based on technical indicators
        
        Args:
            analysis: Technical analysis results
            
        Returns:
            Dictionary with algorithmic decision
        """
        signals = {}
        
        # Trend signals
        trend_score = self._calculate_trend_signal(analysis)
        signals['trend'] = trend_score
        
        # Momentum signals
        momentum_score = self._calculate_momentum_signal(analysis)
        signals['momentum'] = momentum_score
        
        # Volume signals
        volume_score = self._calculate_volume_signal(analysis)
        signals['volume'] = volume_score
        
        # Volatility signals
        volatility_score = self._calculate_volatility_signal(analysis)
        signals['volatility'] = volatility_score
        
        # Technical indicator signals
        technical_score = self._calculate_technical_signal(analysis)
        signals['technical'] = technical_score
        
        # Calculate weighted score
        total_score = sum(signals[key] * self.signal_weights[key] for key in signals)
        
        # Determine action
        if total_score >= 0.6:
            action = 'BUY'
        elif total_score <= -0.6:
            action = 'SELL'
        else:
            action = 'HOLD'
        
        return {
            'action': action,
            'score': total_score,
            'signals': signals,
            'confidence': min(abs(total_score), 1.0)
        }
    
    def _calculate_trend_signal(self, analysis: Dict) -> float:
        """Calculate trend-based signal (-1 to 1)"""
        score = 0.0
        
        # Trend direction and strength
        if analysis.get('trend_direction') == 'upward':
            score += 0.5
        elif analysis.get('trend_direction') == 'downward':
            score -= 0.5
        
        # Trend strength
        trend_strength = analysis.get('trend_strength', 0)
        score *= trend_strength
        
        # Moving average signals
        if 'price_vs_sma_20' in analysis:
            sma_20_signal = analysis['price_vs_sma_20']
            if sma_20_signal > 2:
                score += 0.2
            elif sma_20_signal < -2:
                score -= 0.2
        
        if 'price_vs_sma_50' in analysis:
            sma_50_signal = analysis['price_vs_sma_50']
            if sma_50_signal > 2:
                score += 0.3
            elif sma_50_signal < -2:
                score -= 0.3
        
        return max(-1.0, min(1.0, score))
    
    def _calculate_momentum_signal(self, analysis: Dict) -> float:
        """Calculate momentum-based signal (-1 to 1)"""
        score = 0.0
        
        # RSI signal
        if 'rsi' in analysis:
            rsi = analysis['rsi']
            if rsi < 30:
                score += 0.4  # Oversold - potential buy
            elif rsi > 70:
                score -= 0.4  # Overbought - potential sell
        
        # MACD signal
        if 'macd_trend' in analysis:
            if analysis['macd_trend'] == 'bullish':
                score += 0.3
            else:
                score -= 0.3
        
        # Recent performance
        if 'return_1_week' in analysis:
            weekly_return = analysis['return_1_week']
            if weekly_return > 5:
                score += 0.2
            elif weekly_return < -5:
                score -= 0.2
        
        return max(-1.0, min(1.0, score))
    
    def _calculate_volume_signal(self, analysis: Dict) -> float:
        """Calculate volume-based signal (-1 to 1)"""
        score = 0.0
        
        # Volume trend
        if analysis.get('volume_trend') == 'increasing':
            score += 0.3
        elif analysis.get('volume_trend') == 'decreasing':
            score -= 0.2
        
        # Volume vs average
        if 'volume_vs_avg' in analysis:
            vol_vs_avg = analysis['volume_vs_avg']
            if vol_vs_avg > 20:
                score += 0.2
            elif vol_vs_avg < -20:
                score -= 0.1
        
        return max(-1.0, min(1.0, score))
    
    def _calculate_volatility_signal(self, analysis: Dict) -> float:
        """Calculate volatility-based signal (-1 to 1)"""
        score = 0.0
        
        # High volatility can be both opportunity and risk
        volatility = analysis.get('volatility_annualized', 0)
        
        if volatility > 50:
            score -= 0.3  # High risk
        elif volatility < 15:
            score += 0.2  # Low risk
        
        # Max drawdown consideration
        max_drawdown = analysis.get('max_drawdown', 0)
        if abs(max_drawdown) > 20:
            score -= 0.2
        
        return max(-1.0, min(1.0, score))
    
    def _calculate_technical_signal(self, analysis: Dict) -> float:
        """Calculate technical indicator signal (-1 to 1)"""
        score = 0.0
        
        # Bollinger Bands
        if 'bb_position' in analysis:
            bb_pos = analysis['bb_position']
            if bb_pos == 'below_lower_band':
                score += 0.3  # Potential buy
            elif bb_pos == 'above_upper_band':
                score -= 0.3  # Potential sell
        
        # Sharpe ratio
        sharpe = analysis.get('sharpe_ratio', 0)
        if sharpe > 1:
            score += 0.2
        elif sharpe < 0:
            score -= 0.2
        
        return max(-1.0, min(1.0, score))
    
    def _get_ai_recommendation(self, symbol: str, analysis: Dict, stock_info: Dict) -> Dict:
        """
        Get AI-powered trading recommendation using OpenAI
        
        Args:
            symbol: Stock symbol
            analysis: Technical analysis results
            stock_info: Stock information
            
        Returns:
            Dictionary with AI recommendation
        """
        try:
            # Prepare analysis data for AI
            analysis_summary = self._prepare_analysis_for_ai(analysis, stock_info)
            
            prompt = f"""
            You are a senior financial analyst with 15+ years of experience providing institutional-grade trading recommendations. 
            Analyze {symbol} and provide a professional trading recommendation.
            
            Company Information:
            - Name: {stock_info.get('company_name', 'N/A')}
            - Sector: {stock_info.get('sector', 'N/A')}
            - Market Cap: ${stock_info.get('market_cap', 0):,}
            
            Technical Analysis Data:
            {analysis_summary}
            
            REQUIREMENTS:
            1. Provide BUY/HOLD/SELL recommendation based on technical analysis
            2. Set realistic confidence level (60-95% range)
            3. Calculate logical price targets using support/resistance levels
            4. Set appropriate stop-loss levels (5-15% below entry for long positions)
            5. Consider risk-reward ratios (minimum 1:2 ratio preferred)
            6. Provide clear, actionable reasoning without jargon
            7. Consider market conditions and sector trends
            
            TRADING STANDARDS:
            - BUY: Strong upward momentum, good risk/reward, clear catalysts
            - HOLD: Consolidation phase, mixed signals, or fair value
            - SELL: Downward trend, poor fundamentals, or overvalued
            
            Return ONLY valid JSON:
            {{
                "recommendation": "BUY/HOLD/SELL",
                "confidence": 85,
                "price_target": 150.00,
                "stop_loss": 120.00,
                "time_horizon": "short/medium/long",
                "reasoning": "Professional analysis explaining the recommendation with specific technical factors",
                "key_factors": ["specific technical indicator", "market condition", "risk factor"],
                "risk_assessment": "low/medium/high"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst providing professional trading recommendations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            
            if ai_response:
                try:
                    # Clean the response - extract JSON
                    json_start = ai_response.find('{')
                    json_end = ai_response.rfind('}') + 1
                    
                    if json_start != -1 and json_end != -1:
                        json_str = ai_response[json_start:json_end]
                        ai_recommendation = json.loads(json_str)
                        
                        # Validate and clean the response
                        return {
                            'recommendation': ai_recommendation.get('recommendation', 'HOLD'),
                            'confidence': ai_recommendation.get('confidence', 50),
                            'price_target': ai_recommendation.get('price_target'),
                            'stop_loss': ai_recommendation.get('stop_loss'),
                            'time_horizon': ai_recommendation.get('time_horizon', 'medium'),
                            'reasoning': ai_recommendation.get('reasoning', 'AI analysis completed'),
                            'key_factors': ai_recommendation.get('key_factors', []),
                            'risk_assessment': ai_recommendation.get('risk_assessment', 'medium')
                        }
                    else:
                        # No JSON found, use fallback
                        return self._parse_ai_response_fallback(ai_response)
                        
                except json.JSONDecodeError:
                    # Fallback parsing
                    return self._parse_ai_response_fallback(ai_response)
            else:
                return self._parse_ai_response_fallback('No response received')
                
        except Exception as e:
            return {
                'recommendation': 'HOLD',
                'confidence': 50,
                'reasoning': f'AI analysis unavailable: {str(e)}',
                'error': str(e)
            }
    
    def _prepare_analysis_for_ai(self, analysis: Dict, stock_info: Dict) -> str:
        """Prepare analysis summary for AI consumption"""
        summary_parts = []
        
        # Price metrics
        current_price = analysis.get('current_price', 0)
        total_return = analysis.get('total_return_pct', 0)
        summary_parts.append(f"Current Price: ${current_price:.2f}")
        summary_parts.append(f"Total Return: {total_return:.2f}%")
        
        # Trend analysis
        trend_dir = analysis.get('trend_direction', 'unknown')
        trend_strength = analysis.get('trend_strength', 0)
        summary_parts.append(f"Trend: {trend_dir} (strength: {trend_strength:.2f})")
        
        # Technical indicators
        if 'rsi' in analysis:
            rsi = analysis['rsi']
            rsi_signal = analysis.get('rsi_signal', 'neutral')
            summary_parts.append(f"RSI: {rsi:.1f} ({rsi_signal})")
        
        if 'macd_trend' in analysis:
            summary_parts.append(f"MACD: {analysis['macd_trend']}")
        
        # Risk metrics
        volatility = analysis.get('volatility_annualized', 0)
        max_drawdown = analysis.get('max_drawdown', 0)
        summary_parts.append(f"Volatility: {volatility:.1f}% (annual)")
        summary_parts.append(f"Max Drawdown: {max_drawdown:.1f}%")
        
        # Performance
        if 'return_1_month' in analysis:
            monthly_return = analysis['return_1_month']
            summary_parts.append(f"1-Month Return: {monthly_return:.2f}%")
        
        return "\n".join(summary_parts)
    
    def _parse_ai_response_fallback(self, response: str) -> Dict:
        """Fallback parser for AI response if JSON parsing fails"""
        # Simple keyword-based parsing
        recommendation = 'HOLD'
        confidence = 50
        
        response_lower = response.lower()
        
        if 'buy' in response_lower and 'sell' not in response_lower:
            recommendation = 'BUY'
            confidence = 70
        elif 'sell' in response_lower:
            recommendation = 'SELL'
            confidence = 70
        
        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'reasoning': response,
            'parsed_fallback': True
        }
    
    def _combine_decisions(self, algo_decision: Dict, ai_decision: Dict) -> Dict:
        """Combine algorithmic and AI decisions"""
        # Weight the decisions (60% algorithmic, 40% AI)
        algo_weight = 0.6
        ai_weight = 0.4
        
        # Map recommendations to scores
        rec_scores = {'BUY': 1, 'HOLD': 0, 'SELL': -1}
        
        algo_score = rec_scores.get(algo_decision['action'], 0)
        ai_score = rec_scores.get(ai_decision.get('recommendation', 'HOLD'), 0)
        
        # Calculate combined score
        combined_score = (algo_score * algo_weight) + (ai_score * ai_weight)
        
        # Determine final recommendation
        if combined_score >= 0.3:
            final_action = 'BUY'
        elif combined_score <= -0.3:
            final_action = 'SELL'
        else:
            final_action = 'HOLD'
        
        # Calculate confidence
        algo_confidence = algo_decision.get('confidence', 0.5)
        ai_confidence = ai_decision.get('confidence', 50) / 100
        combined_confidence = (algo_confidence * algo_weight) + (ai_confidence * ai_weight)
        
        return {
            'action': final_action,
            'confidence': combined_confidence,
            'combined_score': combined_score,
            'reasoning': ai_decision.get('reasoning', 'Combined algorithmic and AI analysis'),
            'price_target': ai_decision.get('price_target'),
            'stop_loss': ai_decision.get('stop_loss'),
            'time_horizon': ai_decision.get('time_horizon', 'medium'),
            'key_factors': ai_decision.get('key_factors', [])
        }
    
    def _assess_risk_level(self, analysis: Dict) -> str:
        """Assess overall risk level"""
        risk_score = 0
        
        # Volatility risk
        volatility = analysis.get('volatility_annualized', 0)
        if volatility > 40:
            risk_score += 2
        elif volatility > 25:
            risk_score += 1
        
        # Drawdown risk
        max_drawdown = abs(analysis.get('max_drawdown', 0))
        if max_drawdown > 30:
            risk_score += 2
        elif max_drawdown > 15:
            risk_score += 1
        
        # Sharpe ratio
        sharpe = analysis.get('sharpe_ratio', 0)
        if sharpe < 0:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 4:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'

# Global instance for easy import
trading_engine = TradingDecisionEngine()

# Convenience function
def get_trading_recommendation(symbol: str, analysis: Dict, stock_info: Dict) -> Dict:
    """Convenience function to get trading recommendation"""
    return trading_engine.get_trading_recommendation(symbol, analysis, stock_info)
