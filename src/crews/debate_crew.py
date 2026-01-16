from src.schemas.evidence import Evidence
from uuid import uuid4

class DebateCrew:
    def execute(self, inputs: dict) -> list[Evidence]:
        ticker = inputs.get("ticker", "UNKNOWN")
        
        evidences = []
        evidences.append(Evidence(
            id=str(uuid4()),
            source_type="synthesis",
            source_ref="debate_session",
            claim=f"After debating bull/bear cases for {ticker}, the bear case regarding regulatory risk is deemed more significant.",
            confidence=0.6,
            tags=["debate", "verdict"]
        ))
        
        return evidences
