from src.schemas.evidence import Evidence
from src.tools.price_fetcher import fetch_prices
from src.tools.signal_calculators import compute_volatility, compute_drawdown
from src.utils.llm import get_llm, generate_text
from uuid import uuid4

class PriceCrew:
    def __init__(self):
        self.llm = get_llm()

    def execute(self, inputs: dict) -> list[Evidence]:
        ticker = inputs.get("ticker", "UNKNOWN")
        prices = fetch_prices(ticker)
        
        volatility = compute_volatility(prices)
        drawdown = compute_drawdown(prices)

        volatility_prompt = (
            "You are a quant analyst. Summarize the volatility signal in one sentence. "
            f"Ticker: {ticker}. Volatility (annualized): {volatility:.2%}."
        )
        volatility_fallback = f"Volatility for {ticker} is {volatility:.2%}"
        volatility_claim = generate_text(self.llm, volatility_prompt, volatility_fallback)

        drawdown_prompt = (
            "You are a risk analyst. Summarize the drawdown in one sentence. "
            f"Ticker: {ticker}. Max drawdown: {drawdown:.2%}."
        )
        drawdown_fallback = f"Max drawdown for {ticker} is {drawdown:.2%}"
        drawdown_claim = generate_text(self.llm, drawdown_prompt, drawdown_fallback)

        evidences = []
        evidences.append(Evidence(
            id=str(uuid4()),
            source_type="price",
            source_ref="mock_price_feed",
            claim=volatility_claim,
            confidence=0.95,
            raw_snippet=str(prices[-5:]),
            tags=["volatility", "risk"]
        ))
        evidences.append(Evidence(
            id=str(uuid4()),
            source_type="price",
            source_ref="mock_price_feed",
            claim=drawdown_claim,
            confidence=1.0,
            tags=["drawdown", "risk"]
        ))
        
        return evidences
