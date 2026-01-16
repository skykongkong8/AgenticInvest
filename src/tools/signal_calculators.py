from typing import List, Dict
import math

def compute_volatility(prices: List[Dict[str, float]]) -> float:
    if not prices:
        return 0.0
    closes = [p["close"] for p in prices]
    if len(closes) < 2:
        return 0.0
        
    returns = [(closes[i] - closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret)**2 for r in returns) / len(returns)
    return math.sqrt(variance) * math.sqrt(252) # Annualized

def compute_drawdown(prices: List[Dict[str, float]]) -> float:
    if not prices:
        return 0.0
    closes = [p["close"] for p in prices]
    peak = closes[0]
    max_dd = 0.0
    
    for p in closes:
        if p > peak:
            peak = p
        dd = (p - peak) / peak
        if dd < max_dd:
            max_dd = dd
            
    return max_dd

def check_red_flags(news: List[Dict[str, str]]) -> List[str]:
    red_flags = []
    keywords = ["lawsuit", "SEC", "DOJ", "recall", "regulator", "investigation"]
    
    for article in news:
        text = (article.get("title", "") + " " + article.get("snippet", "")).lower()
        for k in keywords:
            if k in text:
                red_flags.append(f"Found '{k}' in article: {article.get('title')}")
                
    return red_flags
