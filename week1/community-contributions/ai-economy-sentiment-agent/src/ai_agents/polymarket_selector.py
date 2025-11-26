"""
AI agent for selecting most relevant Polymarket prediction markets
"""

from openai import OpenAI
import json
import re
from typing import Dict, List, Any

from config import (
    OLLAMA_BASE_URL, 
    AI_MODEL, 
    POLYMARKET_FILTER_LIMIT, 
    POLYMARKET_SELECTED_MARKETS,
    AI_TIMEOUT_SECONDS
)
from src.logger import log


def _deduplicate_market_series(markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove repetitive markets from series (e.g., keep only most informative Fed cut counts).
    
    Detects patterns like:
    - "2 Fed rate cuts", "3 Fed rate cuts", "4 Fed rate cuts" → Keep only 1-2 most likely
    - "Trump announces X as Fed Chair" (multiple candidates) → Keep only top 2
    - Multiple recession/GDP markets → Keep most comprehensive
    
    Args:
        markets: List of market dictionaries
    
    Returns:
        Deduplicated list with most informative markets from each series
    """
    if len(markets) <= 5:
        return markets  # Don't deduplicate if we have few markets
    
    deduplicated = []
    skip_indices = set()
    
    # Detect "Fed rate cuts" series (2 cuts, 3 cuts, 4 cuts, etc.)
    fed_cuts_markets = []
    for i, market in enumerate(markets):
        question = market.get('question', '').lower()
        # Match patterns like "2 fed rate cuts", "will 3 fed rate cuts", etc.
        if re.search(r'\d+.*fed.*rate.*cut', question) or re.search(r'fed.*rate.*cut.*\d+', question):
            fed_cuts_markets.append((i, market))
    
    if len(fed_cuts_markets) >= 3:
        # Keep only the most informative: highest probability + one more for context
        fed_cuts_sorted = sorted(fed_cuts_markets, key=lambda x: x[1].get('probability', 0), reverse=True)
        keep_top_2 = [fed_cuts_sorted[0], fed_cuts_sorted[1]] if len(fed_cuts_sorted) > 1 else fed_cuts_sorted
        
        # Mark others for removal
        for idx, market in fed_cuts_markets:
            if (idx, market) not in keep_top_2:
                skip_indices.add(idx)
        
        print(f"  [SERIES] Fed rate cuts: Found {len(fed_cuts_markets)} markets, keeping 2 most informative")
    
    # Detect "Fed Chair candidate" series (multiple Trump announcement markets)
    fed_chair_markets = []
    for i, market in enumerate(markets):
        question = market.get('question', '').lower()
        if 'trump' in question and 'fed chair' in question and 'announce' in question:
            fed_chair_markets.append((i, market))
    
    if len(fed_chair_markets) >= 3:
        # Keep only top 2 most likely candidates
        fed_chair_sorted = sorted(fed_chair_markets, key=lambda x: x[1].get('probability', 0), reverse=True)
        keep_top_2 = [fed_chair_sorted[0], fed_chair_sorted[1]] if len(fed_chair_sorted) > 1 else fed_chair_sorted
        
        for idx, market in fed_chair_markets:
            if (idx, market) not in keep_top_2:
                skip_indices.add(idx)
        
        print(f"  [SERIES] Fed Chair candidates: Found {len(fed_chair_markets)} markets, keeping 2 most likely")
    
    # Detect recession/GDP series (multiple overlapping recession markets)
    recession_markets = []
    for i, market in enumerate(markets):
        question = market.get('question', '').lower()
        if ('recession' in question or 'negative gdp' in question or 'gdp contraction' in question):
            recession_markets.append((i, market))
    
    if len(recession_markets) >= 4:
        # Keep only 2: general recession + most specific GDP metric
        # Prioritize: "recession in 2025" > "negative GDP 2025" > quarterly metrics
        general_recession = None
        gdp_annual = None
        
        for idx, market in recession_markets:
            question = market.get('question', '').lower()
            if 'recession' in question and '2025' in question and 'q' not in question:
                if general_recession is None:
                    general_recession = (idx, market)
            elif 'gdp' in question and '2025' in question and 'q' not in question:
                if gdp_annual is None:
                    gdp_annual = (idx, market)
        
        keep_markets = []
        if general_recession:
            keep_markets.append(general_recession)
        if gdp_annual:
            keep_markets.append(gdp_annual)
        
        if len(keep_markets) >= 2:
            for idx, market in recession_markets:
                if (idx, market) not in keep_markets:
                    skip_indices.add(idx)
            
            print(f"  [SERIES] Recession/GDP: Found {len(recession_markets)} markets, keeping 2 most general")
    
    # Build deduplicated list
    for i, market in enumerate(markets):
        if i not in skip_indices:
            deduplicated.append(market)
    
    return deduplicated


def select_relevant_polymarkets(markets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Use AI to select the most relevant Polymarket prediction markets for economic analysis.
    
    Args:
        markets: List of raw market data from Polymarket API
    
    Returns:
        Dict containing AI-selected markets with relevance explanations
    """
    try:
        if not markets:
            return {'selected_markets': [], 'note': 'No markets to analyze'}
        
        # AGGRESSIVE PRE-FILTERING: Remove non-economic markets BEFORE sending to AI
        # The AI was selecting sports, crypto, and AI topics - we need hard filters
        relevant_markets = []
        closed_count = 0
        archived_count = 0
        filtered_non_economic = 0
        
        # Keywords that indicate NON-ECONOMIC markets (reject these)
        # BE VERY AGGRESSIVE - better to filter too much than let garbage through
        NON_ECONOMIC_KEYWORDS = [
            # Sports - General
            'nfl', 'nba', 'mlb', 'nhl', 'soccer', 'football', 'basketball', 'baseball',
            'formula 1', 'f1', 'racing', 'mercedes', 'verstappen', 'championship',
            'super bowl', 'world series', 'playoffs', 'olympics', 'premier league',
            'match', 'draw', 'game', 'score', 'team', 'player', 'athlete',
            'champion', 'tournament', 'league', 'cup', 'bowl',
            'arch', 'wnba', 'ufc', 'boxing', 'tennis', 'golf', 'hockey',
            
            # AI/Tech companies (individual companies, not economic indicators)
            'chatgpt', 'openai', 'claude', 'gemini', 'gpt-4', 'gpt-5', 'gpt-6',
            'nvidia stock', 'apple stock', 'tesla stock', 'meta stock', 'amazon stock',
            'spacex', 'starship', 'anthropic', 'midjourney', 'dall-e',
            'agi', 'superintelligence', 'sam altman', 'elon musk',
            
            # Crypto/Blockchain (not economic policy)
            'ethereum', 'bitcoin', 'crypto', 'blockchain', 'solana', 'cardano',
            'fusaka', 'eth 2.0', 'btc', 'eth', 'defi', 'nft', 'web3',
            'usdt', 'usdc', 'tether', 'depeg', 'stablecoin', 'altcoin',
            'binance', 'coinbase', 'metamask', 'wallet',
            
            # Entertainment/Celebrities
            'taylor swift', 'kardashian', 'movie', 'oscar', 'grammy', 'emmy',
            'album', 'concert', 'tour', 'celebrity', 'actor', 'actress',
            'netflix', 'disney', 'marvel', 'star wars', 'game of thrones',
            
            # Climate (not economic)
            'temperature', 'hurricane', 'wildfire', 'weather', 'climate change',
            'sea level', 'rainfall', 'drought',
            
            # Politics (scandals/legal cases, NOT election outcomes which affect policy)
            'trump convicted', 'trump arrested', 'trump indicted', 'trump sentenced',
            'biden hospitalized', 'biden health crisis', 'biden resigns',
            'harris resigns', 'desantis arrested', 'scandal',
            'impeachment', 'verdict', 'jury decision', 'sentencing',
            # Note: "trump wins", "harris wins" are ALLOWED - they affect economic policy
            
            # Technology products (not economic indicators)
            'iphone', 'ipad', 'apple watch', 'ps5', 'xbox', 'nintendo',
            'cybertruck', 'model 3', 'model y',
            
            # Social media
            'tiktok ban', 'twitter', 'facebook', 'instagram', 'youtube',
            
            # Gaming/Esports
            'video game', 'esports', 'gamer', 'gaming', 'streamer', 'twitch',
            'fortnite', 'call of duty', 'gta', 'minecraft', 'league of legends',
            'world of warcraft', 'valorant', 'counter-strike',
            
            # Science/Space (not economic indicators)
            'mars mission', 'moon landing', 'jwst', 'james webb', 'spacex mission',
            'rocket launch', 'space station', 'satellite launch', 'artemis',
            'cern', 'particle physics', 'black hole',
            
            # Medical/Health (individual breakthroughs, not economic crises)
            'cancer cure', 'longevity escape velocity', 'life extension',
            'drug approval', 'clinical trial breakthrough', 'aging reversed',
            
            # Other non-economic
            'uap', 'ufo', 'alien', 'nuclear war', 'world war',
            'pandemic', 'covid', 'vaccine', 'virus'
        ]
        
        # Keywords that indicate ECONOMIC markets (keep these)
        ECONOMIC_KEYWORDS = [
            # Fed/Monetary Policy (US)
            'federal reserve', 'fed rate', 'interest rate', 'fomc', 'fed cut',
            'fed hike', 'fed chair', 'powell', 'monetary policy', 'fed meeting',
            
            # International Central Banks
            'ecb', 'european central bank', 'boe', 'bank of england',
            'boj', 'bank of japan', 'pboc', 'people\'s bank of china',
            'currency crisis', 'euro crisis', 'exchange rate', 'forex',
            
            # Economic Indicators
            'recession', 'gdp', 'unemployment', 'inflation', 'cpi', 'ppi',
            'jobs report', 'payroll', 'economic growth', 'economic contraction',
            
            # Labor Market (Expanded)
            'wage growth', 'hourly earnings', 'jobless claims', 'unemployment claims',
            'job openings', 'jolts', 'labor force participation', 'hiring',
            'layoffs', 'unemployment rate',
            
            # Housing Market
            'housing starts', 'building permits', 'home sales', 'existing home sales',
            'new home sales', 'mortgage rate', 'housing market', 'real estate market',
            'home prices', 'housing bubble',
            
            # Consumer Indicators
            'consumer confidence', 'consumer sentiment', 'retail sales',
            'consumer spending', 'personal consumption', 'disposable income',
            
            # Manufacturing/Industrial
            'pmi', 'purchasing managers index', 'ism manufacturing', 'ism services',
            'factory orders', 'industrial production', 'capacity utilization',
            'durable goods', 'manufacturing output',
            
            # Markets/Financial
            'stock market', 's&p 500', 's&p 500', 'dow jones', 'nasdaq', 'market crash',
            'circuit breaker', 'trading halt', 'bear market', 'bull market',
            'market correction', 'volatility index', 'vix',
            
            # Treasury/Bonds
            'treasury', 'bond yield', 'yield curve', 'treasury yield',
            '10-year treasury', '2-year treasury',
            
            # Energy (as economic indicator)
            'oil price', 'crude oil', 'gas price', 'gasoline price', 'energy prices',
            'opec', 'oil production', 'natural gas price',
            
            # Trade/International Economics
            'trade deficit', 'trade surplus', 'exports', 'imports', 'trade balance',
            'current account', 'trade war', 'tariff',
            
            # Economic Policy
            'tax policy', 'tax cut', 'tax increase', 'stimulus', 'government spending',
            'debt ceiling', 'budget deficit', 'fiscal policy', 'government shutdown',
            
            # Banking/Credit
            'bank failure', 'credit crunch', 'financial crisis', 'banking crisis',
            'credit spread', 'credit conditions'
        ]
        
        for market in markets:
            # Skip closed markets
            if market.get('closed', False):
                closed_count += 1
                continue
            
            # Skip archived markets
            if market.get('archived', False):
                archived_count += 1
                continue
            
            # PRE-FILTER: Check if market is economic-related
            question = market.get('question', '').lower()
            
            # Reject if contains non-economic keywords
            is_non_economic = any(keyword in question for keyword in NON_ECONOMIC_KEYWORDS)
            if is_non_economic:
                filtered_non_economic += 1
                continue
            
            # STRICT RULE: Must contain economic keywords to pass
            # Don't be lenient - if it doesn't match economic keywords, reject it
            is_economic = any(keyword in question for keyword in ECONOMIC_KEYWORDS)
            
            # Only accept if explicitly economic
            if not is_economic:
                filtered_non_economic += 1
                continue
            
            # Extract probability - Gamma API uses 'outcomePrices' array
            probability = None
            outcomes_list = []
            
            # Gamma API format: outcomePrices and outcomes are JSON strings, not arrays!
            outcome_prices_raw = market.get('outcomePrices', [])
            outcomes_raw = market.get('outcomes', [])
            
            # Parse JSON strings if needed
            outcome_prices = outcome_prices_raw
            outcomes = outcomes_raw
            
            if isinstance(outcome_prices_raw, str):
                try:
                    outcome_prices = json.loads(outcome_prices_raw)
                except json.JSONDecodeError:
                    outcome_prices = []
            
            if isinstance(outcomes_raw, str):
                try:
                    outcomes = json.loads(outcomes_raw)
                except json.JSONDecodeError:
                    outcomes = []
            
            if outcome_prices and len(outcome_prices) > 0:
                try:
                    # outcomePrices might be strings - convert to float
                    first_price = outcome_prices[0]
                    if isinstance(first_price, str):
                        # Remove any whitespace
                        first_price = first_price.strip()
                    probability = float(first_price)
                    
                    # For multi-outcome markets, capture all outcomes
                    if len(outcomes) > 2:
                        for i, outcome in enumerate(outcomes):
                            if i < len(outcome_prices):
                                try:
                                    price_val = float(str(outcome_prices[i]).strip())
                                    outcomes_list.append({
                                        'outcome': outcome,
                                        'probability': price_val
                                    })
                                except (ValueError, TypeError):
                                    pass
                except (ValueError, TypeError, IndexError, AttributeError) as e:
                    # Debug: what went wrong?
                    if len(relevant_markets) == 0:
                        print(f"          [ERROR] Failed to parse probability: {e}")
                        print(f"          outcomePrices type: {type(outcome_prices)}, value: {outcome_prices}")
                        print(f"          First element type: {type(outcome_prices[0]) if outcome_prices else 'N/A'}")
            
            # Fallback: Try other possible locations
            if probability is None:
                tokens = market.get('tokens', [])
                if tokens and len(tokens) > 0:
                    price = tokens[0].get('price')
                    if price is not None:
                        try:
                            probability = float(price)
                        except (ValueError, TypeError):
                            pass
            
            market_data = {
                'question': market.get('question', 'Unknown'),
                'probability': probability
            }
            
            # Add outcomes for multi-outcome markets
            if outcomes_list:
                market_data['outcomes'] = outcomes_list
            
            relevant_markets.append(market_data)
            
            # Debug: Show first 3 markets with structure info
            if len(relevant_markets) <= 3:
                log.verbose(f"  [DEBUG] Market {len(relevant_markets)}: {market_data['question'][:60]}...")
                log.verbose(f"          Probability: {probability}")
                if outcome_prices:
                    log.verbose(f"          outcomePrices: {outcome_prices}")
                    log.verbose(f"          outcomes: {outcomes}")
                if outcomes_list:
                    log.verbose(f"          Multi-outcome market with {len(outcomes_list)} options:")
                    for outcome in outcomes_list[:3]:
                        log.verbose(f"            - {outcome['outcome']}: {outcome['probability']*100:.1f}%")
            
            # Stop after finding enough economic markets
            # Limit to 50 max to avoid overwhelming the AI model
            if len(relevant_markets) >= min(POLYMARKET_FILTER_LIMIT, 50):
                break
        
        log.verbose(f"  Found {len(markets)} total markets")
        log.verbose(f"    - Closed: {closed_count}")
        log.verbose(f"    - Archived: {archived_count}")
        log.verbose(f"    - Filtered (non-economic): {filtered_non_economic}")
        log.normal(f"  Economic markets for AI: {len(relevant_markets)}")
        
        if not relevant_markets:
            log.error(f"[WARN] No economic markets found after filtering {len(markets)} total markets")
            
            return {
                'selected_markets': [],
                'note': f'No economic markets found. Polymarket may not have active Fed/recession/inflation markets right now.',
                'stats': {
                    'total_markets': len(markets),
                    'closed': closed_count,
                    'archived': archived_count,
                    'filtered_non_economic': filtered_non_economic,
                    'economic': 0
                },
                'suggestion': 'This is common if there are no major upcoming Fed decisions or economic events. The analysis can continue without Polymarket data.'
            }
        
        simplified_markets = relevant_markets
        log.verbose(f"\n{'='*60}")
        log.verbose(f"POLYMARKET PRE-FILTERING RESULTS")
        log.verbose(f"{'='*60}")
        log.verbose(f"Total markets from API: {len(markets)}")
        log.verbose(f"  - Closed: {closed_count}")
        log.verbose(f"  - Archived: {archived_count}")
        log.verbose(f"  - Non-economic (filtered): {filtered_non_economic}")
        log.verbose(f"  - Economic markets for AI: {len(simplified_markets)}")
        log.verbose(f"{'='*60}\n")
        
        # Show sample of what we're sending to AI
        if simplified_markets:
            log.verbose(f"Sample economic markets being sent to AI:")
            for i, m in enumerate(simplified_markets[:5]):
                log.verbose(f"  {i+1}. {m['question'][:80]}...")
            if len(simplified_markets) > 5:
                log.verbose(f"  ... and {len(simplified_markets) - 5} more")
            log.verbose("")
        
        # Use AI to select most relevant markets
        client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
        
        log.normal(f"\nAI selecting {POLYMARKET_SELECTED_MARKETS} most relevant markets from {len(simplified_markets)} candidates...")
        log.verbose(f"[INFO] AI Model: {AI_MODEL}")
        
        # OPTIMIZE PAYLOAD: Send only question + probability (not full market objects)
        # This reduces token count by 80%+
        optimized_markets = [
            {
                'question': m['question'],
                'probability': m.get('probability')
            }
            for m in simplified_markets
        ]
        
        markets_json = json.dumps(optimized_markets, indent=2)
        log.verbose(f"[INFO] Optimized payload size: {len(markets_json)} characters")
        
        try:
            ai_response = client.chat.completions.create(
                model=AI_MODEL,
                timeout=float(AI_TIMEOUT_SECONDS),
                messages=[
                    {
                        "role": "system",
                        "content": """You are a STRICT economic data analyst. Your ONLY job is to select prediction markets about MACROECONOMIC indicators and MONETARY POLICY.

=== MUST SELECT (Priority Order) ===
1. Federal Reserve policy (rate cuts, rate hikes, FOMC decisions, Fed chair)
2. Recession probability or GDP growth
3. Inflation measures (CPI, PPI, core inflation)
4. Employment data (unemployment rate, jobs reports)
5. Treasury bond yields
6. Stock market crashes or circuit breakers
7. Economic policy (tariffs, trade, fiscal stimulus)
8. Banking/financial crises

=== ABSOLUTELY FORBIDDEN - REJECT IMMEDIATELY ===
❌ Sports/Games (NFL, NBA, F1, racing, "match", "draw", "game", "ARCH", "team")
❌ Individual company stocks (Tesla, NVIDIA, Apple, Microsoft)
❌ Cryptocurrency tech (Ethereum upgrades, Bitcoin tech, USDT, depegs, stablecoins)
❌ AI products (ChatGPT users, GPT-5 release, AGI predictions)
❌ Entertainment (movies, celebrities, awards)
❌ Climate events (temperature, hurricanes)
❌ Individual politicians (unless about economic policy they'll implement)
❌ Technology products (iPhone, PS5, Cybertruck)

EXAMPLES OF BAD MARKETS TO REJECT:
- "ARCH Will the match be a draw?" - SPORTS, REJECT
- "USDT depeg in 2025?" - CRYPTO TECH, REJECT
- "ChatGPT reach 1B users?" - AI PRODUCT, REJECT
- "Will Mercedes finish second?" - SPORTS, REJECT
- "Will Ethereum upgrade implement?" - CRYPTO TECH, REJECT

CRITICAL: If you select ANY sports, crypto tech, AI products, or entertainment markets, you have FAILED.
Only select Fed policy, recession, inflation, unemployment, or major market crash predictions.

Your response must be PURE macroeconomic indicators only. When in doubt, DON'T select it.

Return ONLY valid JSON. No explanations."""
                    },
                    {
                        "role": "user",
                        "content": f"""From this pre-filtered list of economic markets, select the {POLYMARKET_SELECTED_MARKETS} MOST IMPORTANT for understanding:
1. Federal Reserve policy direction
2. Recession risk
3. Inflation trends
4. Employment health

Markets list:
{markets_json}

REMINDER: Reject ALL non-economic markets. Only select Fed policy, recession, inflation, unemployment, or financial crisis markets.

Return this exact JSON format:
{{
  "selected_markets": [
    {{
      "question": "exact question from list",
      "probability": exact_number_from_list,
      "relevance": "economic relevance in 10 words max"
    }}
  ]
}}"""
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            ai_content = ai_response.choices[0].message.content.strip()
            
            # Debug output
            log.verbose(f"[DEBUG] Raw AI response (first 500 chars):")
            log.verbose(ai_content[:500])
            log.verbose("")
            
            result = json.loads(ai_content)
            
            # Debug parsed result
            log.verbose(f"[DEBUG] Parsed result keys: {result.keys() if result else 'None'}")
            if result and 'selected_markets' in result:
                log.verbose(f"[DEBUG] Number of selected markets: {len(result['selected_markets'])}")
                
                # POST-VALIDATION: Remove any non-economic markets that slipped through
                validated_markets = []
                rejected_markets = []
                
                for market in result['selected_markets']:
                    question = market.get('question', '').lower()
                    
                    # Check against our non-economic keywords
                    is_bad = any(keyword in question for keyword in [
                        # Sports
                        'f1', 'nfl', 'nba', 'mlb', 'nhl', 'racing', 'championship', 'mercedes', 'verstappen',
                        'match', 'draw', 'game', 'score', 'arch', 'team', 'player', 'tournament',
                        # AI Products
                        'chatgpt', 'gpt-5', 'gpt-6', 'openai', 'claude', 'agi', 'sam altman',
                        # Crypto Tech
                        'ethereum', 'bitcoin', 'crypto', 'fusaka', 'btc', 'eth', 'usdt', 'usdc',
                        'depeg', 'stablecoin', 'defi', 'nft', 'blockchain',
                        # Entertainment
                        'sports', 'taylor swift', 'kardashian', 'movie', 'album', 'netflix',
                        # Tech Products
                        'iphone', 'spacex', 'starship', 'cybertruck', 'elon musk'
                    ])
                    
                    if is_bad:
                        rejected_markets.append(market['question'])
                        log.verbose(f"[REJECTED] Non-economic: {market['question'][:60]}...")
                    else:
                        validated_markets.append(market)
                
                # DEDUPLICATION: Remove repetitive markets from series
                deduplicated_markets = _deduplicate_market_series(validated_markets)
                
                if len(deduplicated_markets) < len(validated_markets):
                    removed = len(validated_markets) - len(deduplicated_markets)
                    log.normal(f"[DEDUP] Removed {removed} repetitive markets, kept {len(deduplicated_markets)}")
                
                validated_markets = deduplicated_markets
                
                if rejected_markets:
                    log.error(f"⚠️  WARNING: AI selected {len(rejected_markets)} non-economic markets (rejected)")
                    for q in rejected_markets:
                        log.verbose(f"    - {q[:80]}")
                
                # Update result with validated markets only
                result['selected_markets'] = validated_markets
                
                if not validated_markets:
                    log.error(f"❌ ERROR: All AI-selected markets were non-economic!")
                    return {
                        'selected_markets': [],
                        'note': 'AI selected only non-economic markets (sports, crypto, etc). Need better market data.'
                    }
        
        except json.JSONDecodeError as e:
            log.error(f"[ERROR] JSON parsing failed: {str(e)}")
            log.verbose(f"[DEBUG] Failed content: {ai_content[:200] if 'ai_content' in locals() else 'N/A'}")
            result = {'selected_markets': []}
        except Exception as e:
            log.error(f"[ERROR] AI request failed: {str(e)}")
            result = {'selected_markets': []}
        
        # Validate results
        if not result or 'selected_markets' not in result or not result.get('selected_markets'):
            log.error(f"[WARN] No markets selected")
            return {
                'selected_markets': [],
                'note': 'No relevant predictions found'
            }
        
        selected = result['selected_markets']
        log.normal(f"✓ Selected {len(selected)} Polymarket predictions\n")
        return {'selected_markets': selected}
            
    except TimeoutError:
        print(f"[WARN] Polymarket AI Selection: Request timed out after 60 seconds")
        return {
            'error': 'AI request timed out',
            'note': 'Model took too long to respond - try reducing market count or using a faster model'
        }
    except json.JSONDecodeError as e:
        print(f"[WARN] Polymarket AI Selection: JSON parsing error - {str(e)[:50]}")
        return {
            'error': f'AI response parsing failed',
            'note': 'Could not parse AI selection'
        }
    except Exception as e:
        error_msg = str(e)
        print(f"[WARN] Polymarket AI Selection: Error - {error_msg[:80]}")
        
        # Check if it's a timeout-related error
        if 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
            return {
                'error': 'Request timed out',
                'note': 'AI model took too long - try a faster model or reduce data size'
            }
        
        return {
            'error': error_msg[:80],
            'note': 'AI selection failed'
        }

