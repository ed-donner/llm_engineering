import os
from typing import Dict, Any, List
from openai import OpenAI
from .data_service import data_service


class AIAssistant:
    """Enhanced AI assistant with comprehensive stock analysis tools"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def get_enhanced_tools(self) -> List[Dict[str, Any]]:
        """Get comprehensive tool definitions for OpenAI function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_current_price_info",
                    "description": "Get current price, basic metrics, and company info",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"}
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_short_term_analysis",
                    "description": "Get 10-day technical analysis and short-term trends",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"}
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_medium_term_analysis",
                    "description": "Get 30-day technical analysis and medium-term trends",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"}
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_long_term_analysis",
                    "description": "Get 90-day technical analysis and long-term trends",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"}
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_comprehensive_analysis",
                    "description": "Get full 1-year technical analysis with all indicators",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"}
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_trading_recommendation",
                    "description": "Get buy/hold/sell recommendation with price targets and reasoning",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"}
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_sharia_compliance",
                    "description": "Get Islamic finance compliance analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"}
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compare_time_periods",
                    "description": "Compare performance across multiple time periods (10d, 30d, 90d)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"}
                        },
                        "required": ["symbol"]
                    }
                }
            }
        ]
    
    def generate_response(self, user_input: str, symbol: str, country: str) -> str:
        """Generate AI response with enhanced tool calling"""
        try:
            # Get basic info without heavy loading
            basic_info = data_service.get_basic_info(symbol, country)
            
            system_msg = f"""You are a professional financial advisor assistant for {symbol}.

IMPORTANT: Only call tools when users specifically request:
- Price information or basic metrics → get_current_price_info
- Short-term analysis (10 days) → get_short_term_analysis  
- Medium-term analysis (30 days) → get_medium_term_analysis
- Long-term analysis (90 days) → get_long_term_analysis
- Comprehensive analysis (1 year) → get_comprehensive_analysis
- Trading recommendations → get_trading_recommendation
- Sharia compliance → get_sharia_compliance
- Time period comparisons → compare_time_periods

For general questions about the company, market commentary, or basic information, respond directly without calling tools.
Keep responses concise and professional."""
            
            user_msg = f"""Stock: {symbol} ({basic_info.get('company_name', 'N/A')})
Country: {country}
Sector: {basic_info.get('sector', 'N/A')}
User Question: {user_input}"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                tools=self.get_enhanced_tools(),  # type: ignore
                tool_choice="auto",
                temperature=0.7,
                max_tokens=600
            )
            
            message = response.choices[0].message
            
            if message.tool_calls:
                return self._handle_tool_calls(message.tool_calls, user_input, symbol, country)
            
            return message.content or "I apologize, but I couldn't generate a response."
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def _handle_tool_calls(self, tool_calls, user_input: str, symbol: str, country: str) -> str:
        """Handle tool calls and generate final response"""
        tool_results = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            
            try:
                if function_name == "get_current_price_info":
                    basic_info = data_service.get_basic_info(symbol, country)
                    current_price = basic_info.get('current_price', 0)
                    market_cap = basic_info.get('market_cap', 0)
                    tool_results.append(f"Current Price: ${current_price:.2f}, Market Cap: ${market_cap:,.0f}")
                
                elif function_name == "get_short_term_analysis":
                    analysis = data_service.get_analysis(symbol, "10d")
                    if 'error' not in analysis:
                        return_pct = analysis.get('total_return_pct', 0)
                        volatility = analysis.get('volatility_annualized', 0)
                        tool_results.append(f"10-Day Analysis: Return {return_pct:.2f}%, Volatility {volatility:.1f}%")
                    else:
                        tool_results.append("10-Day Analysis: Data unavailable")
                
                elif function_name == "get_medium_term_analysis":
                    analysis = data_service.get_analysis(symbol, "1mo")
                    if 'error' not in analysis:
                        return_pct = analysis.get('total_return_pct', 0)
                        trend = analysis.get('trend_direction', 'neutral')
                        tool_results.append(f"30-Day Analysis: Return {return_pct:.2f}%, Trend {trend}")
                    else:
                        tool_results.append("30-Day Analysis: Data unavailable")
                
                elif function_name == "get_long_term_analysis":
                    analysis = data_service.get_analysis(symbol, "3mo")
                    if 'error' not in analysis:
                        return_pct = analysis.get('total_return_pct', 0)
                        sharpe = analysis.get('sharpe_ratio', 0)
                        tool_results.append(f"90-Day Analysis: Return {return_pct:.2f}%, Sharpe {sharpe:.2f}")
                    else:
                        tool_results.append("90-Day Analysis: Data unavailable")
                
                elif function_name == "get_comprehensive_analysis":
                    analysis = data_service.get_analysis(symbol, "1y")
                    if 'error' not in analysis:
                        return_pct = analysis.get('total_return_pct', 0)
                        max_drawdown = analysis.get('max_drawdown', 0)
                        rsi = analysis.get('rsi', 50)
                        tool_results.append(f"1-Year Analysis: Return {return_pct:.2f}%, Max Drawdown {max_drawdown:.1f}%, RSI {rsi:.1f}")
                    else:
                        tool_results.append("1-Year Analysis: Data unavailable")
                
                elif function_name == "get_trading_recommendation":
                    trading = data_service.get_trading_recommendation(symbol, country)
                    if 'error' not in trading:
                        rec = trading.get('recommendation', 'HOLD')
                        conf = trading.get('confidence', 0.5) * 100
                        tool_results.append(f"Trading: {rec} ({conf:.0f}% confidence)")
                    else:
                        tool_results.append("Trading: Analysis unavailable")
                
                elif function_name == "get_sharia_compliance":
                    sharia = data_service.get_sharia_compliance(symbol, country)
                    if 'error' not in sharia:
                        ruling = sharia.get('ruling', 'UNCERTAIN')
                        conf = sharia.get('confidence', 0.5) * 100
                        tool_results.append(f"Sharia: {ruling} ({conf:.0f}% confidence)")
                    else:
                        tool_results.append("Sharia: Analysis unavailable")
                
                elif function_name == "compare_time_periods":
                    periods = ["10d", "1mo", "3mo"]
                    comparisons = []
                    for period in periods:
                        analysis = data_service.get_analysis(symbol, period)
                        if 'error' not in analysis:
                            return_pct = analysis.get('total_return_pct', 0)
                            comparisons.append(f"{period}: {return_pct:.2f}%")
                    tool_results.append(f"Period Comparison: {', '.join(comparisons)}")
                
            except Exception as e:
                tool_results.append(f"{function_name}: Error - {str(e)}")
        
        # Generate final response
        final_response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Provide a concise, professional response based on the tool results. Focus on actionable insights."},
                {"role": "user", "content": f"Question: {user_input}\n\nTool Results: {' | '.join(tool_results)}"}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return final_response.choices[0].message.content or "I couldn't generate a response."


# Global instance
ai_assistant = AIAssistant()
