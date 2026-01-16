from datetime import datetime, timedelta
from typing import List, Dict

def fetch_news(ticker: str, days: int = 7) -> List[Dict[str, str]]:
    """
    Returns deterministic mock news articles.
    """
    mock_articles = [
        {"title": f"{ticker} announces record breaking quarterly results", "sentiment": "positive"},
        {"title": f"Analyst upgrades {ticker} to Buy", "sentiment": "positive"},
        {"title": f"Supply chain issues affect {ticker}", "sentiment": "negative"},
        {"title": f"{ticker} CEO faces lawsuit over tweets", "sentiment": "negative"},
        {"title": f"{ticker} unveils new product line", "sentiment": "positive"},
    ]
    
    # Deterministic selection based on ticker
    seed = sum(ord(c) for c in ticker)
    selected = []
    current_date = datetime.now()
    
    for i, article in enumerate(mock_articles):
        # Rotate through articles based on ticker seed
        if (seed + i) % 2 == 0:
            article_copy = article.copy()
            article_copy["date"] = (current_date - timedelta(days=i)).isoformat()
            article_copy["snippet"] = f"Full content of {article['title']}..."
            selected.append(article_copy)
            
    return selected
