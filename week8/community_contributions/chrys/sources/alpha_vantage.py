"""Alpha Vantage adapter for stocks and indices."""
import requests

from models import AssetData

API_URL = "https://www.alphavantage.co/query"


def fetch_alpha_vantage(symbol: str, api_key: str) -> AssetData | None:
    if not api_key:
        return None
    try:
        # Quote
        q = requests.get(
            API_URL,
            params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key},
            timeout=15,
        )
        q.raise_for_status()
        qj = q.json()
        quote = qj.get("Global Quote", {})
        if not quote:
            return None
        price = float(quote.get("05. price", 0) or 0)
        change_pct = quote.get("10. change percent", "0%").strip("%") or "0"
        try:
            change_val = float(change_pct)
        except ValueError:
            change_val = 0.0
        change_24h = f"{change_val:+.2f}%" if change_val else "0%"

        # Daily time series for OHLCV and 52w
        t = requests.get(
            API_URL,
            params={
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": "compact",
                "apikey": api_key,
            },
            timeout=15,
        )
        t.raise_for_status()
        tj = t.json()
        series = tj.get("Time Series (Daily)", {})
        if not series:
            return AssetData(
                asset=symbol,
                price=price,
                change_24h=change_24h,
                volume_ratio=1.0,
                ohlcv_14=[],
                ohlcv_50=[],
                high_52w=price,
                low_52w=price,
            )
        # Sort by date descending
        dates = sorted(series.keys(), reverse=True)
        ohlcv_50 = []
        for d in dates[:50]:
            v = series[d]
            ohlcv_50.append({
                "t": d,
                "o": float(v.get("1. open", 0)),
                "h": float(v.get("2. high", 0)),
                "l": float(v.get("3. low", 0)),
                "c": float(v.get("4. close", 0)),
                "v": int(float(v.get("5. volume", 0))),
            })
        ohlcv_14 = ohlcv_50[:14]
        if len(ohlcv_50) < 20:
            vol_avg_20 = sum(x["v"] for x in ohlcv_50) / len(ohlcv_50) if ohlcv_50 else 1
        else:
            vol_avg_20 = sum(x["v"] for x in ohlcv_50[:20]) / 20
        last_vol = ohlcv_50[0]["v"] if ohlcv_50 else 1
        volume_ratio = last_vol / vol_avg_20 if vol_avg_20 else 1.0
        highs = [x["h"] for x in ohlcv_50]
        lows = [x["l"] for x in ohlcv_50]
        high_52w = max(highs) if highs else price
        low_52w = min(lows) if lows else price
        return AssetData(
            asset=symbol,
            price=price,
            change_1h="",  # AV daily only
            change_24h=change_24h,
            volume_ratio=round(volume_ratio, 2),
            ohlcv_14=ohlcv_14,
            ohlcv_50=ohlcv_50,
            high_52w=high_52w,
            low_52w=low_52w,
        )
    except Exception:
        return None
