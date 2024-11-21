# tickers is a list of stock tickers
import tickers

# prices is a dict; the key is a ticker and the value is a list of historic prices, today first
import prices

# Trade represents a decision to buy or sell a quantity of a ticker
import Trade

import random
import numpy as np

def trade2():
    # Buy if the current price is lower than the average of the last 5 days
    trades = []
    for ticker in tickers:
        if prices[ticker][0] < np.mean(prices[ticker][1:6]):
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade3():
    # Sell if the current price is higher than the average of the last 10 days
    trades = []
    for ticker in tickers:
        if prices[ticker][0] > np.mean(prices[ticker][1:11]):
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade4():
    # Buy if the current price is the lowest in the last 3 days
    trades = []
    for ticker in tickers:
        if prices[ticker][0] == min(prices[ticker][:3]):
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade5():
    # Sell if the current price is the highest in the last 3 days
    trades = []
    for ticker in tickers:
        if prices[ticker][0] == max(prices[ticker][:3]):
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade6():
    # Buy if the current price is higher than the previous day's price
    trades = []
    for ticker in tickers:
        if prices[ticker][0] > prices[ticker][1]:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade7():
    # Sell if the current price is lower than the previous day's price
    trades = []
    for ticker in tickers:
        if prices[ticker][0] < prices[ticker][1]:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade8():
    # Buy if the current price is higher than the average of the last 20 days
    trades = []
    for ticker in tickers:
        if prices[ticker][0] > np.mean(prices[ticker][1:21]):
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade9():
    # Sell if the current price is lower than the average of the last 20 days
    trades = []
    for ticker in tickers:
        if prices[ticker][0] < np.mean(prices[ticker][1:21]):
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade10():
    # Buy if the current price is higher than the highest price in the last 5 days
    trades = []
    for ticker in tickers:
        if prices[ticker][0] > max(prices[ticker][1:6]):
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade11():
    # Sell if the current price is lower than the lowest price in the last 5 days
    trades = []
    for ticker in tickers:
        if prices[ticker][0] < min(prices[ticker][1:6]):
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade12():
    # Long/Short: Buy the best-performing stock and sell the worst-performing stock in the last 10 days
    best_ticker = max(tickers, key=lambda x: (prices[x][0] - prices[x][9]) / prices[x][9])
    worst_ticker = min(tickers, key=lambda x: (prices[x][0] - prices[x][9]) / prices[x][9])
    return [Trade(best_ticker, 100), Trade(worst_ticker, -100)]

def trade13():
    # Buy if the 5-day moving average crosses above the 20-day moving average
    trades = []
    for ticker in tickers:
        if np.mean(prices[ticker][:5]) > np.mean(prices[ticker][:20]) and np.mean(prices[ticker][1:6]) <= np.mean(prices[ticker][1:21]):
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade14():
    # Sell if the 5-day moving average crosses below the 20-day moving average
    trades = []
    for ticker in tickers:
        if np.mean(prices[ticker][:5]) < np.mean(prices[ticker][:20]) and np.mean(prices[ticker][1:6]) >= np.mean(prices[ticker][1:21]):
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade15():
    # Buy if the current volume is higher than the average volume of the last 10 days
    trades = []
    for ticker in tickers:
        if volumes[ticker][0] > np.mean(volumes[ticker][1:11]):
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade16():
    # Sell if the current volume is lower than the average volume of the last 10 days
    trades = []
    for ticker in tickers:
        if volumes[ticker][0] < np.mean(volumes[ticker][1:11]):
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade17():
    # Long/Short: Buy the stock with the highest relative strength index (RSI) and sell the stock with the lowest RSI
    rsi = {}
    for ticker in tickers:
        gains = [max(prices[ticker][i] - prices[ticker][i+1], 0) for i in range(13)]
        losses = [max(prices[ticker][i+1] - prices[ticker][i], 0) for i in range(13)]
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi[ticker] = 100 - (100 / (1 + rs))
    best_ticker = max(tickers, key=lambda x: rsi[x])
    worst_ticker = min(tickers, key=lambda x: rsi[x])
    return [Trade(best_ticker, 100), Trade(worst_ticker, -100)]

def trade18():
    # Buy if the current price is higher than the 50-day moving average and the 50-day moving average is higher than the 200-day moving average
    trades = []
    for ticker in tickers:
        if prices[ticker][0] > np.mean(prices[ticker][:50]) > np.mean(prices[ticker][:200]):
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade19():
    # Sell if the current price is lower than the 50-day moving average and the 50-day moving average is lower than the 200-day moving average
    trades = []
    for ticker in tickers:
        if prices[ticker][0] < np.mean(prices[ticker][:50]) < np.mean(prices[ticker][:200]):
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade20():
    # Long/Short: Buy the stock with the highest momentum and sell the stock with the lowest momentum
    momentums = {}
    for ticker in tickers:
        momentums[ticker] = prices[ticker][0] - prices[ticker][19]
    best_ticker = max(tickers, key=lambda x: momentums[x])
    worst_ticker = min(tickers, key=lambda x: momentums[x])
    return [Trade(best_ticker, 100), Trade(worst_ticker, -100)]

def trade21():
    # Buy if the current price is higher than the upper Bollinger Band
    trades = []
    for ticker in tickers:
        sma = np.mean(prices[ticker][:20])
        std = np.std(prices[ticker][:20])
        upper_band = sma + 2 * std
        if prices[ticker][0] > upper_band:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade22():
    # Sell if the current price is lower than the lower Bollinger Band
    trades = []
    for ticker in tickers:
        sma = np.mean(prices[ticker][:20])
        std = np.std(prices[ticker][:20])
        lower_band = sma - 2 * std
        if prices[ticker][0] < lower_band:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade23():
    # Buy if the current volatility is higher than the average volatility of the last 10 days
    trades = []
    for ticker in tickers:
        volatility = np.std(prices[ticker][:10])
        avg_volatility = np.mean([np.std(prices[ticker][i:i+10]) for i in range(10)])
        if volatility > avg_volatility:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade24():
    # Sell if the current volatility is lower than the average volatility of the last 10 days
    trades = []
    for ticker in tickers:
        volatility = np.std(prices[ticker][:10])
        avg_volatility = np.mean([np.std(prices[ticker][i:i+10]) for i in range(10)])
        if volatility < avg_volatility:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade25():
    # Long/Short: Buy the stock with the lowest volatility and sell the stock with the highest volatility
    volatilities = {}
    for ticker in tickers:
        volatilities[ticker] = np.std(prices[ticker][:10])
    best_ticker = min(tickers, key=lambda x: volatilities[x])
    worst_ticker = max(tickers, key=lambda x: volatilities[x])
    return [Trade(best_ticker, 100), Trade(worst_ticker, -100)]

def trade26():
    # Buy if the current price is higher than the 20-day exponential moving average (EMA)
    trades = []
    for ticker in tickers:
        ema = prices[ticker][0]
        multiplier = 2 / (20 + 1)
        for i in range(1, 20):
            ema = (prices[ticker][i] - ema) * multiplier + ema
        if prices[ticker][0] > ema:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade27():
    # Sell if the current price is lower than the 20-day exponential moving average (EMA)
    trades = []
    for ticker in tickers:
        ema = prices[ticker][0]
        multiplier = 2 / (20 + 1)
        for i in range(1, 20):
            ema = (prices[ticker][i] - ema) * multiplier + ema
        if prices[ticker][0] < ema:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade28():
    # Buy if the current price is higher than the upper Keltner Channel
    trades = []
    for ticker in tickers:
        ema = prices[ticker][0]
        multiplier = 2 / (20 + 1)
        for i in range(1, 20):
            ema = (prices[ticker][i] - ema) * multiplier + ema
        atr = np.mean([np.max(prices[ticker][i:i+10]) - np.min(prices[ticker][i:i+10]) for i in range(10)])
        upper_channel = ema + 2 * atr
        if prices[ticker][0] > upper_channel:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade29():
    # Sell if the current price is lower than the lower Keltner Channel
    trades = []
    for ticker in tickers:
        ema = prices[ticker][0]
        multiplier = 2 / (20 + 1)
        for i in range(1, 20):
            ema = (prices[ticker][i] - ema) * multiplier + ema
        atr = np.mean([np.max(prices[ticker][i:i+10]) - np.min(prices[ticker][i:i+10]) for i in range(10)])
        lower_channel = ema - 2 * atr
        if prices[ticker][0] < lower_channel:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade30():
    # Long/Short: Buy the stock with the highest Sharpe ratio and sell the stock with the lowest Sharpe ratio
    sharpe_ratios = {}
    for ticker in tickers:
        returns = [prices[ticker][i] / prices[ticker][i+1] - 1 for i in range(19)]
        sharpe_ratios[ticker] = np.mean(returns) / np.std(returns)
    best_ticker = max(tickers, key=lambda x: sharpe_ratios[x])
    worst_ticker = min(tickers, key=lambda x: sharpe_ratios[x])
    return [Trade(best_ticker, 100), Trade(worst_ticker, -100)]

def trade31():
    # Buy if the current price is higher than the Ichimoku Cloud conversion line
    trades = []
    for ticker in tickers:
        conversion_line = (np.max(prices[ticker][:9]) + np.min(prices[ticker][:9])) / 2
        if prices[ticker][0] > conversion_line:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade32():
    # Buy if the current price is higher than the price 5 days ago
    trades = []
    for ticker in tickers:
        if prices[ticker][0] > prices[ticker][4]:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade33():
    # Sell if the current price is lower than the price 5 days ago
    trades = []
    for ticker in tickers:
        if prices[ticker][0] < prices[ticker][4]:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade34():
    # Buy if the current price is the highest in the last 15 days
    trades = []
    for ticker in tickers:
        if prices[ticker][0] == max(prices[ticker][:15]):
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade35():
    # Sell if the current price is the lowest in the last 15 days
    trades = []
    for ticker in tickers:
        if prices[ticker][0] == min(prices[ticker][:15]):
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade36():
    # Buy if the current price is higher than the 10-day simple moving average (SMA)
    trades = []
    for ticker in tickers:
        sma = np.mean(prices[ticker][:10])
        if prices[ticker][0] > sma:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade37():
    # Sell if the current price is lower than the 10-day simple moving average (SMA)
    trades = []
    for ticker in tickers:
        sma = np.mean(prices[ticker][:10])
        if prices[ticker][0] < sma:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade38():
    # Buy if the current price is higher than the highest price in the last 20 days
    trades = []
    for ticker in tickers:
        if prices[ticker][0] > max(prices[ticker][:20]):
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade39():
    # Sell if the current price is lower than the lowest price in the last 20 days
    trades = []
    for ticker in tickers:
        if prices[ticker][0] < min(prices[ticker][:20]):
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade40():
    # Buy if the current price is higher than the 50-day SMA
    trades = []
    for ticker in tickers:
        sma = np.mean(prices[ticker][:50])
        if prices[ticker][0] > sma:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade41():
    # Sell if the current price is lower than the 50-day SMA
    trades = []
    for ticker in tickers:
        sma = np.mean(prices[ticker][:50])
        if prices[ticker][0] < sma:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade42():
    # Buy if the current price is higher than the previous 2 days (a simple uptrend)
    trades = []
    for ticker in tickers:
        if prices[ticker][0] > prices[ticker][1] > prices[ticker][2]:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade43():
    # Sell if the current price is lower than the previous 2 days (a simple downtrend)
    trades = []
    for ticker in tickers:
        if prices[ticker][0] < prices[ticker][1] < prices[ticker][2]:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade44():
    # Buy if the current price is higher than the previous day's high (a breakout)
    trades = []
    for ticker in tickers:
        if prices[ticker][0] > max(prices[ticker][1:2]):
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade45():
    # Sell if the current price is lower than the previous day's low (a breakdown)
    trades = []
    for ticker in tickers:
        if prices[ticker][0] < min(prices[ticker][1:2]):
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade46():
    # Buy if the current price is above the previous day's high and the previous day was a down day (a potential reversal)
    trades = []
    for ticker in tickers:
        if prices[ticker][0] > max(prices[ticker][1:2]) and prices[ticker][1] < prices[ticker][2]:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade47():
    # Sell if the current price is below the previous day's low and the previous day was an up day (a potential reversal)
    trades = []
    for ticker in tickers:
        if prices[ticker][0] < min(prices[ticker][1:2]) and prices[ticker][1] > prices[ticker][2]:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade48():
    # Buy if the current price is above the 5-day SMA and the 5-day SMA is above the 10-day SMA (a bullish crossover)
    trades = []
    for ticker in tickers:
        sma5 = np.mean(prices[ticker][:5])
        sma10 = np.mean(prices[ticker][:10])
        if prices[ticker][0] > sma5 > sma10:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade49():
    # Sell if the current price is below the 5-day SMA and the 5-day SMA is below the 10-day SMA (a bearish crossover)
    trades = []
    for ticker in tickers:
        sma5 = np.mean(prices[ticker][:5])
        sma10 = np.mean(prices[ticker][:10])
        if prices[ticker][0] < sma5 < sma10:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade50():
    # Buy if the current price is above the 50-day SMA and the previous price was below the 50-day SMA (a bullish breakthrough)
    trades = []
    for ticker in tickers:
        sma50 = np.mean(prices[ticker][:50])
        if prices[ticker][0] > sma50 and prices[ticker][1] < sma50:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade51():
    # Sell if the current price is below the 50-day SMA and the previous price was above the 50-day SMA (a bearish breakthrough)
    trades = []
    for ticker in tickers:
        sma50 = np.mean(prices[ticker][:50])
        if prices[ticker][0] < sma50 and prices[ticker][1] > sma50:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade52():
    # Buy if the current price is more than 2 standard deviations below the 20-day mean (a potential oversold condition)
    trades = []
    for ticker in tickers:
        mean20 = np.mean(prices[ticker][:20])
        std20 = np.std(prices[ticker][:20])
        if prices[ticker][0] < mean20 - 2 * std20:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade53():
    # Sell if the current price is more than 2 standard deviations above the 20-day mean (a potential overbought condition)
    trades = []
    for ticker in tickers:
        mean20 = np.mean(prices[ticker][:20])
        std20 = np.std(prices[ticker][:20])
        if prices[ticker][0] > mean20 + 2 * std20:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade54():
    # Buy if the current price is below the 50-day mean and the 50-day mean is increasing (a potential uptrend)
    trades = []
    for ticker in tickers:
        mean50 = np.mean(prices[ticker][:50])
        prev_mean50 = np.mean(prices[ticker][1:51])
        if prices[ticker][0] < mean50 and mean50 > prev_mean50:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade55():
    # Sell if the current price is above the 50-day mean and the 50-day mean is decreasing (a potential downtrend)
    trades = []
    for ticker in tickers:
        mean50 = np.mean(prices[ticker][:50])
        prev_mean50 = np.mean(prices[ticker][1:51])
        if prices[ticker][0] > mean50 and mean50 < prev_mean50:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade56():
    # Buy if the 5-day mean is above the 50-day mean and the 5-day mean was previously below the 50-day mean (a potential trend change)
    trades = []
    for ticker in tickers:
        mean5 = np.mean(prices[ticker][:5])
        mean50 = np.mean(prices[ticker][:50])
        prev_mean5 = np.mean(prices[ticker][1:6])
        if mean5 > mean50 and prev_mean5 < mean50:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade57():
    # Sell if the 5-day mean is below the 50-day mean and the 5-day mean was previously above the 50-day mean (a potential trend change)
    trades = []
    for ticker in tickers:
        mean5 = np.mean(prices[ticker][:5])
        mean50 = np.mean(prices[ticker][:50])
        prev_mean5 = np.mean(prices[ticker][1:6])
        if mean5 < mean50 and prev_mean5 > mean50:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade58():
    # Buy the ticker that has had the largest percent decrease over the last 10 days (a potential mean reversion play)
    percent_changes = {}
    for ticker in tickers:
        percent_changes[ticker] = (prices[ticker][0] - prices[ticker][9]) / prices[ticker][9] * 100
    worst_ticker = min(tickers, key=lambda x: percent_changes[x])
    return [Trade(worst_ticker, 100)]

def trade59():
    # Sell the ticker that has had the largest percent increase over the last 10 days (a potential mean reversion play)
    percent_changes = {}
    for ticker in tickers:
        percent_changes[ticker] = (prices[ticker][0] - prices[ticker][9]) / prices[ticker][9] * 100
    best_ticker = max(tickers, key=lambda x: percent_changes[x])
    return [Trade(best_ticker, -100)]

def trade60():
    # Buy if the current price is above the 200-day mean and the 200-day mean is increasing (a potential long-term uptrend)
    trades = []
    for ticker in tickers:
        mean200 = np.mean(prices[ticker][:200])
        prev_mean200 = np.mean(prices[ticker][1:201])
        if prices[ticker][0] > mean200 and mean200 > prev_mean200:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade61():
    # Sell if the current price is below the 200-day mean and the 200-day mean is decreasing (a potential long-term downtrend)
    trades = []
    for ticker in tickers:
        mean200 = np.mean(prices[ticker][:200])
        prev_mean200 = np.mean(prices[ticker][1:201])
        if prices[ticker][0] < mean200 and mean200 < prev_mean200:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade62():
    # Buy if the stock's return is greater than the market's return over the last 5 days
    trades = []
    for ticker in tickers:
        stock_return = (prices[ticker][0] - prices[ticker][4]) / prices[ticker][4]
        market_return = (sum(prices[t][0] for t in tickers) - sum(prices[t][4] for t in tickers)) / sum(prices[t][4] for t in tickers)
        if stock_return > market_return:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade63():
    # Sell if the stock's return is less than the market's return over the last 5 days
    trades = []
    for ticker in tickers:
        stock_return = (prices[ticker][0] - prices[ticker][4]) / prices[ticker][4]
        market_return = (sum(prices[t][0] for t in tickers) - sum(prices[t][4] for t in tickers)) / sum(prices[t][4] for t in tickers)
        if stock_return < market_return:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade64():
    # Buy the stock with the highest relative strength compared to the market over the last 10 days
    relative_strengths = {}
    for ticker in tickers:
        stock_return = prices[ticker][0] / prices[ticker][9]
        market_return = sum(prices[t][0] for t in tickers) / sum(prices[t][9] for t in tickers)
        relative_strengths[ticker] = stock_return / market_return
    best_ticker = max(tickers, key=lambda x: relative_strengths[x])
    return [Trade(best_ticker, 100)]

def trade65():
    # Sell the stock with the lowest relative strength compared to the market over the last 10 days
    relative_strengths = {}
    for ticker in tickers:
        stock_return = prices[ticker][0] / prices[ticker][9]
        market_return = sum(prices[t][0] for t in tickers) / sum(prices[t][9] for t in tickers)
        relative_strengths[ticker] = stock_return / market_return
    worst_ticker = min(tickers, key=lambda x: relative_strengths[x])
    return [Trade(worst_ticker, -100)]

def trade66():
    # Buy stocks that have a higher Sharpe ratio than the market over the last 20 days
    trades = []
    market_returns = [(sum(prices[t][i] for t in tickers) / sum(prices[t][i+1] for t in tickers)) - 1 for i in range(19)]
    market_sharpe = np.mean(market_returns) / np.std(market_returns)
    for ticker in tickers:
        stock_returns = [(prices[ticker][i] / prices[ticker][i+1]) - 1 for i in range(19)]
        stock_sharpe = np.mean(stock_returns) / np.std(stock_returns)
        if stock_sharpe > market_sharpe:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade67():
    # Sell stocks that have a lower Sharpe ratio than the market over the last 20 days
    trades = []
    market_returns = [(sum(prices[t][i] for t in tickers) / sum(prices[t][i+1] for t in tickers)) - 1 for i in range(19)]
    market_sharpe = np.mean(market_returns) / np.std(market_returns)
    for ticker in tickers:
        stock_returns = [(prices[ticker][i] / prices[ticker][i+1]) - 1 for i in range(19)]
        stock_sharpe = np.mean(stock_returns) / np.std(stock_returns)
        if stock_sharpe < market_sharpe:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade68():
    # Buy stocks that have a higher beta than 1 (they move more than the market)
    trades = []
    market_returns = [(sum(prices[t][i] for t in tickers) / sum(prices[t][i+1] for t in tickers)) - 1 for i in range(49)]
    for ticker in tickers:
        stock_returns = [(prices[ticker][i] / prices[ticker][i+1]) - 1 for i in range(49)]
        beta = np.cov(stock_returns, market_returns)[0, 1] / np.var(market_returns)
        if beta > 1:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade69():
    # Sell stocks that have a lower beta than 1 (they move less than the market)
    trades = []
    market_returns = [(sum(prices[t][i] for t in tickers) / sum(prices[t][i+1] for t in tickers)) - 1 for i in range(49)]
    for ticker in tickers:
        stock_returns = [(prices[ticker][i] / prices[ticker][i+1]) - 1 for i in range(49)]
        beta = np.cov(stock_returns, market_returns)[0, 1] / np.var(market_returns)
        if beta < 1:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades

def trade70():
    # Buy stocks that have a higher percentage of up days than the market over the last 50 days
    trades = []
    market_up_days = sum(sum(prices[t][i] for t in tickers) > sum(prices[t][i+1] for t in tickers) for i in range(49))
    for ticker in tickers:
        stock_up_days = sum(prices[ticker][i] > prices[ticker][i+1] for i in range(49))
        if stock_up_days > market_up_days:
            quantity = random.randrange(1, 100)
            trades.append(Trade(ticker, quantity))
    return trades

def trade71():
    # Sell stocks that have a lower percentage of up days than the market over the last 50 days
    trades = []
    market_up_days = sum(sum(prices[t][i] for t in tickers) > sum(prices[t][i+1] for t in tickers) for i in range(49))
    for ticker in tickers:
        stock_up_days = sum(prices[ticker][i] > prices[ticker][i+1] for i in range(49))
        if stock_up_days < market_up_days:
            quantity = random.randrange(-100, -1)
            trades.append(Trade(ticker, quantity))
    return trades