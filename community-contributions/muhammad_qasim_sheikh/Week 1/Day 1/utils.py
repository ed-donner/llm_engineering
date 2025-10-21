# utils.py

import requests
import re
import datetime
import logging
from typing import Dict, Optional, Union

# -----------------------------------------
# Logging setup
# -----------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------
# Braiins API endpoints (7 selected)
# -----------------------------------------
BRAIINS_APIS = {
    'price_stats': 'https://insights.braiins.com/api/v1.0/price-stats',
    'hashrate_stats': 'https://insights.braiins.com/api/v1.0/hashrate-stats',
    'difficulty_stats': 'https://insights.braiins.com/api/v1.0/difficulty-stats',
    'transaction_fees_history': 'https://insights.braiins.com/api/v1.0/transaction-fees-history',
    'daily_revenue_history': 'https://insights.braiins.com/api/v1.0/daily-revenue-history',
    'hashrate_value_history': 'https://insights.braiins.com/api/v1.0/hashrate-value-history',
    'halvings': 'https://insights.braiins.com/api/v2.0/halvings'
}


# -----------------------------------------
# Utility Functions
# -----------------------------------------
def clean_value(value):
    """Clean strings, remove brackets/quotes and standardize whitespace."""
    if value is None:
        return ""
    s = str(value)
    s = s.replace(",", " ")
    s = re.sub(r"[\[\]\{\}\(\)]", "", s)
    s = s.replace('"', "").replace("'", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def parse_date(date_str: str) -> Optional[str]:
    """Parse dates into a standard readable format."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        if 'T' in date_str:
            return datetime.datetime.fromisoformat(date_str.replace('Z', '').split('.')[0]).strftime('%Y-%m-%d %H:%M:%S')
        if '-' in date_str and len(date_str) == 10:
            return datetime.datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
        if '/' in date_str and len(date_str) == 10:
            return datetime.datetime.strptime(date_str, '%m/%d/%Y').strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return date_str
    return date_str


def fetch_endpoint_data(url: str) -> Optional[Union[Dict, list]]:
    """Generic GET request to Braiins API endpoint."""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def clean_and_process_data(data: Union[Dict, list]) -> Union[Dict, list]:
    """Clean all keys and values in the fetched data."""
    if isinstance(data, dict):
        return {clean_value(k): clean_value(v) for k, v in data.items()}
    elif isinstance(data, list):
        cleaned_list = []
        for item in data:
            if isinstance(item, dict):
                cleaned_list.append({clean_value(k): clean_value(v) for k, v in item.items()})
            else:
                cleaned_list.append(clean_value(item))
        return cleaned_list
    return clean_value(data)


# -----------------------------------------
# Main data fetcher
# -----------------------------------------
def fetch_clean_data(history_limit: int = 30) -> Dict[str, Union[Dict, list]]:
    """
    Fetch and clean data from 7 selected Braiins endpoints.
    For historical data, it limits the number of records.
    Returns a dictionary ready to be passed into an LLM.
    """
    logger.info("Fetching Bitcoin network data from Braiins...")
    results = {}

    for key, url in BRAIINS_APIS.items():
        logger.info(f"Fetching {key} ...")
        raw_data = fetch_endpoint_data(url)
        if raw_data is not None:
            # --- START OF THE NEW CODE ---
            # If the endpoint is for historical data, limit the number of records
            if "history" in key and isinstance(raw_data, list):
                logger.info(f"Limiting {key} data to the last {history_limit} records.")
                raw_data = raw_data[-history_limit:]
            # --- END OF THE NEW CODE ---

            results[key] = clean_and_process_data(raw_data)
        else:
            results[key] = {"error": "Failed to fetch"}

    logger.info("All data fetched and cleaned successfully.")
    return results

# -----------------------------------------
# Local test run (optional)
# -----------------------------------------
if __name__ == "__main__":
    data = fetch_clean_data()
    print("Sample keys fetched:", list(data.keys()))
