from src.schemas.evidence import Evidence
from src.utils.llm import get_llm, generate_text
from uuid import uuid4

class DebateCrew:
    def __init__(self):
        self.llm = get_llm()

    def execute(self, inputs: dict) -> list[Evidence]:
        ticker = inputs.get("ticker", "UNKNOWN")
        prompt = (
            "You are a market research analyst. Summarize a bull/bear debate in one sentence. "
            "Make the conclusion explicit and mention the primary risk driver. "
            f"Ticker: {ticker}."
        )
        fallback_claim = (
            f"After debating bull/bear cases for {ticker}, the bear case regarding regulatory risk "
            "is deemed more significant."
        )
        claim = generate_text(self.llm, prompt, fallback_claim)

        evidences = []
        evidences.append(Evidence(
            id=str(uuid4()),
            source_type="synthesis",
            source_ref="debate_session",
            claim=claim,
            confidence=0.6,
            tags=["debate", "verdict"]
        ))
        
        return evidences
