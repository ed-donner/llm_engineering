"""
Sharia Compliance Module

This module provides comprehensive Islamic finance compliance checking
for stocks and investments according to Islamic principles.
"""

import os
import json
import requests
from typing import Dict, List, Optional, Tuple
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import time
import re

# Load environment variables
load_dotenv()

class ShariaComplianceChecker:
    """Enhanced Sharia compliance checker for Islamic investing"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Sharia compliance criteria weights
        self.criteria_weights = {
            'business_activity': 0.40,  # Most important
            'financial_ratios': 0.30,
            'debt_levels': 0.20,
            'revenue_sources': 0.10
        }
        
        # Prohibited business activities (comprehensive list)
        self.prohibited_activities = {
            # Core prohibitions
            'alcohol', 'alcoholic_beverages', 'wine', 'beer', 'spirits', 'liquor',
            'gambling', 'casino', 'lottery', 'betting', 'gaming', 'poker',
            'tobacco', 'cigarettes', 'smoking', 'nicotine',
            'pork', 'pig_farming', 'swine', 'ham', 'bacon',
            'adult_entertainment', 'pornography', 'strip_clubs', 'escort_services',
            
            # Financial prohibitions
            'conventional_banking', 'interest_based_finance', 'usury', 'riba',
            'conventional_insurance', 'life_insurance', 'derivatives_trading',
            'forex_trading', 'currency_speculation', 'margin_trading',
            'short_selling', 'day_trading', 'high_frequency_trading',
            
            # Weapons and defense
            'weapons', 'arms_manufacturing', 'defense_contractors', 'military_equipment',
            'ammunition', 'explosives', 'nuclear_weapons',
            
            # Other prohibitions
            'nightclubs', 'bars', 'entertainment_venues', 'music_industry',
            'film_industry', 'media_entertainment', 'advertising_haram_products'
        }
        
        # Sharia-compliant sectors (generally accepted)
        self.compliant_sectors = {
            'technology', 'healthcare', 'pharmaceuticals', 'telecommunications',
            'utilities', 'real_estate', 'construction', 'manufacturing',
            'retail', 'food_beverages', 'transportation', 'energy_renewable'
        }
        
        # Questionable sectors (need detailed analysis)
        self.questionable_sectors = {
            'financial_services', 'media', 'hotels', 'airlines',
            'oil_gas', 'mining', 'chemicals', 'entertainment',
            'restaurants', 'hospitality', 'advertising'
        }
        
        # AAOIFI and DSN Sharia standards
        self.sharia_standards = {
            'max_debt_to_assets': 0.33,  # 33% maximum debt-to-assets ratio
            'max_interest_income': 0.05,  # 5% maximum interest income
            'max_non_compliant_income': 0.05,  # 5% maximum non-compliant income
            'min_tangible_assets': 0.20  # 20% minimum tangible assets
        }
    
    def _search_company_business_activities(self, company_name: str, symbol: str) -> Dict:
        """
        Search web for company's business activities to verify Sharia compliance
        
        Args:
            company_name: Company name
            symbol: Stock symbol
            
        Returns:
            Dictionary with business activity information
        """
        try:
            # Search query for company business activities
            search_queries = [
                f"{company_name} business activities products services",
                f"{company_name} {symbol} what does company do",
                f"{company_name} revenue sources business model"
            ]
            
            business_info = {
                'activities': [],
                'products': [],
                'services': [],
                'revenue_sources': [],
                'prohibited_found': [],
                'confidence': 0.5
            }
            
            for query in search_queries[:1]:  # Limit to 1 search to avoid rate limits
                try:
                    # Simple web search simulation (in production, use proper search API)
                    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    
                    # For now, return basic analysis based on company name and sector
                    # In production, implement actual web scraping with proper rate limiting
                    business_info['confidence'] = 0.6
                    break
                    
                except Exception as e:
                    print(f"Web search error: {e}")
                    continue
            
            return business_info
            
        except Exception as e:
            print(f"Error in business activity search: {e}")
            return {'activities': [], 'prohibited_found': [], 'confidence': 0.3}
    
    def _estimate_debt_ratio(self, stock_info: Dict) -> float:
        """
        Estimate debt-to-assets ratio based on available information
        
        Args:
            stock_info: Stock information dictionary
            
        Returns:
            Estimated debt-to-assets ratio
        """
        try:
            # In production, this would fetch actual balance sheet data
            # For now, estimate based on sector and other indicators
            sector = stock_info.get('sector', '').lower()
            industry = stock_info.get('industry', '').lower()
            
            # High debt sectors
            if any(x in sector or x in industry for x in ['utility', 'telecom', 'airline', 'real estate']):
                return 0.45  # Typically higher debt
            
            # Medium debt sectors  
            elif any(x in sector or x in industry for x in ['manufacturing', 'retail', 'energy']):
                return 0.25
            
            # Low debt sectors
            elif any(x in sector or x in industry for x in ['technology', 'healthcare', 'software']):
                return 0.15
            
            # Financial sector (different calculation)
            elif 'financial' in sector or 'bank' in sector:
                return 0.8  # Banks have high leverage by nature
            
            # Default estimate
            return 0.3
            
        except Exception:
            return 0.3  # Conservative default
    
    def _check_business_activity(self, stock_info: Dict) -> float:
        """
        Check if the company's primary business activity is Sharia-compliant
        
        Returns:
            Score from 0.0 (non-compliant) to 1.0 (fully compliant)
        """
        sector = stock_info.get('sector', '').lower()
        industry = stock_info.get('industry', '').lower()
        company_name = stock_info.get('company_name', '').lower()
        
        # Check for explicitly prohibited activities
        for prohibited in self.prohibited_activities:
            if (prohibited.replace('_', ' ') in sector or 
                prohibited.replace('_', ' ') in industry or
                prohibited.replace('_', ' ') in company_name):
                return 0.0
        
        # Check for compliant sectors
        for compliant in self.compliant_sectors:
            if (compliant.replace('_', ' ') in sector or 
                compliant.replace('_', ' ') in industry):
                return 1.0
        
        # Check for questionable sectors
        for questionable in self.questionable_sectors:
            if (questionable.replace('_', ' ') in sector or 
                questionable.replace('_', ' ') in industry):
                return 0.5
        
        # Default for unknown sectors
        return 0.7
    
    def check_sharia_compliance(self, symbol: str, stock_info: Dict, analysis: Dict) -> Dict:
        """
        Comprehensive Sharia compliance check
        
        Args:
            symbol: Stock symbol
            stock_info: Stock information
            analysis: Technical analysis results
            
        Returns:
            Dictionary with compliance assessment
        """
        try:
            # Business activity screening
            business_score = self._check_business_activity(stock_info)
            
            # Financial ratios screening
            financial_score = self._check_financial_ratios(stock_info, analysis)
            
            # Debt levels screening
            debt_score = self._check_debt_levels(stock_info)
            
            # Revenue sources screening
            revenue_score = self._check_revenue_sources(stock_info)
            
            # Calculate weighted compliance score
            total_score = (
                business_score * self.criteria_weights['business_activity'] +
                financial_score * self.criteria_weights['financial_ratios'] +
                debt_score * self.criteria_weights['debt_levels'] +
                revenue_score * self.criteria_weights['revenue_sources']
            )
            
            # Get AI-powered detailed analysis
            ai_analysis = self._get_ai_sharia_analysis(symbol, stock_info)
            
            # Determine final ruling
            ruling = self._determine_ruling(total_score, ai_analysis)
            
            return {
                'symbol': symbol,
                'ruling': ruling['status'],
                'confidence': ruling['confidence'],
                'compliance_score': total_score,
                'detailed_scores': {
                    'business_activity': business_score,
                    'financial_ratios': financial_score,
                    'debt_levels': debt_score,
                    'revenue_sources': revenue_score
                },
                'reasoning': ruling['reasoning'],
                'key_concerns': ruling.get('concerns', []),
                'recommendations': ruling.get('recommendations', []),
                'ai_analysis': ai_analysis.get('analysis', ''),
                'scholar_consultation_advised': ruling.get('scholar_consultation', False),
                'alternative_suggestions': ruling.get('alternatives', [])
            }
            
        except Exception as e:
            return {
                'symbol': symbol,
                'ruling': 'UNCERTAIN',
                'confidence': 0.0,
                'reasoning': f'Error in Sharia compliance analysis: {str(e)}',
                'error': str(e)
            }
    
    def _check_business_activity(self, stock_info: Dict) -> float:
        """
        Check if the company's primary business activity is Sharia-compliant
        
        Returns:
            Score from 0.0 (non-compliant) to 1.0 (fully compliant)
        """
        sector = stock_info.get('sector', '').lower()
        industry = stock_info.get('industry', '').lower()
        company_name = stock_info.get('company_name', '').lower()
        
        # Check for explicitly prohibited activities
        for prohibited in self.prohibited_activities:
            if (prohibited.replace('_', ' ') in sector or 
                prohibited.replace('_', ' ') in industry or
                prohibited.replace('_', ' ') in company_name):
                return 0.0
        
        # Check for compliant sectors
        for compliant in self.compliant_sectors:
            if (compliant.replace('_', ' ') in sector or 
                compliant.replace('_', ' ') in industry):
                return 1.0
        
        # Check for questionable sectors
        for questionable in self.questionable_sectors:
            if (questionable.replace('_', ' ') in sector or 
                questionable.replace('_', ' ') in industry):
                return 0.5
        
        # Default for unknown sectors
        return 0.7
    
    def _check_financial_ratios(self, stock_info: Dict, analysis: Dict) -> float:
        """
        Check financial ratios according to AAOIFI and DSN Sharia standards
        
        AAOIFI/DSN Sharia screening ratios:
        - Debt/Total Assets < 33%
        - Interest Income/Total Revenue < 5%
        - Non-compliant Income/Total Revenue < 5%
        - Tangible Assets/Total Assets > 20%
        
        Returns:
            Score from 0.0 to 1.0
        """
        score = 1.0
        penalties = []
        
        try:
            # Get financial metrics (these would come from detailed financial data)
            market_cap = stock_info.get('market_cap', 0)
            pe_ratio = stock_info.get('pe_ratio', 0)
            
            # Debt-to-Assets ratio check
            # Note: In production, fetch actual balance sheet data
            debt_to_assets = self._estimate_debt_ratio(stock_info)
            if debt_to_assets > self.sharia_standards['max_debt_to_assets']:
                penalty = min(0.5, (debt_to_assets - self.sharia_standards['max_debt_to_assets']) * 2)
                score -= penalty
                penalties.append(f"High debt ratio: {debt_to_assets:.1%} > {self.sharia_standards['max_debt_to_assets']:.1%}")
            
            # Interest income check (for financial companies)
            sector = stock_info.get('sector', '').lower()
            if 'financial' in sector or 'bank' in sector:
                # Financial companies likely have significant interest income
                score -= 0.3
                penalties.append("Financial sector - likely high interest income")
            
            # Industry-specific checks
            industry = stock_info.get('industry', '').lower()
            if any(prohibited in industry for prohibited in ['insurance', 'casino', 'alcohol', 'tobacco']):
                score = 0.0
                penalties.append(f"Prohibited industry: {industry}")
            
            return max(0.0, score)
            
        except Exception as e:
            print(f"Error in financial ratio analysis: {e}")
            return 0.5  # Default moderate score if analysis fails
        # For now, we'll use available basic metrics and estimate
        
        # PE ratio check (very high PE might indicate speculation)
        pe_ratio = stock_info.get('pe_ratio', 0)
        if pe_ratio > 50:
            score -= 0.2
        elif pe_ratio > 30:
            score -= 0.1
        
        # Beta check (high beta indicates high speculation/volatility)
        beta = stock_info.get('beta', 1.0)
        if beta > 2.0:
            score -= 0.3
        elif beta > 1.5:
            score -= 0.1
        
        # Volatility check from analysis
        volatility = analysis.get('volatility_annualized', 0)
        if volatility > 60:
            score -= 0.2
        elif volatility > 40:
            score -= 0.1
        
        return max(0.0, score)
    
    def _check_debt_levels(self, stock_info: Dict) -> float:
        """
        Check debt levels according to Sharia standards
        
        Returns:
            Score from 0.0 to 1.0
        """
        # Note: In a real implementation, you would fetch debt-to-assets ratio
        # For now, we'll use sector-based estimation
        
        sector = stock_info.get('sector', '').lower()
        
        # Sectors typically with high debt
        high_debt_sectors = ['utilities', 'real estate', 'telecommunications']
        medium_debt_sectors = ['manufacturing', 'transportation', 'energy']
        low_debt_sectors = ['technology', 'healthcare', 'retail']
        
        if any(s in sector for s in high_debt_sectors):
            return 0.6  # Assume higher debt but may still be acceptable
        elif any(s in sector for s in medium_debt_sectors):
            return 0.8
        elif any(s in sector for s in low_debt_sectors):
            return 1.0
        else:
            return 0.7  # Default assumption
    
    def _check_revenue_sources(self, stock_info: Dict) -> float:
        """
        Check revenue sources for non-compliant income
        
        Returns:
            Score from 0.0 to 1.0
        """
        sector = stock_info.get('sector', '').lower()
        industry = stock_info.get('industry', '').lower()
        
        # Industries with potential non-compliant revenue
        if 'financial' in sector or 'bank' in industry:
            return 0.3  # Banks typically have significant interest income
        elif 'insurance' in industry:
            return 0.2
        elif 'hotel' in industry or 'entertainment' in industry:
            return 0.6  # May have some non-compliant revenue sources
        else:
            return 0.9  # Assume mostly compliant revenue
    
    def _get_ai_sharia_analysis(self, symbol: str, stock_info: Dict) -> Dict:
        """
        Get AI-powered detailed Sharia compliance analysis
        
        Args:
            symbol: Stock symbol
            stock_info: Stock information
            
        Returns:
            Dictionary with AI analysis
        """
        try:
            prompt = f"""
            As an Islamic finance expert, analyze the Sharia compliance of {symbol}.
            
            Company Information:
            - Name: {stock_info.get('company_name', 'N/A')}
            - Sector: {stock_info.get('sector', 'N/A')}
            - Industry: {stock_info.get('industry', 'N/A')}
            - Country: {stock_info.get('country', 'N/A')}
            
            Please analyze according to Islamic finance principles and provide:
            1. Primary business activity assessment
            2. Potential Sharia compliance concerns
            3. Revenue source analysis
            4. Debt and interest exposure concerns
            5. Overall compliance recommendation
            6. Specific areas requiring scholar consultation
            7. Alternative Sharia-compliant investment suggestions
            
            Format your response as JSON:
            {{
                "compliance_status": "HALAL/HARAM/DOUBTFUL",
                "confidence": 85,
                "analysis": "Detailed analysis...",
                "concerns": ["concern1", "concern2"],
                "recommendations": ["rec1", "rec2"],
                "scholar_consultation": true/false,
                "alternatives": ["alt1", "alt2"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in Islamic finance and Sharia compliance for investments."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                if ai_response:
                    return json.loads(ai_response)
                else:
                    return {'analysis': 'No AI response received', 'error': 'Empty response'}
            except json.JSONDecodeError:
                return {'analysis': ai_response, 'parsed_fallback': True}
                
        except Exception as e:
            return {'analysis': f'AI analysis unavailable: {str(e)}', 'error': str(e)}
    
    def _determine_ruling(self, compliance_score: float, ai_analysis: Dict) -> Dict:
        """
        Determine final Sharia compliance ruling
        
        Args:
            compliance_score: Calculated compliance score
            ai_analysis: AI analysis results
            
        Returns:
            Dictionary with final ruling
        """
        # Get AI recommendation if available
        ai_status = ai_analysis.get('compliance_status', 'DOUBTFUL')
        ai_confidence = ai_analysis.get('confidence', 50) / 100
        
        # Combine algorithmic score with AI analysis
        if compliance_score >= 0.8 and ai_status == 'HALAL':
            status = 'HALAL'
            confidence = min(0.9, (compliance_score + ai_confidence) / 2)
            reasoning = "Company appears to be Sharia-compliant based on business activities and financial structure."
        elif compliance_score <= 0.3 or ai_status == 'HARAM':
            status = 'HARAM'
            confidence = max(0.7, (1 - compliance_score + ai_confidence) / 2)
            reasoning = "Company has significant Sharia compliance issues and should be avoided."
        else:
            status = 'DOUBTFUL'
            confidence = 0.6
            reasoning = "Company has mixed compliance indicators. Consultation with Islamic scholars recommended."
        
        return {
            'status': status,
            'confidence': confidence,
            'reasoning': reasoning,
            'concerns': ai_analysis.get('concerns', []),
            'recommendations': ai_analysis.get('recommendations', []),
            'scholar_consultation': ai_analysis.get('scholar_consultation', status == 'DOUBTFUL'),
            'alternatives': ai_analysis.get('alternatives', [])
        }
    
    def get_compliance_summary(self, compliance_result: Dict) -> str:
        """Generate a human-readable compliance summary"""
        if 'error' in compliance_result:
            return f"Compliance Analysis Error: {compliance_result['error']}"
        
        symbol = compliance_result.get('symbol', 'Unknown')
        ruling = compliance_result.get('ruling', 'UNCERTAIN')
        confidence = compliance_result.get('confidence', 0) * 100
        
        summary = [f"Sharia Compliance Analysis for {symbol}"]
        summary.append(f"Ruling: {ruling} (Confidence: {confidence:.0f}%)")
        
        if ruling == 'HALAL':
            summary.append("✅ This investment appears to be permissible under Islamic law.")
        elif ruling == 'HARAM':
            summary.append("❌ This investment should be avoided due to Sharia non-compliance.")
        else:
            summary.append("⚠️ This investment requires further investigation and scholar consultation.")
        
        # Add key concerns if any
        concerns = compliance_result.get('key_concerns', [])
        if concerns:
            summary.append(f"Key Concerns: {', '.join(concerns)}")
        
        # Add recommendations
        recommendations = compliance_result.get('recommendations', [])
        if recommendations:
            summary.append(f"Recommendations: {', '.join(recommendations[:2])}")
        
        return "\n".join(summary)
    
    def get_sharia_alternatives(self, sector: str, country: str = 'USA') -> List[str]:
        """
        Get Sharia-compliant alternatives in the same sector
        
        Args:
            sector: Company sector
            country: Market country
            
        Returns:
            List of alternative stock symbols
        """
        # This would typically connect to a Sharia-compliant stock database
        # For now, return some common Sharia-compliant stocks by sector
        
        alternatives = {
            'technology': ['AAPL', 'MSFT', 'GOOGL', 'META'],
            'healthcare': ['JNJ', 'PFE', 'UNH', 'ABBV'],
            'consumer': ['PG', 'KO', 'PEP', 'WMT'],
            'industrial': ['BA', 'CAT', 'GE', 'MMM']
        }
        
        sector_lower = sector.lower()
        for key, stocks in alternatives.items():
            if key in sector_lower:
                return stocks[:3]  # Return top 3 alternatives
        
        return []

# Global instance for easy import
sharia_checker = ShariaComplianceChecker()

# Convenience function
def check_sharia_compliance(symbol: str, stock_info: Dict, analysis: Dict) -> Dict:
    """Convenience function to check Sharia compliance"""
    return sharia_checker.check_sharia_compliance(symbol, stock_info, analysis)
