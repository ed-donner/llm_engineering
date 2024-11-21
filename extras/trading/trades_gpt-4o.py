# tickers is a list of stock tickers
import tickers

# prices is a dict; the key is a ticker and the value is a list of historic prices, today first
import prices

# Trade represents a decision to buy or sell a quantity of a ticker
import Trade

import random
import numpy as np

def trade2():
    # Buy top performing stock in the last 5 days
    avg_prices = {ticker: np.mean(prices[ticker][:5]) for ticker in tickers}
    best_ticker = max(avg_prices, key=avg_prices.get)
    trade = Trade(best_ticker, 100)
    return [trade]

def trade3():
    # Sell worst performing stock in the last 5 days
    avg_prices = {ticker: np.mean(prices[ticker][:5]) for ticker in tickers}
    worst_ticker = min(avg_prices, key=avg_prices.get)
    trade = Trade(worst_ticker, -100)
    return [trade]

def trade4():
    # Buy random stock from top 5 performing in the last 10 days
    avg_prices = {ticker: np.mean(prices[ticker][:10]) for ticker in tickers}
    top_5_tickers = sorted(avg_prices, key=avg_prices.get, reverse=True)[:5]
    ticker = random.choice(top_5_tickers)
    trade = Trade(ticker, 100)
    return [trade]

def trade5():
    # Sell random stock from bottom 5 performing in the last 10 days
    avg_prices = {ticker: np.mean(prices[ticker][:10]) for ticker in tickers}
    bottom_5_tickers = sorted(avg_prices, key=avg_prices.get)[:5]
    ticker = random.choice(bottom_5_tickers)
    trade = Trade(ticker, -100)
    return [trade]

def trade6():
    # Buy stocks with a positive trend over the last 7 days
    trending_up = [ticker for ticker in tickers if prices[ticker][0] > prices[ticker][6]]
    ticker = random.choice(trending_up)
    trade = Trade(ticker, 100)
    return [trade]

def trade7():
    # Sell stocks with a negative trend over the last 7 days
    trending_down = [ticker for ticker in tickers if prices[ticker][0] < prices[ticker][6]]
    ticker = random.choice(trending_down)
    trade = Trade(ticker, -100)
    return [trade]

def trade8():
    # Buy stocks with the lowest volatility over the last 20 days
    volatilities = {ticker: np.std(prices[ticker][:20]) for ticker in tickers}
    least_volatile = min(volatilities, key=volatilities.get)
    trade = Trade(least_volatile, 100)
    return [trade]

def trade9():
    # Sell stocks with the highest volatility over the last 20 days
    volatilities = {ticker: np.std(prices[ticker][:20]) for ticker in tickers}
    most_volatile = max(volatilities, key=volatilities.get)
    trade = Trade(most_volatile, -100)
    return [trade]

def trade10():
    # Random mixed strategy: randomly buy or sell a random stock
    ticker = random.choice(tickers)
    quantity = random.choice([-100, 100])
    trade = Trade(ticker, quantity)
    return [trade]

def trade11():
    # Buy the top 3 performing stocks in the last 15 days
    avg_prices = {ticker: np.mean(prices[ticker][:15]) for ticker in tickers}
    top_3_tickers = sorted(avg_prices, key=avg_prices.get, reverse=True)[:3]
    trades = [Trade(ticker, 100) for ticker in top_3_tickers]
    return trades

def trade12():
    # Sell the bottom 3 performing stocks in the last 15 days
    avg_prices = {ticker: np.mean(prices[ticker][:15]) for ticker in tickers}
    bottom_3_tickers = sorted(avg_prices, key=avg_prices.get)[:3]
    trades = [Trade(ticker, -100) for ticker in bottom_3_tickers]
    return trades

def trade13():
    # Buy 2 random stocks with the highest increase in price in the last 10 days
    price_increases = {ticker: prices[ticker][0] - prices[ticker][9] for ticker in tickers}
    top_2_increases = sorted(price_increases, key=price_increases.get, reverse=True)[:2]
    trades = [Trade(ticker, 100) for ticker in top_2_increases]
    return trades

def trade14():
    # Sell 2 random stocks with the highest decrease in price in the last 10 days
    price_decreases = {ticker: prices[ticker][0] - prices[ticker][9] for ticker in tickers}
    top_2_decreases = sorted(price_decreases, key=price_decreases.get)[:2]
    trades = [Trade(ticker, -100) for ticker in top_2_decreases]
    return trades

def trade15():
    # Buy stocks that have shown the highest volatility in the last 30 days
    volatilities = {ticker: np.std(prices[ticker][:30]) for ticker in tickers}
    high_volatility_tickers = sorted(volatilities, key=volatilities.get, reverse=True)[:3]
    trades = [Trade(ticker, 100) for ticker in high_volatility_tickers]
    return trades

def trade16():
    # Sell stocks that have shown the lowest volatility in the last 30 days
    volatilities = {ticker: np.std(prices[ticker][:30]) for ticker in tickers}
    low_volatility_tickers = sorted(volatilities, key=volatilities.get)[:3]
    trades = [Trade(ticker, -100) for ticker in low_volatility_tickers]
    return trades

def trade17():
    # Buy stocks with prices above their 50-day moving average
    ma_50 = {ticker: np.mean(prices[ticker][:50]) for ticker in tickers}
    above_ma_tickers = [ticker for ticker in tickers if prices[ticker][0] > ma_50[ticker]]
    trades = [Trade(ticker, 100) for ticker in random.sample(above_ma_tickers, min(3, len(above_ma_tickers)))]
    return trades

def trade18():
    # Sell stocks with prices below their 50-day moving average
    ma_50 = {ticker: np.mean(prices[ticker][:50]) for ticker in tickers}
    below_ma_tickers = [ticker for ticker in tickers if prices[ticker][0] < ma_50[ticker]]
    trades = [Trade(ticker, -100) for ticker in random.sample(below_ma_tickers, min(3, len(below_ma_tickers)))]
    return trades

def trade19():
    # Mixed strategy: buy 2 random stocks and sell 2 random stocks
    buy_tickers = random.sample(tickers, 2)
    sell_tickers = random.sample([ticker for ticker in tickers if ticker not in buy_tickers], 2)
    trades = [Trade(ticker, 100) for ticker in buy_tickers] + [Trade(ticker, -100) for ticker in sell_tickers]
    return trades

def trade20():
    # Buy stocks that have positive return in the last 20 days and sell those with negative return
    returns = {ticker: (prices[ticker][0] - prices[ticker][19]) / prices[ticker][19] for ticker in tickers}
    buy_tickers = [ticker for ticker in tickers if returns[ticker] > 0]
    sell_tickers = [ticker for ticker in tickers if returns[ticker] < 0]
    trades = [Trade(ticker, 100) for ticker in random.sample(buy_tickers, min(2, len(buy_tickers)))] + \
             [Trade(ticker, -100) for ticker in random.sample(sell_tickers, min(2, len(sell_tickers)))]
    return trades

def trade21():
    # Buy the top performing stock in the last 3 days
    avg_prices = {ticker: np.mean(prices[ticker][:3]) for ticker in tickers}
    best_ticker = max(avg_prices, key=avg_prices.get)
    trade = Trade(best_ticker, 100)
    return [trade]

def trade22():
    # Sell the worst performing stock in the last 3 days
    avg_prices = {ticker: np.mean(prices[ticker][:3]) for ticker in tickers}
    worst_ticker = min(avg_prices, key=avg_prices.get)
    trade = Trade(worst_ticker, -100)
    return [trade]

def trade23():
    # Buy stocks that have not changed price in the last 7 days
    stable_tickers = [ticker for ticker in tickers if prices[ticker][0] == prices[ticker][6]]
    trades = [Trade(ticker, 100) for ticker in random.sample(stable_tickers, min(3, len(stable_tickers)))]
    return trades

def trade24():
    # Sell stocks that have the smallest price change in the last 5 days
    smallest_changes = sorted(tickers, key=lambda t: abs(prices[t][0] - prices[t][4]))[:3]
    trades = [Trade(ticker, -100) for ticker in smallest_changes]
    return trades

def trade25():
    # Buy random stocks from the top 10 highest priced stocks
    highest_priced = sorted(tickers, key=lambda t: prices[t][0], reverse=True)[:10]
    ticker = random.choice(highest_priced)
    trade = Trade(ticker, 100)
    return [trade]

def trade26():
    # Sell random stocks from the bottom 10 lowest priced stocks
    lowest_priced = sorted(tickers, key=lambda t: prices[t][0])[:10]
    ticker = random.choice(lowest_priced)
    trade = Trade(ticker, -100)
    return [trade]

def trade27():
    # Buy 2 stocks with the highest momentum (last 5 days)
    momentums = {ticker: prices[ticker][0] - prices[ticker][4] for ticker in tickers}
    top_momentum_tickers = sorted(momentums, key=momentums.get, reverse=True)[:2]
    trades = [Trade(ticker, 100) for ticker in top_momentum_tickers]
    return trades

def trade28():
    # Sell 2 stocks with the lowest momentum (last 5 days)
    momentums = {ticker: prices[ticker][0] - prices[ticker][4] for ticker in tickers}
    lowest_momentum_tickers = sorted(momentums, key=momentums.get)[:2]
    trades = [Trade(ticker, -100) for ticker in lowest_momentum_tickers]
    return trades

def trade29():
    # Buy the stock with the highest daily price increase yesterday
    yesterday_increase = {ticker: prices[ticker][1] - prices[ticker][2] for ticker in tickers}
    best_yesterday_ticker = max(yesterday_increase, key=yesterday_increase.get)
    trade = Trade(best_yesterday_ticker, 100)
    return [trade]

def trade30():
    # Sell the stock with the highest daily price decrease yesterday
    yesterday_decrease = {ticker: prices[ticker][1] - prices[ticker][2] for ticker in tickers}
    worst_yesterday_ticker = min(yesterday_decrease, key=yesterday_decrease.get)
    trade = Trade(worst_yesterday_ticker, -100)
    return [trade]

def trade31():
    # Long/short strategy: Buy the top performing stock and sell the worst performing stock over the last 7 days
    avg_prices = {ticker: np.mean(prices[ticker][:7]) for ticker in tickers}
    best_ticker = max(avg_prices, key=avg_prices.get)
    worst_ticker = min(avg_prices, key=avg_prices.get)
    trades = [Trade(best_ticker, 100), Trade(worst_ticker, -100)]
    return trades

def trade32():
    # Buy stocks that have had a positive return in the last 5 days and sell those with a negative return
    returns = {ticker: (prices[ticker][0] - prices[ticker][4]) / prices[ticker][4] for ticker in tickers}
    buy_tickers = [ticker for ticker in tickers if returns[ticker] > 0]
    sell_tickers = [ticker for ticker in tickers if returns[ticker] < 0]
    trades = [Trade(ticker, 100) for ticker in random.sample(buy_tickers, min(2, len(buy_tickers)))] + \
             [Trade(ticker, -100) for ticker in random.sample(sell_tickers, min(2, len(sell_tickers)))]
    return trades

def trade33():
    # Buy 2 stocks with the highest price-to-earnings ratio and sell 2 with the lowest
    pe_ratios = {ticker: random.uniform(10, 30) for ticker in tickers}  # Mock P/E ratios
    top_pe_tickers = sorted(pe_ratios, key=pe_ratios.get, reverse=True)[:2]
    low_pe_tickers = sorted(pe_ratios, key=pe_ratios.get)[:2]
    trades = [Trade(ticker, 100) for ticker in top_pe_tickers] + [Trade(ticker, -100) for ticker in low_pe_tickers]
    return trades

def trade34():
    # Buy the stock with the highest volume and sell the one with the lowest volume
    volumes = {ticker: random.randint(1000, 10000) for ticker in tickers}  # Mock volumes
    high_volume_ticker = max(volumes, key=volumes.get)
    low_volume_ticker = min(volumes, key=volumes.get)
    trades = [Trade(high_volume_ticker, 100), Trade(low_volume_ticker, -100)]
    return trades

def trade35():
    # Buy 3 stocks with the highest recent momentum and sell 3 with the lowest recent momentum
    momentums = {ticker: prices[ticker][0] - prices[ticker][5] for ticker in tickers}
    top_momentum_tickers = sorted(momentums, key=momentums.get, reverse=True)[:3]
    low_momentum_tickers = sorted(momentums, key=momentums.get)[:3]
    trades = [Trade(ticker, 100) for ticker in top_momentum_tickers] + [Trade(ticker, -100) for ticker in low_momentum_tickers]
    return trades

def trade36():
    # Buy stocks in the technology sector and sell stocks in the energy sector
    tech_stocks = random.sample(tickers, 3)  # Mock tech stocks
    energy_stocks = random.sample(tickers, 3)  # Mock energy stocks
    trades = [Trade(ticker, 100) for ticker in tech_stocks] + [Trade(ticker, -100) for ticker in energy_stocks]
    return trades

def trade37():
    # Long/short strategy: Buy the top 2 stocks with the highest recent gains and sell the top 2 with the highest recent losses
    recent_gains = {ticker: prices[ticker][0] - prices[ticker][10] for ticker in tickers}
    top_gainers = sorted(recent_gains, key=recent_gains.get, reverse=True)[:2]
    top_losers = sorted(recent_gains, key=recent_gains.get)[:2]
    trades = [Trade(ticker, 100) for ticker in top_gainers] + [Trade(ticker, -100) for ticker in top_losers]
    return trades

def trade38():
    # Buy the stocks with the highest dividend yield and sell those with the lowest
    dividend_yields = {ticker: random.uniform(1, 5) for ticker in tickers}  # Mock dividend yields
    high_yield_tickers = sorted(dividend_yields, key=dividend_yields.get, reverse=True)[:2]
    low_yield_tickers = sorted(dividend_yields, key=dividend_yields.get)[:2]
    trades = [Trade(ticker, 100) for ticker in high_yield_tickers] + [Trade(ticker, -100) for ticker in low_yield_tickers]
    return trades

def trade39():
    # Buy stocks that are trading near their 52-week highs and sell those near their 52-week lows
    highs_52w = {ticker: max(prices[ticker]) for ticker in tickers}
    lows_52w = {ticker: min(prices[ticker]) for ticker in tickers}
    near_highs = [ticker for ticker in tickers if prices[ticker][0] >= 0.9 * highs_52w[ticker]]
    near_lows = [ticker for ticker in tickers if prices[ticker][0] <= 1.1 * lows_52w[ticker]]
    trades = [Trade(ticker, 100) for ticker in random.sample(near_highs, min(2, len(near_highs)))] + \
             [Trade(ticker, -100) for ticker in random.sample(near_lows, min(2, len(near_lows)))]
    return trades

def trade40():
    # Long/short strategy: Buy 2 random stocks from the top 10 performing sectors and sell 2 from the bottom 10
    sectors = {ticker: random.choice(['Tech', 'Energy', 'Health', 'Finance', 'Retail']) for ticker in tickers}
    sector_performance = {sector: random.uniform(-10, 10) for sector in set(sectors.values())}
    top_sectors = sorted(sector_performance, key=sector_performance.get, reverse=True)[:2]
    bottom_sectors = sorted(sector_performance, key=sector_performance.get)[:2]
    buy_tickers = [ticker for ticker in tickers if sectors[ticker] in top_sectors]
    sell_tickers = [ticker for ticker in tickers if sectors[ticker] in bottom_sectors]
    trades = [Trade(ticker, 100) for ticker in random.sample(buy_tickers, min(2, len(buy_tickers)))] + \
             [Trade(ticker, -100) for ticker in random.sample(sell_tickers, min(2, len(sell_tickers)))]
    return trades

def trade41():
    # Buy the stock with the highest price increase today
    price_increases = {ticker: prices[ticker][0] - prices[ticker][1] for ticker in tickers}
    best_ticker = max(price_increases, key=price_increases.get)
    trade = Trade(best_ticker, 100)
    return [trade]

def trade42():
    # Sell the stock with the highest price decrease today
    price_decreases = {ticker: prices[ticker][0] - prices[ticker][1] for ticker in tickers}
    worst_ticker = min(price_decreases, key=price_decreases.get)
    trade = Trade(worst_ticker, -100)
    return [trade]

def trade43():
    # Buy stocks that have had a positive return in the last 3 days
    returns = {ticker: (prices[ticker][0] - prices[ticker][2]) / prices[ticker][2] for ticker in tickers}
    buy_tickers = [ticker for ticker in tickers if returns[ticker] > 0]
    trades = [Trade(ticker, 100) for ticker in random.sample(buy_tickers, min(3, len(buy_tickers)))]
    return trades

def trade44():
    # Sell stocks that have had a negative return in the last 3 days
    returns = {ticker: (prices[ticker][0] - prices[ticker][2]) / prices[ticker][2] for ticker in tickers}
    sell_tickers = [ticker for ticker in tickers if returns[ticker] < 0]
    trades = [Trade(ticker, -100) for ticker in random.sample(sell_tickers, min(3, len(sell_tickers)))]
    return trades

def trade45():
    # Buy the stock with the highest average return over the last 10 days
    avg_returns = {ticker: np.mean([(prices[ticker][i] - prices[ticker][i+1]) / prices[ticker][i+1] for i in range(9)]) for ticker in tickers}
    best_ticker = max(avg_returns, key=avg_returns.get)
    trade = Trade(best_ticker, 100)
    return [trade]

def trade46():
    # Sell the stock with the lowest average return over the last 10 days
    avg_returns = {ticker: np.mean([(prices[ticker][i] - prices[ticker][i+1]) / prices[ticker][i+1] for i in range(9)]) for ticker in tickers}
    worst_ticker = min(avg_returns, key=avg_returns.get)
    trade = Trade(worst_ticker, -100)
    return [trade]

def trade47():
    # Buy stocks that are oversold based on RSI (Randomly assigned for simplicity)
    rsi = {ticker: random.uniform(0, 100) for ticker in tickers}
    oversold_tickers = [ticker for ticker in tickers if rsi[ticker] < 30]
    trades = [Trade(ticker, 100) for ticker in random.sample(oversold_tickers, min(3, len(oversold_tickers)))]
    return trades

def trade48():
    # Sell stocks that are overbought based on RSI (Randomly assigned for simplicity)
    rsi = {ticker: random.uniform(0, 100) for ticker in tickers}
    overbought_tickers = [ticker for ticker in tickers if rsi[ticker] > 70]
    trades = [Trade(ticker, -100) for ticker in random.sample(overbought_tickers, min(3, len(overbought_tickers)))]
    return trades

def trade49():
    # Buy stocks with positive momentum over the last 20 days
    momentums = {ticker: prices[ticker][0] - prices[ticker][19] for ticker in tickers}
    positive_momentum_tickers = [ticker for ticker in momentums if momentums[ticker] > 0]
    trades = [Trade(ticker, 100) for ticker in random.sample(positive_momentum_tickers, min(3, len(positive_momentum_tickers)))]
    return trades

def trade50():
    # Sell stocks with negative momentum over the last 20 days
    momentums = {ticker: prices[ticker][0] - prices[ticker][19] for ticker in tickers}
    negative_momentum_tickers = [ticker for ticker in momentums if momentums[ticker] < 0]
    trades = [Trade(ticker, -100) for ticker in random.sample(negative_momentum_tickers, min(3, len(negative_momentum_tickers)))]
    return trades

def trade51():
    # Buy stocks that have a high positive correlation with a randomly chosen strong performer
    import scipy.stats
    base_ticker = random.choice(tickers)
    base_prices = prices[base_ticker]
    correlations = {ticker: scipy.stats.pearsonr(base_prices, prices[ticker])[0] for ticker in tickers if ticker != base_ticker}
    high_corr_tickers = [ticker for ticker, corr in correlations.items() if corr > 0.8]
    trades = [Trade(ticker, 100) for ticker in random.sample(high_corr_tickers, min(3, len(high_corr_tickers)))]
    return trades

def trade52():
    # Sell stocks that have a high negative correlation with a randomly chosen weak performer
    import scipy.stats
    base_ticker = random.choice(tickers)
    base_prices = prices[base_ticker]
    correlations = {ticker: scipy.stats.pearsonr(base_prices, prices[ticker])[0] for ticker in tickers if ticker != base_ticker}
    low_corr_tickers = [ticker for ticker, corr in correlations.items() if corr < -0.8]
    trades = [Trade(ticker, -100) for ticker in random.sample(low_corr_tickers, min(3, len(low_corr_tickers)))]
    return trades

def trade53():
    # Long/short strategy: Buy stocks with high positive correlation and sell stocks with high negative correlation to a strong performer
    import scipy.stats
    base_ticker = random.choice(tickers)
    base_prices = prices[base_ticker]
    correlations = {ticker: scipy.stats.pearsonr(base_prices, prices[ticker])[0] for ticker in tickers if ticker != base_ticker}
    high_corr_tickers = [ticker for ticker, corr in correlations.items() if corr > 0.7]
    low_corr_tickers = [ticker for ticker, corr in correlations.items() if corr < -0.7]
    trades = [Trade(ticker, 100) for ticker in random.sample(high_corr_tickers, min(2, len(high_corr_tickers)))] + \
             [Trade(ticker, -100) for ticker in random.sample(low_corr_tickers, min(2, len(low_corr_tickers)))]
    return trades

def trade54():
    # Buy stocks that have a high correlation with an index (e.g., S&P 500)
    import scipy.stats
    index_prices = [random.uniform(1000, 5000) for _ in range(len(prices[tickers[0]]))]  # Mock index prices
    correlations = {ticker: scipy.stats.pearsonr(index_prices, prices[ticker])[0] for ticker in tickers}
    high_corr_tickers = [ticker for ticker, corr in correlations.items() if corr > 0.8]
    trades = [Trade(ticker, 100) for ticker in random.sample(high_corr_tickers, min(3, len(high_corr_tickers)))]
    return trades

def trade55():
    # Sell stocks that have a low correlation with an index (e.g., S&P 500)
    import scipy.stats
    index_prices = [random.uniform(1000, 5000) for _ in range(len(prices[tickers[0]]))]  # Mock index prices
    correlations = {ticker: scipy.stats.pearsonr(index_prices, prices[ticker])[0] for ticker in tickers}
    low_corr_tickers = [ticker for ticker, corr in correlations.items() if corr < 0.2]
    trades = [Trade(ticker, -100) for ticker in random.sample(low_corr_tickers, min(3, len(low_corr_tickers)))]
    return trades

def trade56():
    # Long/short strategy: Buy stocks with high correlation and sell stocks with low correlation to a randomly chosen strong performer
    import scipy.stats
    base_ticker = random.choice(tickers)
    base_prices = prices[base_ticker]
    correlations = {ticker: scipy.stats.pearsonr(base_prices, prices[ticker])[0] for ticker in tickers if ticker != base_ticker}
    high_corr_tickers = [ticker for ticker, corr in correlations.items() if corr > 0.7]
    low_corr_tickers = [ticker for ticker, corr in correlations.items() if corr < 0.2]
    trades = [Trade(ticker, 100) for ticker in random.sample(high_corr_tickers, min(2, len(high_corr_tickers)))] + \
             [Trade(ticker, -100) for ticker in random.sample(low_corr_tickers, min(2, len(low_corr_tickers)))]
    return trades

def trade57():
    # Buy stocks that are inversely correlated with a major sector ETF (mocked data)
    import scipy.stats
    sector_etf_prices = [random.uniform(50, 150) for _ in range(len(prices[tickers[0]]))]  # Mock sector ETF prices
    correlations = {ticker: scipy.stats.pearsonr(sector_etf_prices, prices[ticker])[0] for ticker in tickers}
    inverse_corr_tickers = [ticker for ticker, corr in correlations.items() if corr < -0.7]
    trades = [Trade(ticker, 100) for ticker in random.sample(inverse_corr_tickers, min(3, len(inverse_corr_tickers)))]
    return trades

def trade58():
    # Sell stocks that are highly correlated with a volatile index
    import scipy.stats
    volatile_index_prices = [random.uniform(1000, 2000) for _ in range(len(prices[tickers[0]]))]  # Mock volatile index prices
    correlations = {ticker: scipy.stats.pearsonr(volatile_index_prices, prices[ticker])[0] for ticker in tickers}
    high_corr_tickers = [ticker for ticker, corr in correlations.items() if corr > 0.8]
    trades = [Trade(ticker, -100) for ticker in random.sample(high_corr_tickers, min(3, len(high_corr_tickers)))]
    return trades

def trade59():
    # Buy stocks that are less correlated with the overall market (S&P 500)
    import scipy.stats
    market_prices = [random.uniform(1000, 5000) for _ in range(len(prices[tickers[0]]))]  # Mock market index prices
    correlations = {ticker: scipy.stats.pearsonr(market_prices, prices[ticker])[0] for ticker in tickers}
    low_corr_tickers = [ticker for ticker, corr in correlations.items() if corr < 0.3]
    trades = [Trade(ticker, 100) for ticker in random.sample(low_corr_tickers, min(3, len(low_corr_tickers)))]
    return trades

def trade60():
    # Sell stocks that are highly correlated with a specific commodity price (e.g., oil)
    import scipy.stats
    commodity_prices = [random.uniform(50, 100) for _ in range(len(prices[tickers[0]]))]  # Mock commodity prices
    correlations = {ticker: scipy.stats.pearsonr(commodity_prices, prices[ticker])[0] for ticker in tickers}
    high_corr_tickers = [ticker for ticker, corr in correlations.items() if corr > 0.7]
    trades = [Trade(ticker, -100) for ticker in random.sample(high_corr_tickers, min(3, len(high_corr_tickers)))]
    return trades

def trade61():
    # Buy stocks forming a "double bottom" pattern (last 5 days)
    double_bottom_tickers = [ticker for ticker in tickers if prices[ticker][4] < prices[ticker][2] == prices[ticker][0] < prices[ticker][1] and prices[ticker][3] > prices[ticker][2]]
    trades = [Trade(ticker, 100) for ticker in random.sample(double_bottom_tickers, min(3, len(double_bottom_tickers)))]
    return trades

def trade62():
    # Sell stocks forming a "double top" pattern (last 5 days)
    double_top_tickers = [ticker for ticker in tickers if prices[ticker][4] > prices[ticker][2] == prices[ticker][0] > prices[ticker][1] and prices[ticker][3] < prices[ticker][2]]
    trades = [Trade(ticker, -100) for ticker in random.sample(double_top_tickers, min(3, len(double_top_tickers)))]
    return trades

def trade63():
    # Buy stocks showing a "head and shoulders" bottom pattern (last 7 days)
    hs_bottom_tickers = [ticker for ticker in tickers if prices[ticker][6] > prices[ticker][5] < prices[ticker][4] > prices[ticker][3] < prices[ticker][2] and prices[ticker][1] < prices[ticker][0]]
    trades = [Trade(ticker, 100) for ticker in random.sample(hs_bottom_tickers, min(3, len(hs_bottom_tickers)))]
    return trades

def trade64():
    # Sell stocks showing a "head and shoulders" top pattern (last 7 days)
    hs_top_tickers = [ticker for ticker in tickers if prices[ticker][6] < prices[ticker][5] > prices[ticker][4] < prices[ticker][3] > prices[ticker][2] and prices[ticker][1] > prices[ticker][0]]
    trades = [Trade(ticker, -100) for ticker in random.sample(hs_top_tickers, min(3, len(hs_top_tickers)))]
    return trades

def trade65():
    # Buy stocks forming a "bullish flag" pattern (last 10 days)
    bullish_flag_tickers = [ticker for ticker in tickers if prices[ticker][9] < prices[ticker][8] and all(prices[ticker][i] < prices[ticker][i+1] for i in range(8, 4, -1)) and all(prices[ticker][i] > prices[ticker][i+1] for i in range(4, 0, -1))]
    trades = [Trade(ticker, 100) for ticker in random.sample(bullish_flag_tickers, min(3, len(bullish_flag_tickers)))]
    return trades

def trade66():
    # Sell stocks forming a "bearish flag" pattern (last 10 days)
    bearish_flag_tickers = [ticker for ticker in tickers if prices[ticker][9] > prices[ticker][8] and all(prices[ticker][i] > prices[ticker][i+1] for i in range(8, 4, -1)) and all(prices[ticker][i] < prices[ticker][i+1] for i in range(4, 0, -1))]
    trades = [Trade(ticker, -100) for ticker in random.sample(bearish_flag_tickers, min(3, len(bearish_flag_tickers)))]
    return trades

def trade67():
    # Buy stocks forming a "ascending triangle" pattern (last 15 days)
    ascending_triangle_tickers = [ticker for ticker in tickers if prices[ticker][14] < prices[ticker][13] and prices[ticker][0] > prices[ticker][7] and all(prices[ticker][i] <= prices[ticker][i+1] for i in range(13))]
    trades = [Trade(ticker, 100) for ticker in random.sample(ascending_triangle_tickers, min(3, len(ascending_triangle_tickers)))]
    return trades

def trade68():
    # Sell stocks forming a "descending triangle" pattern (last 15 days)
    descending_triangle_tickers = [ticker for ticker in tickers if prices[ticker][14] > prices[ticker][13] and prices[ticker][0] < prices[ticker][7] and all(prices[ticker][i] >= prices[ticker][i+1] for i in range(13))]
    trades = [Trade(ticker, -100) for ticker in random.sample(descending_triangle_tickers, min(3, len(descending_triangle_tickers)))]
    return trades

def trade69():
    # Buy stocks forming a "rounding bottom" pattern (last 20 days)
    rounding_bottom_tickers = [ticker for ticker in tickers if all(prices[ticker][i] >= prices[ticker][i+1] for i in range(10)) and all(prices[ticker][i] <= prices[ticker][i+1] for i in range(10, 19))]
    trades = [Trade(ticker, 100) for ticker in random.sample(rounding_bottom_tickers, min(3, len(rounding_bottom_tickers)))]
    return trades

def trade70():
    # Sell stocks forming a "rounding top" pattern (last 20 days)
    rounding_top_tickers = [ticker for ticker in tickers if all(prices[ticker][i] <= prices[ticker][i+1] for i in range(10)) and all(prices[ticker][i] >= prices[ticker][i+1] for i in range(10, 19))]
    trades = [Trade(ticker, -100) for ticker in random.sample(rounding_top_tickers, min(3, len(rounding_top_tickers)))]
    return trades

def trade71():
    # Buy stocks showing a strong upward trend over the last 10 days
    upward_trend_tickers = [ticker for ticker in tickers if prices[ticker][0] > prices[ticker][9] and all(prices[ticker][i] >= prices[ticker][i+1] for i in range(9))]
    trades = [Trade(ticker, 100) for ticker in random.sample(upward_trend_tickers, min(3, len(upward_trend_tickers)))]
    return trades

def trade72():
    # Sell stocks showing a strong downward trend over the last 10 days
    downward_trend_tickers = [ticker for ticker in tickers if prices[ticker][0] < prices[ticker][9] and all(prices[ticker][i] <= prices[ticker][i+1] for i in range(9))]
    trades = [Trade(ticker, -100) for ticker in random.sample(downward_trend_tickers, min(3, len(downward_trend_tickers)))]
    return trades

def trade73():
    # Buy stocks that have reverted to their mean price over the last 20 days
    mean_reversion_tickers = [ticker for ticker in tickers if abs(prices[ticker][0] - np.mean(prices[ticker][:20])) < np.std(prices[ticker][:20])]
    trades = [Trade(ticker, 100) for ticker in random.sample(mean_reversion_tickers, min(3, len(mean_reversion_tickers)))]
    return trades

def trade74():
    # Sell stocks that have deviated significantly from their mean price over the last 20 days
    mean_deviation_tickers = [ticker for ticker in tickers if abs(prices[ticker][0] - np.mean(prices[ticker][:20])) > 2 * np.std(prices[ticker][:20])]
    trades = [Trade(ticker, -100) for ticker in random.sample(mean_deviation_tickers, min(3, len(mean_deviation_tickers)))]
    return trades

def trade75():
    # Buy stocks that have shown increased volatility in the last 10 days compared to the previous 20 days
    increased_volatility_tickers = [ticker for ticker in tickers if np.std(prices[ticker][:10]) > 1.5 * np.std(prices[ticker][10:30])]
    trades = [Trade(ticker, 100) for ticker in random.sample(increased_volatility_tickers, min(3, len(increased_volatility_tickers)))]
    return trades

def trade76():
    # Sell stocks that have shown decreased volatility in the last 10 days compared to the previous 20 days
    decreased_volatility_tickers = [ticker for ticker in tickers if np.std(prices[ticker][:10]) < 0.5 * np.std(prices[ticker][10:30])]
    trades = [Trade(ticker, -100) for ticker in random.sample(decreased_volatility_tickers, min(3, len(decreased_volatility_tickers)))]
    return trades

def trade77():
    # Buy stocks that have broken above their previous 50-day high
    previous_50_day_highs = {ticker: max(prices[ticker][1:51]) for ticker in tickers}
    breakout_tickers = [ticker for ticker in tickers if prices[ticker][0] > previous_50_day_highs[ticker]]
    trades = [Trade(ticker, 100) for ticker in random.sample(breakout_tickers, min(3, len(breakout_tickers)))]
    return trades

def trade78():
    # Sell stocks that have broken below their previous 50-day low
    previous_50_day_lows = {ticker: min(prices[ticker][1:51]) for ticker in tickers}
    breakdown_tickers = [ticker for ticker in tickers if prices[ticker][0] < previous_50_day_lows[ticker]]
    trades = [Trade(ticker, -100) for ticker in random.sample(breakdown_tickers, min(3, len(breakdown_tickers)))]
    return trades

def trade79():
    # Buy stocks that have shown a significant upward price spike in the last 3 days
    price_spike_tickers = [ticker for ticker in tickers if (prices[ticker][0] - prices[ticker][2]) / prices[ticker][2] > 0.1]
    trades = [Trade(ticker, 100) for ticker in random.sample(price_spike_tickers, min(3, len(price_spike_tickers)))]
    return trades

def trade80():
    # Sell stocks that have shown a significant downward price spike in the last 3 days
    price_drop_tickers = [ticker for ticker in tickers if (prices[ticker][0] - prices[ticker][2]) / prices[ticker][2] < -0.1]
    trades = [Trade(ticker, -100) for ticker in random.sample(price_drop_tickers, min(3, len(price_drop_tickers)))]
    return trades

def trade81():
    # Buy stocks that have formed a "golden cross" (50-day MA crosses above 200-day MA)
    golden_cross_tickers = [ticker for ticker in tickers if np.mean(prices[ticker][:50]) > np.mean(prices[ticker][:200])]
    trades = [Trade(ticker, 100) for ticker in random.sample(golden_cross_tickers, min(3, len(golden_cross_tickers)))]
    return trades

def trade82():
    # Sell stocks that have formed a "death cross" (50-day MA crosses below 200-day MA)
    death_cross_tickers = [ticker for ticker in tickers if np.mean(prices[ticker][:50]) < np.mean(prices[ticker][:200])]
    trades = [Trade(ticker, -100) for ticker in random.sample(death_cross_tickers, min(3, len(death_cross_tickers)))]
    return trades

def trade83():
    # Buy stocks that have shown an increase in trading volume in the last 5 days
    volume_increase_tickers = [ticker for ticker in tickers if np.mean(prices[ticker][:5]) > 1.2 * np.mean(prices[ticker][5:10])]
    trades = [Trade(ticker, 100) for ticker in random.sample(volume_increase_tickers, min(3, len(volume_increase_tickers)))]
    return trades

def trade84():
    # Sell stocks that have shown a decrease in trading volume in the last 5 days
    volume_decrease_tickers = [ticker for ticker in tickers if np.mean(prices[ticker][:5]) < 0.8 * np.mean(prices[ticker][5:10])]
    trades = [Trade(ticker, -100) for ticker in random.sample(volume_decrease_tickers, min(3, len(volume_decrease_tickers)))]
    return trades

def trade85():
    # Buy stocks that have shown consistent daily gains for the last 5 days
    consistent_gainers = [ticker for ticker in tickers if all(prices[ticker][i] > prices[ticker][i+1] for i in range(5))]
    trades = [Trade(ticker, 100) for ticker in random.sample(consistent_gainers, min(3, len(consistent_gainers)))]
    return trades

def trade86():
    # Sell stocks that have shown consistent daily losses for the last 5 days
    consistent_losers = [ticker for ticker in tickers if all(prices[ticker][i] < prices[ticker][i+1] for i in range(5))]
    trades = [Trade(ticker, -100) for ticker in random.sample(consistent_losers, min(3, len(consistent_losers)))]
    return trades

def trade87():
    # Buy stocks that are trading near their all-time highs
    all_time_high_tickers = [ticker for ticker in tickers if prices[ticker][0] >= 0.95 * max(prices[ticker])]
    trades = [Trade(ticker, 100) for ticker in random.sample(all_time_high_tickers, min(3, len(all_time_high_tickers)))]
    return trades

def trade88():
    # Sell stocks that are trading near their all-time lows
    all_time_low_tickers = [ticker for ticker in tickers if prices[ticker][0] <= 1.05 * min(prices[ticker])]
    trades = [Trade(ticker, -100) for ticker in random.sample(all_time_low_tickers, min(3, len(all_time_low_tickers)))]
    return trades

def trade89():
    # Buy stocks that have gapped up at market open today
    gap_up_tickers = [ticker for ticker in tickers if prices[ticker][0] > 1.05 * prices[ticker][1]]
    trades = [Trade(ticker, 100) for ticker in random.sample(gap_up_tickers, min(3, len(gap_up_tickers)))]
    return trades

def trade90():
    # Sell stocks that have gapped down at market open today
    gap_down_tickers = [ticker for ticker in tickers if prices[ticker][0] < 0.95 * prices[ticker][1]]
    trades = [Trade(ticker, -100) for ticker in random.sample(gap_down_tickers, min(3, len(gap_down_tickers)))]
    return trades

def trade91():
    # Buy stocks that have shown a steady upward trend for the last 15 days
    steady_uptrend_tickers = [ticker for ticker in tickers if all(prices[ticker][i] >= prices[ticker][i+1] for i in range(15))]
    trades = [Trade(ticker, 100) for ticker in random.sample(steady_uptrend_tickers, min(3, len(steady_uptrend_tickers)))]
    return trades

def trade92():
    # Sell stocks that have shown a steady downward trend for the last 15 days
    steady_downtrend_tickers = [ticker for ticker in tickers if all(prices[ticker][i] <= prices[ticker][i+1] for i in range(15))]
    trades = [Trade(ticker, -100) for ticker in random.sample(steady_downtrend_tickers, min(3, len(steady_downtrend_tickers)))]
    return trades

def trade93():
    # Buy stocks that have outperformed the market index by 5% in the last 30 days
    market_index_return = random.uniform(-0.05, 0.05)  # Mock market index return
    outperforming_tickers = [ticker for ticker in tickers if (prices[ticker][0] - prices[ticker][29]) / prices[ticker][29] > market_index_return + 0.05]
    trades = [Trade(ticker, 100) for ticker in random.sample(outperforming_tickers, min(3, len(outperforming_tickers)))]
    return trades

def trade94():
    # Sell stocks that have underperformed the market index by 5% in the last 30 days
    market_index_return = random.uniform(-0.05, 0.05)  # Mock market index return
    underperforming_tickers = [ticker for ticker in tickers if (prices[ticker][0] - prices[ticker][29]) / prices[ticker][29] < market_index_return - 0.05]
    trades = [Trade(ticker, -100) for ticker in random.sample(underperforming_tickers, min(3, len(underperforming_tickers)))]
    return trades

def trade95():
    # Buy stocks that have broken above their previous 10-day high
    previous_10_day_highs = {ticker: max(prices[ticker][1:11]) for ticker in tickers}
    breakout_tickers = [ticker for ticker in tickers if prices[ticker][0] > previous_10_day_highs[ticker]]
    trades = [Trade(ticker, 100) for ticker in random.sample(breakout_tickers, min(3, len(breakout_tickers)))]
    return trades

def trade96():
    # Sell stocks that have broken below their previous 10-day low
    previous_10_day_lows = {ticker: min(prices[ticker][1:11]) for ticker in tickers}
    breakdown_tickers = [ticker for ticker in tickers if prices[ticker][0] < previous_10_day_lows[ticker]]
    trades = [Trade(ticker, -100) for ticker in random.sample(breakdown_tickers, min(3, len(breakdown_tickers)))]
    return trades

def trade97():
    # Buy stocks with a relative strength index (RSI) below 30 (oversold)
    rsi = {ticker: random.uniform(0, 100) for ticker in tickers}  # Mock RSI values
    oversold_tickers = [ticker for ticker in tickers if rsi[ticker] < 30]
    trades = [Trade(ticker, 100) for ticker in random.sample(oversold_tickers, min(3, len(oversold_tickers)))]
    return trades

def trade98():
    # Sell stocks with a relative strength index (RSI) above 70 (overbought)
    rsi = {ticker: random.uniform(0, 100) for ticker in tickers}  # Mock RSI values
    overbought_tickers = [ticker for ticker in tickers if rsi[ticker] > 70]
    trades = [Trade(ticker, -100) for ticker in random.sample(overbought_tickers, min(3, len(overbought_tickers)))]
    return trades

def trade99():
    # Buy stocks with a price-to-earnings ratio (P/E) below the industry average (mocked data)
    pe_ratios = {ticker: random.uniform(10, 30) for ticker in tickers}  # Mock P/E ratios
    industry_average_pe = 20  # Mock industry average P/E
    undervalued_tickers = [ticker for ticker in tickers if pe_ratios[ticker] < industry_average_pe]
    trades = [Trade(ticker, 100) for ticker in random.sample(undervalued_tickers, min(3, len(undervalued_tickers)))]
    return trades

def trade100():
    # Sell stocks with a price-to-earnings ratio (P/E) above the industry average (mocked data)
    pe_ratios = {ticker: random.uniform(10, 30) for ticker in tickers}  # Mock P/E ratios
    industry_average_pe = 20  # Mock industry average P/E
    overvalued_tickers = [ticker for ticker in tickers if pe_ratios[ticker] > industry_average_pe]
    trades = [Trade(ticker, -100) for ticker in random.sample(overvalued_tickers, min(3, len(overvalued_tickers)))]
    return trades

def trade101():
    # Buy stocks that have outperformed the market by more than 5% in the last 10 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(10)]
    market_return = (market_total[0] - market_total[-1]) / market_total[-1]
    outperforming_tickers = [ticker for ticker in tickers if (prices[ticker][0] - prices[ticker][9]) / prices[ticker][9] > market_return + 0.05]
    trades = [Trade(ticker, 100) for ticker in random.sample(outperforming_tickers, min(3, len(outperforming_tickers)))]
    return trades

def trade102():
    # Sell stocks that have underperformed the market by more than 5% in the last 10 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(10)]
    market_return = (market_total[0] - market_total[-1]) / market_total[-1]
    underperforming_tickers = [ticker for ticker in tickers if (prices[ticker][0] - prices[ticker][9]) / prices[ticker][9] < market_return - 0.05]
    trades = [Trade(ticker, -100) for ticker in random.sample(underperforming_tickers, min(3, len(underperforming_tickers)))]
    return trades

def trade103():
    # Buy stocks that have shown a positive return while the market showed a negative return over the last 5 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(5)]
    market_return = (market_total[0] - market_total[-1]) / market_total[-1]
    positive_tickers = [ticker for ticker in tickers if (prices[ticker][0] - prices[ticker][4]) / prices[ticker][4] > 0 and market_return < 0]
    trades = [Trade(ticker, 100) for ticker in random.sample(positive_tickers, min(3, len(positive_tickers)))]
    return trades

def trade104():
    # Sell stocks that have shown a negative return while the market showed a positive return over the last 5 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(5)]
    market_return = (market_total[0] - market_total[-1]) / market_total[-1]
    negative_tickers = [ticker for ticker in tickers if (prices[ticker][0] - prices[ticker][4]) / prices[ticker][4] < 0 and market_return > 0]
    trades = [Trade(ticker, -100) for ticker in random.sample(negative_tickers, min(3, len(negative_tickers)))]
    return trades

def trade105():
    # Buy stocks that have shown less volatility compared to the market over the last 20 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(20)]
    market_volatility = np.std(market_total)
    low_volatility_tickers = [ticker for ticker in tickers if np.std(prices[ticker][:20]) < market_volatility]
    trades = [Trade(ticker, 100) for ticker in random.sample(low_volatility_tickers, min(3, len(low_volatility_tickers)))]
    return trades

def trade106():
    # Sell stocks that have shown more volatility compared to the market over the last 20 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(20)]
    market_volatility = np.std(market_total)
    high_volatility_tickers = [ticker for ticker in tickers if np.std(prices[ticker][:20]) > market_volatility]
    trades = [Trade(ticker, -100) for ticker in random.sample(high_volatility_tickers, min(3, len(high_volatility_tickers)))]
    return trades

def trade107():
    # Buy stocks that have shown an increasing trend while the market showed a decreasing trend over the last 15 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(15)]
    market_trend = market_total[0] > market_total[-1]
    increasing_tickers = [ticker for ticker in tickers if prices[ticker][0] > prices[ticker][14] and not market_trend]
    trades = [Trade(ticker, 100) for ticker in random.sample(increasing_tickers, min(3, len(increasing_tickers)))]
    return trades

def trade108():
    # Sell stocks that have shown a decreasing trend while the market showed an increasing trend over the last 15 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(15)]
    market_trend = market_total[0] < market_total[-1]
    decreasing_tickers = [ticker for ticker in tickers if prices[ticker][0] < prices[ticker][14] and market_trend]
    trades = [Trade(ticker, -100) for ticker in random.sample(decreasing_tickers, min(3, len(decreasing_tickers)))]
    return trades

def trade109():
    # Buy stocks that have broken above their previous 10-day high while the market is flat
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(10)]
    market_flat = abs((market_total[0] - market_total[-1]) / market_total[-1]) < 0.01
    previous_10_day_highs = {ticker: max(prices[ticker][1:11]) for ticker in tickers}
    breakout_tickers = [ticker for ticker in tickers if prices[ticker][0] > previous_10_day_highs[ticker] and market_flat]
    trades = [Trade(ticker, 100) for ticker in random.sample(breakout_tickers, min(3, len(breakout_tickers)))]
    return trades

def trade110():
    # Sell stocks that have broken below their previous 10-day low while the market is flat
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(10)]
    market_flat = abs((market_total[0] - market_total[-1]) / market_total[-1]) < 0.01
    previous_10_day_lows = {ticker: min(prices[ticker][1:11]) for ticker in tickers}
    breakdown_tickers = [ticker for ticker in tickers if prices[ticker][0] < previous_10_day_lows[ticker] and market_flat]
    trades = [Trade(ticker, -100) for ticker in random.sample(breakdown_tickers, min(3, len(breakdown_tickers)))]
    return trades

def trade111():
    # Buy stocks that have shown a higher positive return compared to the market over the last 20 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(20)]
    market_return = (market_total[0] - market_total[-1]) / market_total[-1]
    higher_positive_tickers = [ticker for ticker in tickers if (prices[ticker][0] - prices[ticker][19]) / prices[ticker][19] > market_return]
    trades = [Trade(ticker, 100) for ticker in random.sample(higher_positive_tickers, min(3, len(higher_positive_tickers)))]
    return trades

def trade112():
    # Sell stocks that have shown a higher negative return compared to the market over the last 20 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(20)]
    market_return = (market_total[0] - market_total[-1]) / market_total[-1]
    higher_negative_tickers = [ticker for ticker in tickers if (prices[ticker][0] - prices[ticker][19]) / prices[ticker][19] < market_return]
    trades = [Trade(ticker, -100) for ticker in random.sample(higher_negative_tickers, min(3, len(higher_negative_tickers)))]
    return trades

def trade113():
    # Buy stocks that have shown less drawdown compared to the market over the last 30 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(30)]
    market_drawdown = min(market_total) / max(market_total)
    less_drawdown_tickers = [ticker for ticker in tickers if min(prices[ticker][:30]) / max(prices[ticker][:30]) > market_drawdown]
    trades = [Trade(ticker, 100) for ticker in random.sample(less_drawdown_tickers, min(3, len(less_drawdown_tickers)))]
    return trades

def trade114():
    # Sell stocks that have shown more drawdown compared to the market over the last 30 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(30)]
    market_drawdown = min(market_total) / max(market_total)
    more_drawdown_tickers = [ticker for ticker in tickers if min(prices[ticker][:30]) / max(prices[ticker][:30]) < market_drawdown]
    trades = [Trade(ticker, -100) for ticker in random.sample(more_drawdown_tickers, min(3, len(more_drawdown_tickers)))]
    return trades

def trade115():
    # Buy stocks that have had a smaller price range compared to the market over the last 15 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(15)]
    market_range = max(market_total) - min(market_total)
    small_range_tickers = [ticker for ticker in tickers if max(prices[ticker][:15]) - min(prices[ticker][:15]) < market_range]
    trades = [Trade(ticker, 100) for ticker in random.sample(small_range_tickers, min(3, len(small_range_tickers)))]
    return trades

def trade116():
    # Sell stocks that have had a larger price range compared to the market over the last 15 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(15)]
    market_range = max(market_total) - min(market_total)
    large_range_tickers = [ticker for ticker in tickers if max(prices[ticker][:15]) - min(prices[ticker][:15]) > market_range]
    trades = [Trade(ticker, -100) for ticker in random.sample(large_range_tickers, min(3, len(large_range_tickers)))]
    return trades

def trade117():
    # Buy stocks that have consistently stayed above their market-relative average price in the last 10 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(10)]
    market_avg = sum(market_total) / len(market_total)
    consistent_above_avg_tickers = [ticker for ticker in tickers if all(prices[ticker][i] > market_avg for i in range(10))]
    trades = [Trade(ticker, 100) for ticker in random.sample(consistent_above_avg_tickers, min(3, len(consistent_above_avg_tickers)))]
    return trades

def trade118():
    # Sell stocks that have consistently stayed below their market-relative average price in the last 10 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(10)]
    market_avg = sum(market_total) / len(market_total)
    consistent_below_avg_tickers = [ticker for ticker in tickers if all(prices[ticker][i] < market_avg for i in range(10))]
    trades = [Trade(ticker, -100) for ticker in random.sample(consistent_below_avg_tickers, min(3, len(consistent_below_avg_tickers)))]
    return trades

def trade119():
    # Buy stocks that have shown a positive correlation with the market trend over the last 20 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(20)]
    market_trend = scipy.stats.linregress(range(20), market_total).slope
    positive_corr_tickers = [ticker for ticker in tickers if scipy.stats.pearsonr(prices[ticker][:20], market_total)[0] > 0.5]
    trades = [Trade(ticker, 100) for ticker in random.sample(positive_corr_tickers, min(3, len(positive_corr_tickers)))]
    return trades

def trade120():
    # Sell stocks that have shown a negative correlation with the market trend over the last 20 days
    market_total = [sum(prices[ticker][i] for ticker in tickers) for i in range(20)]
    market_trend = scipy.stats.linregress(range(20), market_total).slope
    negative_corr_tickers = [ticker for ticker in tickers if scipy.stats.pearsonr(prices[ticker][:20], market_total)[0] < -0.5]
    trades = [Trade(ticker, -100) for ticker in random.sample(negative_corr_tickers, min(3, len(negative_corr_tickers)))]
    return trades