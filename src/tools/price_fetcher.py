import random
from datetime import datetime, timedelta
from typing import List, Dict

def fetch_prices(ticker: str, days: int = 30) -> List[Dict[str, float]]:
    """
    Returns a deterministic mock OHLC series based on the ticker.
    """
    seed = sum(ord(c) for c in ticker)
    random.seed(seed)
    
    prices = []
    base_price = 100.0 + (seed % 50)
    current_date = datetime.now() - timedelta(days=days)
    
    for _ in range(days):
        # Increased volatility range to ensures trigger firing for QA
        change = (random.random() - 0.5) * 15 
        base_price += change
        prices.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "original_open": 0.0, # Not used in V0
            "close": round(base_price, 2),
            "volume": random.randint(1000000, 5000000)
        })
        current_date += timedelta(days=1)
        
    return prices
