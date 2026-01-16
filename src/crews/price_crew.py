from src.schemas.evidence import Evidence
from src.tools.price_fetcher import fetch_prices
from src.tools.signal_calculators import compute_volatility, compute_drawdown
from uuid import uuid4

class PriceCrew:
    def execute(self, inputs: dict) -> list[Evidence]:
        ticker = inputs.get("ticker", "UNKNOWN")
        prices = fetch_prices(ticker)
        
        volatility = compute_volatility(prices)
        drawdown = compute_drawdown(prices)
        
        evidences = []
        evidences.append(Evidence(
            id=str(uuid4()),
            source_type="price",
            source_ref="mock_price_feed",
            claim=f"Volatility for {ticker} is {volatility:.2%}",
            confidence=0.95,
            raw_snippet=str(prices[-5:]),
            tags=["volatility", "risk"]
        ))
        evidences.append(Evidence(
            id=str(uuid4()),
            source_type="price",
            source_ref="mock_price_feed",
            claim=f"Max drawdown for {ticker} is {drawdown:.2%}",
            confidence=1.0,
            tags=["drawdown", "risk"]
        ))
        
        return evidences
