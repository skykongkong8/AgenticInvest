from src.schemas.evidence import Evidence
from src.utils.llm import get_llm, generate_text
from uuid import uuid4

class FundamentalsCrew:
    def __init__(self):
        self.llm = get_llm()

    def execute(self, inputs: dict) -> list[Evidence]:
        ticker = inputs.get("ticker", "UNKNOWN")
        
        # Mock fundamentals
        pe_ratio = 25.4
        result = "undervalued" if pe_ratio < 20 else "overvalued"
        prompt = (
            "You are a fundamental analyst. Write one sentence interpreting the valuation. "
            f"Ticker: {ticker}. P/E ratio: {pe_ratio}. Conclusion: {result}."
        )
        fallback_claim = f"{ticker} has a P/E ratio of {pe_ratio}, considering it {result}"
        claim = generate_text(self.llm, prompt, fallback_claim)

        evidences = []
        evidences.append(Evidence(
            id=str(uuid4()),
            source_type="analysis",
            source_ref="10-K",
            claim=claim,
            confidence=0.85,
            tags=["valuation", "fundamental"]
        ))
        
        return evidences
