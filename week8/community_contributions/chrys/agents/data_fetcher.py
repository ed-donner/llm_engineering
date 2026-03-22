"""DATA_FETCHER agent: retrieves live and historical price data from APIs."""
import time
from typing import List

from agents.base import AgentBase
from models import AssetData

# Import sources - use late or local refs to avoid circular deps
def _get_sources():
    from sources.alpha_vantage import fetch_alpha_vantage
    from sources.metals_api import fetch_metals
    from sources.coingecko import fetch_coingecko
    return fetch_alpha_vantage, fetch_metals, fetch_coingecko


class DataFetcherAgent(AgentBase):
    name = "DATA_FETCHER"
    logger_name = "aria.data_fetcher"

    def __init__(self, alpha_key: str = "", metals_key: str = ""):
        super().__init__()
        self.alpha_key = alpha_key
        # metals_key = CommodityPriceAPI key for gold (XAU) and silver (XAG)
        self.metals_key = metals_key

    def _route(self, symbol: str) -> str:
        s = symbol.upper().replace("/USD", "").strip()
        if s in ("XAU", "XAG"):
            return "metals"
        if s in ("BTC", "ETH"):
            return "coingecko"
        return "alpha"  # stocks, indices, WTI, Copper via Alpha Vantage

    def fetch_one(self, symbol: str) -> AssetData | None:
        route = self._route(symbol)
        fetch_av, fetch_metals, fetch_cg = _get_sources()
        for attempt in range(2):
            try:
                if route == "metals":
                    out = fetch_metals(symbol, self.metals_key)
                elif route == "coingecko":
                    out = fetch_cg(symbol, "")
                else:
                    out = fetch_av(symbol, self.alpha_key)
                if out:
                    return out
            except Exception as e:
                self.log(f"Fetch {symbol} attempt {attempt + 1} failed: {e}")
                if attempt == 0:
                    time.sleep(10)
        return None

    def run(self, watchlist: List[str]) -> List[AssetData]:
        self.log("Starting data fetch for watchlist")
        results: List[AssetData] = []
        for symbol in watchlist:
            data = self.fetch_one(symbol)
            if data:
                results.append(data)
                self.log(f"Fetched {symbol}: {data.price}")
            else:
                self.log(f"Skipped {symbol} (fetch failed)")
        self.log(f"Fetched {len(results)}/{len(watchlist)} assets")
        return results
