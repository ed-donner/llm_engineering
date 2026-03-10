"""CoinGecko adapter for crypto (BTC, ETH)."""
import requests

from models import AssetData

BASE = "https://api.coingecko.com/api/v3"

COIN_IDS = {"BTC/USD": "bitcoin", "BTC": "bitcoin", "ETH/USD": "ethereum", "ETH": "ethereum"}


def _symbol_to_id(symbol: str) -> str | None:
    s = symbol.upper().strip()
    s_clean = s.replace("/USD", "").strip()
    return COIN_IDS.get(s) or COIN_IDS.get(s_clean)


def fetch_coingecko(symbol: str, _api_key: str = "") -> AssetData | None:
    cid = _symbol_to_id(symbol)
    if not cid:
        return None
    try:
        # Price + 24h change
        r = requests.get(
            BASE + "/simple/price",
            params={"ids": cid, "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get(cid, {})
        price = float(data.get("usd", 0))
        change_24 = data.get("usd_24h_change") or 0
        change_24h = f"{float(change_24):+.2f}%"

        # Market chart for OHLC-like series (last 50 days)
        m = requests.get(
            BASE + f"/coins/{cid}/market_chart",
            params={"vs_currency": "usd", "days": "60"},
            timeout=10,
        )
        m.raise_for_status()
        mc = m.json()
        prices = mc.get("prices", [])[:50]
        volumes = {t: v for t, v in mc.get("total_volumes", [])}
        ohlcv_50 = []
        for i, (ts, p) in enumerate(prices):
            v = volumes.get(ts, 0) or 0
            ohlcv_50.append({"t": ts, "o": p, "h": p, "l": p, "c": p, "v": v})
        ohlcv_14 = ohlcv_50[:14]
        if len(ohlcv_50) >= 20:
            vol_avg = sum(ohlcv_50[i].get("v", 0) for i in range(20)) / 20
            last_vol = ohlcv_50[0].get("v", 1) or 1
            vol_ratio = last_vol / vol_avg if vol_avg else 1.0
        else:
            vol_ratio = 1.0
        highs = [x["h"] for x in ohlcv_50]
        lows = [x["l"] for x in ohlcv_50]
        return AssetData(
            asset=symbol,
            price=price,
            change_1h="",
            change_24h=change_24h,
            volume_ratio=round(vol_ratio, 2),
            ohlcv_14=ohlcv_14,
            ohlcv_50=ohlcv_50,
            high_52w=max(highs) if highs else price,
            low_52w=min(lows) if lows else price,
        )
    except Exception:
        return None
