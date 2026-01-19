from src.schemas.evidence import Evidence
from src.tools.news_fetcher import fetch_news
from src.tools.signal_calculators import check_red_flags
from src.utils.llm import get_llm, generate_text
from uuid import uuid4

class NewsCrew:
    def __init__(self):
        self.llm = get_llm()

    def execute(self, inputs: dict) -> list[Evidence]:
        ticker = inputs.get("ticker", "UNKNOWN")
        news_items = fetch_news(ticker)
        red_flags = check_red_flags(news_items)
        
        evidences = []
        
        # General Sentiment
        prompt = (
            "You are a news analyst. Summarize the recent coverage volume in one sentence. "
            f"Ticker: {ticker}. Article count: {len(news_items)}."
        )
        fallback_claim = f"Found {len(news_items)} recent articles for {ticker}"
        claim = generate_text(self.llm, prompt, fallback_claim)
        evidences.append(Evidence(
            id=str(uuid4()),
            source_type="news",
            source_ref="mock_news_api",
            claim=claim,
            confidence=0.8,
            tags=["volume", "sentiment"]
        ))
        
        # Red Flags
        if red_flags:
            red_flag_prompt = (
                "You are a risk analyst. Summarize the red flags in one sentence. "
                f"Ticker: {ticker}. Red flags: {', '.join(red_flags)}."
            )
            red_flag_fallback = f"Identified potential red flags: {', '.join(red_flags)}"
            red_flag_claim = generate_text(self.llm, red_flag_prompt, red_flag_fallback)
            evidences.append(Evidence(
                id=str(uuid4()),
                source_type="news",
                source_ref="mock_news_api",
                claim=red_flag_claim,
                confidence=0.7,
                tags=["risk", "legal"]
            ))
            
        return evidences
