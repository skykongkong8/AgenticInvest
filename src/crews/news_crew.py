from src.schemas.evidence import Evidence
from src.tools.news_fetcher import fetch_news
from src.tools.signal_calculators import check_red_flags
from uuid import uuid4

class NewsCrew:
    def execute(self, inputs: dict) -> list[Evidence]:
        ticker = inputs.get("ticker", "UNKNOWN")
        news_items = fetch_news(ticker)
        red_flags = check_red_flags(news_items)
        
        evidences = []
        
        # General Sentiment
        evidences.append(Evidence(
            id=str(uuid4()),
            source_type="news",
            source_ref="mock_news_api",
            claim=f"Found {len(news_items)} recent articles for {ticker}",
            confidence=0.8,
            tags=["volume", "sentiment"]
        ))
        
        # Red Flags
        if red_flags:
            evidences.append(Evidence(
                id=str(uuid4()),
                source_type="news",
                source_ref="mock_news_api",
                claim=f"Identified potential red flags: {', '.join(red_flags)}",
                confidence=0.7,
                tags=["risk", "legal"]
            ))
            
        return evidences
