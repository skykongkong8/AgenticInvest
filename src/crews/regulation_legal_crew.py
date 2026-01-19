from src.schemas.evidence import Evidence
from src.utils.llm import get_llm, generate_text
from uuid import uuid4

class RegulationLegalCrew:
    def __init__(self):
        self.llm = get_llm()

    def execute(self, inputs: dict) -> list[Evidence]:
        ticker = inputs.get("ticker", "UNKNOWN")
        prompt = (
            "You are a regulatory analyst. Summarize legal exposure in one sentence. "
            f"Ticker: {ticker}. No recent class action lawsuits in 90 days."
        )
        fallback_claim = f"No active class action lawsuits found for {ticker} in the last 90 days."
        claim = generate_text(self.llm, prompt, fallback_claim)

        evidences = []
        evidences.append(Evidence(
            id=str(uuid4()),
            source_type="legal_db",
            source_ref="court_filings",
            claim=claim,
            confidence=0.9,
            tags=["legal", "compliance"]
        ))
        
        return evidences
