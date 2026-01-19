from src.schemas.evidence import Evidence
from src.utils.llm import get_llm, generate_text
from uuid import uuid4

class OptionsLiquidityCrew:
    def __init__(self):
        self.llm = get_llm()

    def execute(self, inputs: dict) -> list[Evidence]:
        ticker = inputs.get("ticker", "UNKNOWN")
        prompt = (
            "You are an options market analyst. Summarize the put/call signal in one sentence. "
            f"Ticker: {ticker}. Signal: high put/call ratio."
        )
        fallback_claim = f"High put/call ratio detected for {ticker}, indicating bearish sentiment."
        claim = generate_text(self.llm, prompt, fallback_claim)

        evidences = []
        evidences.append(Evidence(
            id=str(uuid4()),
            source_type="market_data",
            source_ref="options_chain",
            claim=claim,
            confidence=0.75,
            tags=["options", "bearing"]
        ))
        
        return evidences
