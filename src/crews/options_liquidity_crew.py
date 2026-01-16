from src.schemas.evidence import Evidence
from uuid import uuid4

class OptionsLiquidityCrew:
    def execute(self, inputs: dict) -> list[Evidence]:
        ticker = inputs.get("ticker", "UNKNOWN")
        
        evidences = []
        evidences.append(Evidence(
            id=str(uuid4()),
            source_type="market_data",
            source_ref="options_chain",
            claim=f"High put/call ratio detected for {ticker}, indicating bearish sentiment.",
            confidence=0.75,
            tags=["options", "bearing"]
        ))
        
        return evidences
