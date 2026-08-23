# tickers is a list of stock tickers
import tickers

# prices is a dict; the key is a ticker and the value is a list of historic prices, today first
import prices

# Trade represents a decision to buy or sell a quantity of a ticker
import Trade

import random
import numpy as np

def trade2():
    # Buy the stock with the highest price today
    ticker = max(prices, key=lambda t: prices[t][0])  # Find ticker with highest price
    return [Trade(ticker, random.randrange(1, 10))]   # Buy a small quantity

def trade3():
    # Sell the stock with the lowest price today
    ticker = min(prices, key=lambda t: prices[t][0])
    return [Trade(ticker, random.randrange(-10, -1))] 

def trade4():
    # Buy the stock with the largest percent increase today
    changes = {t: (prices[t][0] - prices[t][1]) / prices[t][1] for t in prices}
    ticker = max(changes, key=changes.get)
    return [Trade(ticker, random.randrange(1, 10))]

def trade5():
    # Sell the stock with the largest percent decrease today
    changes = {t: (prices[t][0] - prices[t][1]) / prices[t][1] for t in prices}
    ticker = min(changes, key=changes.get)
    return [Trade(ticker, random.randrange(-10, -1))]

def trade6():
    # Buy the 3 stocks with the highest moving average over the last 5 days
    mvgs = {t: np.mean(prices[t][:5]) for t in prices}
    top_tickers = sorted(mvgs, key=mvgs.get, reverse=True)[:3]
    return [Trade(t, random.randrange(1, 5)) for t in top_tickers]

def trade7():
    # Sell the 3 stocks with the lowest moving average over the last 5 days
    mvgs = {t: np.mean(prices[t][:5]) for t in prices}
    bottom_tickers = sorted(mvgs, key=mvgs.get)[:3]
    return [Trade(t, random.randrange(-5, -1)) for t in bottom_tickers]

def trade8():
    # Randomly buy or sell a single stock based on a coin flip
    ticker = random.choice(tickers)
    action = random.choice([-1, 1])  # -1 for sell, 1 for buy
    return [Trade(ticker, action * random.randrange(1, 10))]

def trade9():
    # Diversify: Buy a small amount of 5 random stocks
    chosen_tickers = random.sample(tickers, 5)
    return [Trade(t, random.randrange(1, 3)) for t in chosen_tickers]

def trade10():
    # Follow the trend: If the market is up today, buy, else sell
    market_change = (prices[tickers[0]][0] - prices[tickers[0]][1]) / prices[tickers[0]][1]
    action = 1 if market_change > 0 else -1
    ticker = random.choice(tickers)
    return [Trade(ticker, action * random.randrange(1, 10))]

def trade11():
    # Mean Reversion: Buy the 2 stocks that fell the most yesterday, hoping they rebound
    yesterday_changes = {t: (prices[t][1] - prices[t][2]) / prices[t][2] for t in prices}
    bottom_tickers = sorted(yesterday_changes, key=yesterday_changes.get)[:2]
    return [Trade(t, random.randrange(1, 5)) for t in bottom_tickers]

def trade12():
    # Momentum: Short the 2 stocks that rose the most yesterday, expecting a pullback
    yesterday_changes = {t: (prices[t][1] - prices[t][2]) / prices[t][2] for t in prices}
    top_tickers = sorted(yesterday_changes, key=yesterday_changes.get, reverse=True)[:2]
    return [Trade(t, random.randrange(-5, -1)) for t in top_tickers]

def trade13():
    # Pairs Trading: Long one stock, short another with a similar price history
    correlations = np.corrcoef([prices[t] for t in tickers])
    i, j = np.unravel_index(np.argmax(correlations), correlations.shape)
    return [Trade(tickers[i], 1), Trade(tickers[j], -1)] 

def trade14():
    # Relative Strength: Go long on the strongest stock, short the weakest
    performances = {t: (prices[t][0] - prices[t][-1]) / prices[t][-1] for t in prices}
    strongest = max(performances, key=performances.get)
    weakest = min(performances, key=performances.get)
    return [Trade(strongest, 1), Trade(weakest, -1)]

def trade15():
    # Calendar Spread: Buy this month's option, sell next month's (same strike
    # This is a simplified representation, as actual option trading is more complex
    ticker = random.choice(tickers)
    return [Trade(f"{ticker}_OPT_THIS_MONTH", 1), Trade(f"{ticker}_OPT_NEXT_MONTH", -1)]

def trade16():
    # Straddle: Buy both a call and put option on the same stock (same strike
    ticker = random.choice(tickers)
    strike = prices[ticker][0]  # Use the current price as a simple strike price
    return [Trade(f"{ticker}_CALL_{strike}", 1), Trade(f"{ticker}_PUT_{strike}", 1)]

def trade17():
    # Breakout: Buy if a stock breaks above its 52-week high
    ticker = random.choice(tickers)
    if prices[ticker][0] > max(prices[ticker]):
        return [Trade(ticker, random.randrange(1, 10))]
    else:
        return [] 

def trade18():
    # Volatility: If market volatility is high, sell (expecting it to decrease
    market_volatility = np.std([prices[t][0] / prices[t][1] for t in tickers])
    if market_volatility > 0.05:  # You'd adjust this threshold based on your risk tolerance
        ticker = random.choice(tickers)
        return [Trade(ticker, random.randrange(-10, -1))]
    else:
        return []

def trade19():
    # Golden Cross: Buy if the short-term moving average crosses above the long-term
    ticker = random.choice(tickers)
    short_ma = np.mean(prices[ticker][:5])
    long_ma = np.mean(prices[ticker][:20])
    if short_ma > long_ma and short_ma - long_ma < 0.01:  # Small margin to avoid false signals
        return [Trade(ticker, random.randrange(1, 10))]
    else:
        return []

def trade20():
    # Death Cross: Sell if the short-term moving average crosses below the long-term
    ticker = random.choice(tickers)
    short_ma = np.mean(prices[ticker][:5])
    long_ma = np.mean(prices[ticker][:20])
    if short_ma < long_ma and long_ma - short_ma < 0.01: 
        return [Trade(ticker, random.randrange(-10, -1))]
    else:
        return []

def trade21():
    # Correlated Pairs Buy: Buy a pair of stocks that have historically moved together
    correlations = np.corrcoef([prices[t] for t in tickers])
    i, j = np.unravel_index(np.argmax(correlations), correlations.shape)
    return [Trade(tickers[i], 1), Trade(tickers[j], 1)]

def trade22():
    # Correlated Pairs Sell: Sell a pair of stocks that have historically moved together
    correlations = np.corrcoef([prices[t] for t in tickers])
    i, j = np.unravel_index(np.argmax(correlations), correlations.shape)
    return [Trade(tickers[i], -1), Trade(tickers[j], -1)]

def trade23():
    # Contrarian Pairs Buy: Buy a stock that's down while its correlated pair is up
    correlations = np.corrcoef([prices[t] for t in tickers])
    i, j = np.unravel_index(np.argmax(correlations), correlations.shape)
    if prices[tickers[i]][0] < prices[tickers[i]][1] and prices[tickers[j]][0] > prices[tickers[j]][1]:
        return [Trade(tickers[i], 1)]
    else:
        return []

def trade24():
    # Contrarian Pairs Sell: Sell a stock that's up while its correlated pair is down
    correlations = np.corrcoef([prices[t] for t in tickers])
    i, j = np.unravel_index(np.argmax(correlations), correlations.shape)
    if prices[tickers[i]][0] > prices[tickers[i]][1] and prices[tickers[j]][0] < prices[tickers[j]][1]:
        return [Trade(tickers[i], -1)]
    else:
        return []

def trade25():
    # Correlation Reversal: Buy a stock that's recently become less correlated with the market
    # This is a simplified version, you'd likely use a rolling correlation window
    market_prices = [prices[t] for t in tickers]
    correlations_today = np.corrcoef(market_prices)
    correlations_yesterday = np.corrcoef([p[1:] for p in market_prices])
    diffs = correlations_today - correlations_yesterday
    i, j = np.unravel_index(np.argmin(diffs), diffs.shape)
    if i != j:  # Ensure we're not comparing a stock to itself
        return [Trade(tickers[i], 1)]
    else:
        return []

def trade26():
    # Sector Rotation: Buy the top 2 stocks from the sector that's most correlated with the market
    # Assuming you have sector data (e.g., 'sector_map' dict: ticker -> sector)
    sector_returns = {s: np.mean([(prices[t][0] - prices[t][1]) / prices[t][1] for t in tickers if sector_map[t] == s]) for s in set(sector_map.values())}
    top_sector = max(sector_returns, key=sector_returns.get)
    top_tickers_in_sector = sorted([(t, prices[t][0]) for t in tickers if sector_map[t] == top_sector], key=lambda x: x[1], reverse=True)[:2]
    return [Trade(t, 1) for t, _ in top_tickers_in_sector]

def trade27():
    # Beta-Weighted Portfolio: Allocate more to stocks with higher betas (more volatile
    # You'd need historical market data to calculate betas
    betas = {t: random.uniform(0.5, 2) for t in tickers}  # Placeholder for actual betas
    total_beta = sum(betas.values())
    allocations = {t: betas[t] / total_beta * 100 for t in tickers}
    return [Trade(t, int(allocations[t])) for t in tickers]

def trade28():
    # Diversified Portfolio: Buy a mix of stocks with low correlations to each other
    correlations = np.corrcoef([prices[t] for t in tickers])
    chosen_tickers = []
    while len(chosen_tickers) < 5 and len(tickers) > 0:
        t = random.choice(tickers)
        if all(correlations[tickers.index(t)][tickers.index(c)] < 0.5 for c in chosen_tickers):
            chosen_tickers.append(t)
            tickers.remove(t) 
    return [Trade(t, random.randrange(1, 3)) for t in chosen_tickers]

def trade29():
    # Cointegration: Find a pair of stocks that are cointegrated and trade their spread
    # This requires more complex analysis (e.g., using the Johansen test)
    # For simplicity, we'll just pick a random pair and assume cointegration
    i, j = random.sample(range(len(tickers)), 2)
    spread = prices[tickers[i]][0] - prices[tickers[j]][0]
    if spread > 0:
        return [Trade(tickers[i], -1), Trade(tickers[j], 1)] 
    else:
        return [Trade(tickers[i], 1), Trade(tickers[j], -1)]

def trade30():
    # Basket Trading: Buy or sell a basket of stocks based on their correlation to a benchmark
    # You'd need a benchmark ticker and its historical prices
    benchmark = "SPY"
    correlations = np.corrcoef([prices[t] for t in tickers + [benchmark]])[:-1, -1]  # Correlate each stock with the benchmark
    if np.mean(correlations) > 0.5:
        return [Trade(t, 1) for t in tickers]
    else:
        return [Trade(t, -1) for t in tickers]

def trade31():
    # Double Bottom: Buy when a stock forms a double bottom pattern
    ticker = random.choice(tickers)
    if prices[ticker][0] < prices[ticker][2] < prices[ticker][4] and prices[ticker][1] > prices[ticker][3]:
        return [Trade(ticker, 1)]
    else:
        return []

def trade32():
    # Double Top: Sell when a stock forms a double top pattern
    ticker = random.choice(tickers)
    if prices[ticker][0] > prices[ticker][2] > prices[ticker][4] and prices[ticker][1] < prices[ticker][3]:
        return [Trade(ticker, -1)]
    else:
        return []

def trade33():
    # Head and Shoulders: Sell when a stock forms a head and shoulders pattern
    ticker = random.choice(tickers)
    if prices[ticker][0] < prices[ticker][2] < prices[ticker][4] and prices[ticker][1] > prices[ticker][3] > prices[ticker][5]:
        return [Trade(ticker, -1)]
    else:
        return []

def trade34
    # Inverse Head and Shoulders: Buy when a stock forms an inverse head and shoulders pattern
    ticker = random.choice(tickers)
    if prices[ticker][0] > prices[ticker][2] > prices[ticker][4] and prices[ticker][1] < prices[ticker][3] < prices[ticker][5]:
        return [Trade(ticker, 1)]
    else:
        return []

def trade35():
    # Ascending Triangle: Buy when a stock forms an ascending triangle pattern
    ticker = random.choice(tickers)
    # Simplified logic: check for higher lows and flat highs
    if prices[ticker][0] > prices[ticker][2] > prices[ticker][4] and prices[ticker][1] == prices[ticker][3] == prices[ticker][5]:
        return [Trade(ticker, 1)]
    else:
        return []

def trade36():
    # Descending Triangle: Sell when a stock forms a descending triangle pattern
    ticker = random.choice(tickers)
    # Simplified logic: check for lower highs and flat lows
    if prices[ticker][0] < prices[ticker][2] < prices[ticker][4] and prices[ticker][1] == prices[ticker][3] == prices[ticker][5]:
        return [Trade(ticker, -1)]
    else:
        return []

def trade37():
    # Flag/Pennant: Buy or sell based on the direction of the flag/pennant pattern
    ticker = random.choice(tickers)
    # Simplified logic: check for a consolidation period after a strong move
    if abs(prices[ticker][0] - np.mean(prices[ticker][1:5])) < 0.05 and abs(prices[ticker][5] - prices[ticker][6]) > 0.1:
        # Buy if the prior move was up, sell if down
        return [Trade(ticker, 1 if prices[ticker][5] > prices[ticker][6] else -1)]
    else:
        return []

def trade38():
    # Gap Up: Buy when a stock opens significantly higher than its previous close
    ticker = random.choice(tickers)
    if prices[ticker][0] > prices[ticker][1] * 1.05:  # 5% gap up
        return [Trade(ticker, 1)]
    else:
        return []

def trade39():
    # Gap Down: Sell when a stock opens significantly lower than its previous close
    ticker = random.choice(tickers)
    if prices[ticker][0] < prices[ticker][1] * 0.95:  # 5% gap down
        return [Trade(ticker, -1)]
    else:
        return []

def trade40():
    # Rounding Bottom: Buy when a stock forms a rounding bottom pattern
    ticker = random.choice(tickers)
    # Simplified logic: check for a gradual price increase after a period of decline
    if prices[ticker][0] > prices[ticker][2] > prices[ticker][4] and prices[ticker][1] < prices[ticker][3] < prices[ticker][5]:
        return [Trade(ticker, 1)]
    else:
        return []

def trade41():
    # Overbought/Oversold (RSI): Sell if RSI is above 70, buy if below 30
    ticker = random.choice(tickers)
    rsi = calculate_rsi(prices[ticker], 14)  # Assuming you have an RSI calculation function
    if rsi > 70:
        return [Trade(ticker, -1)]
    elif rsi < 30:
        return [Trade(ticker, 1)]
    else:
        return []

def trade42():
    # Bollinger Bands Breakout: Buy if price breaks above the upper band, sell if below lower
    ticker = random.choice(tickers)
    upper, middle, lower = calculate_bollinger_bands(prices[ticker], 20, 2)  # Assuming you have a Bollinger Band calculation function
    if prices[ticker][0] > upper:
        return [Trade(ticker, 1)]
    elif prices[ticker][0] < lower:
        return [Trade(ticker, -1)]
    else:
        return []

def trade43():
    # Channel Breakout: Buy or sell when price breaks out of a recent price channel
    ticker = random.choice(tickers)
    highs = [max(prices[ticker][i:i+5]) for i in range(len(prices[ticker]) - 5)]
    lows = [min(prices[ticker][i:i+5]) for i in range(len(prices[ticker]) - 5)]
    if prices[ticker][0] > highs[-1]:
        return [Trade(ticker, 1)]
    elif prices[ticker][0] < lows[-1]:
        return [Trade(ticker, -1)]
    else:
        return []

def trade44():
    # Trend Following: Buy if the 20-day moving average is rising, sell if falling
    ticker = random.choice(tickers)
    ma20_today = np.mean(prices[ticker][:20])
    ma20_yesterday = np.mean(prices[ticker][1:21])
    if ma20_today > ma20_yesterday:
        return [Trade(ticker, 1)]
    elif ma20_today < ma20_yesterday:
        return [Trade(ticker, -1)]
    else:
        return []

def trade45():
    # MACD Crossover: Buy when MACD line crosses above signal line, sell when below
    ticker = random.choice(tickers)
    macd_line, signal_line = calculate_macd(prices[ticker])  # Assuming you have a MACD calculation function
    if macd_line[-1] > signal_line[-1] and macd_line[-2] <= signal_line[-2]:
        return [Trade(ticker, 1)]
    elif macd_line[-1] < signal_line[-1] and macd_line[-2] >= signal_line[-2]:
        return [Trade(ticker, -1)]
    else:
        return []

def trade46():
    # Stochastic Oscillator: Buy if %K crosses above %D in oversold zone, sell if opposite
    ticker = random.choice(tickers)
    k_line, d_line = calculate_stochastic(prices[ticker])  # Assuming you have a Stochastic calculation function
    if k_line[-1] > d_line[-1] and k_line[-1] < 20:
        return [Trade(ticker, 1)]
    elif k_line[-1] < d_line[-1] and k_line[-1] > 80:
        return [Trade(ticker, -1)]
    else:
        return []

def trade47():
    # Volume Spike: Buy if today's volume is much higher than the average
    # You'd need volume data for this strategy
    ticker = random.choice(tickers)
    avg_volume = np.mean(volumes[ticker][1:])  # Assuming you have 'volumes' data
    if volumes[ticker][0] > avg_volume * 2:
        return [Trade(ticker, 1)]
    else:
        return []

def trade48():
    # Price Spike: Buy if today's price increase is much higher than average daily change
    ticker = random.choice(tickers)
    daily_changes = [(prices[ticker][i] - prices[ticker][i + 1]) / prices[ticker][i + 1] for i in range(len(prices[ticker]) - 1)]
    avg_change = np.mean(daily_changes)
    today_change = (prices[ticker][0] - prices[ticker][1]) / prices[ticker][1]
    if today_change > avg_change * 2:
        return [Trade(ticker, 1)]
    else:
        return []

def trade49():
    # Mean Reversion (Long-term): Buy if the price is below its 200-day moving average
    ticker = random.choice(tickers)
    ma200 = np.mean(prices[ticker])
    if prices[ticker][0] < ma200:
        return [Trade(ticker, 1)]
    else:
        return []

def trade50():
    # Trend Reversal (Parabolic SAR): Buy or sell based on the Parabolic SAR indicator
    # Assuming you have a Parabolic SAR calculation function
    ticker = random.choice(tickers)
    sar = calculate_parabolic_sar(prices[ticker])
    if prices[ticker][0] > sar[-1]: 
        return [Trade(ticker, 1)]
    elif prices[ticker][0] < sar[-1]:
        return [Trade(ticker, -1)]
    else:
        return []

def trade51():
    # Market Outperformance: Buy stocks whose daily returns beat the market
    total_market_values = [sum(prices[t][i] for t in tickers) for i in range(len(prices[tickers[0]]))]
    market_return = (total_market_values[0] - total_market_values[1]) / total_market_values[1]
    outperformers = [t for t in tickers if (prices[t][0] - prices[t][1]) / prices[t][1] > market_return]
    if outperformers:
        ticker = random.choice(outperformers)
        return [Trade(ticker, 1)]
    else:
        return []

def trade52():
    # Market Underperformance: Short stocks whose daily returns lag the market
    total_market_values = [sum(prices[t][i] for t in tickers) for i in range(len(prices[tickers[0]]))]
    market_return = (total_market_values[0] - total_market_values[1]) / total_market_values[1]
    underperformers = [t for t in tickers if (prices[t][0] - prices[t][1]) / prices[t][1] < market_return]
    if underperformers:
        ticker = random.choice(underperformers)
        return [Trade(ticker, -1)]
    else:
        return []

def trade53():
    # Relative Strength to Market: Buy the stock with the highest relative strength to the market
    total_market_values = [sum(prices[t][i] for t in tickers) for i in range(len(prices[tickers[0]]))]
    market_return = (total_market_values[0] - total_market_values[1]) / total_market_values[1]
    relative_strengths = {t: ((prices[t][0] - prices[t][1]) / prices[t][1]) - market_return for t in tickers}
    ticker = max(relative_strengths, key=relative_strengths.get)
    return [Trade(ticker, 1)]

def trade54():
    # Relative Weakness to Market: Short the stock with the lowest relative strength to the market
    total_market_values = [sum(prices[t][i] for t in tickers) for i in range(len(prices[tickers[0]]))]
    market_return = (total_market_values[0] - total_market_values[1]) / total_market_values[1]
    relative_strengths = {t: ((prices[t][0] - prices[t][1]) / prices[t][1]) - market_return for t in tickers}
    ticker = min(relative_strengths, key=relative_strengths.get)
    return [Trade(ticker, -1)]

def trade55():
    # Sector vs. Market: Buy top stock from sector outperforming the market, short from underperforming
    # Assuming you have sector data (e.g., 'sector_map' dict: ticker -> sector)
    total_market_values = [sum(prices[t][i] for t in tickers) for i in range(len(prices[tickers[0]]))]
    market_return = (total_market_values[0] - total_market_values[1]) / total_market_values[1]
    sector_returns = {s: np.mean([(prices[t][0] - prices[t][1]) / prices[t][1] for t in tickers if sector_map[t] == s]) for s in set(sector_map.values())}
    outperforming_sectors = [s for s in sector_returns if sector_returns[s] > market_return]
    underperforming_sectors = [s for s in sector_returns if sector_returns[s] < market_return]
    trades = []
    if outperforming_sectors:
        top_ticker = max([(t, prices[t][0]) for t in tickers if sector_map[t] == random.choice(outperforming_sectors)], key=lambda x: x[1])[0]
        trades.append(Trade(top_ticker, 1))
    if underperforming_sectors:
        bottom_ticker = min([(t, prices[t][0]) for t in tickers if sector_map[t] == random.choice(underperforming_sectors)], key=lambda x: x[1])[0]
        trades.append(Trade(bottom_ticker, -1))
    return trades

def trade56():
    # Market-Neutral Pairs: Long/short pairs of stocks with similar market betas
    betas = {t: random.uniform(0.8, 1.2) for t in tickers}  # Placeholder, calculate actual betas
    pairs = [(t1, t2) for t1 in tickers for t2 in tickers if abs(betas[t1] - betas[t2]) < 0.1 and t1 != t2]
    if pairs:
        t1, t2 = random.choice(pairs)
        return [Trade(t1, 1), Trade(t2, -1)]
    else:
        return []

def trade57():
    # Beta Rotation: Buy high-beta stocks if the market is rising, low-beta if falling
    total_market_values = [sum(prices[t][i] for t in tickers) for i in range(len(prices[tickers[0]]))]
    market_return = (total_market_values[0] - total_market_values[1]) / total_market_values[1]
    betas = {t: random.uniform(0.5, 2) for t in tickers}  # Placeholder, calculate actual betas
    if market_return > 0:  # Market is rising
        target_beta = 1.5  # Example target for high-beta
    else:
        target_beta = 0.8   # Example target for low-beta
    closest_ticker = min(tickers, key=lambda t: abs(betas[t] - target_beta))
    return [Trade(closest_ticker, 1 if market_return > 0 else -1)]  # Buy if rising, short if falling

def trade58():
    # Market Timing with Relative Strength: Buy strong stocks in up markets, sell in down markets
    total_market_values = [sum(prices[t][i] for t in tickers) for i in range(len(prices[tickers[0]]))]
    market_return = (total_market_values[0] - total_market_values[1]) / total_market_values[1]
    relative_strengths = {t: ((prices[t][0] - prices[t][-1]) / prices[t][-1]) for t in tickers}  # Calculate over a longer period (e.g., 20 days)
    if market_return > 0:
        strongest = max(relative_strengths, key=relative_strengths.get)
        return [Trade(strongest, 1)]
    else:
        weakest = min(relative_strengths, key=relative_strengths.get)
        return [Trade(weakest, -1)]

def trade59():
    # Relative Value to Market: Buy stocks trading below their historical average relative to the market
    # Requires historical data to calculate averages
    total_market_values = [sum(prices[t][i] for t in tickers) for i in range(len(prices[tickers[0]]))]
    relative_values = {t: prices[t][0] / total_market_values[0] for t in tickers}  # Current relative value
    historical_averages = {t: 0.05 for t in tickers}  # Placeholder, calculate actual averages
    undervalued = [t for t in tickers if relative_values[t] < historical_averages[t] * 0.95]  # Allow some buffer
    if undervalued:
        ticker = random.choice(undervalued)
        return [Trade(ticker, 1)]
    else:
        return []

def trade60():
    # Market-Cap Weighted: Allocate trade amounts proportional to each stock's market cap relative to total market
    total_market_value = sum(prices[t][0] for t in tickers)
    market_caps = {t: prices[t][0] * 1000 for t in tickers}  # Assuming 1000 shares outstanding for each stock
    weights = {t: market_caps[t] / total_market_value for t in tickers}
    total_trade_amount = 100  # Example
    trades = [Trade(t, int(weights[t] * total_trade_amount)) for t in tickers]
    return trades