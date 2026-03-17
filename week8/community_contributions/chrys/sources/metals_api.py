"""CommodityPriceAPI adapter for gold (XAU) and silver (XAG)."""
import requests

from models import AssetData

BASE = "https://api.commoditypriceapi.com/v2"


def _symbol_to_code(symbol: str) -> str | None:
    s = symbol.upper().replace("/USD", "").strip()
    if s == "XAU":
        return "XAU"
    if s == "XAG":
        return "XAG"
    return None


def fetch_metals(symbol: str, api_key: str = "") -> AssetData | None:
    code = _symbol_to_code(symbol)
    if not code:
        return None
    if not api_key:
        return None
    try:
        r = requests.get(
            f"{BASE}/rates/latest",
            params={"apiKey": api_key, "symbols": code},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        if not data.get("success", False):
            return None
        rates = data.get("rates", {})
        # rates can be { "XAU": 1792.9 } or nested by symbol
        price = rates.get(code)
        if price is None and isinstance(rates, dict):
            for v in rates.values():
                if isinstance(v, (int, float)):
                    price = float(v)
                    break
        else:
            price = float(price) if price is not None else None
        if price is None or price <= 0:
            return None
        return AssetData(
            asset=symbol,
            price=price,
            change_1h="",
            change_24h="",
            volume_ratio=1.0,
            ohlcv_14=[],
            ohlcv_50=[],
            high_52w=price,
            low_52w=price,
        )
    except Exception:
        return None
