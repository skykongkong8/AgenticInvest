from src.schemas.evidence import Evidence
from uuid import uuid4

class FundamentalsCrew:
    def execute(self, inputs: dict) -> list[Evidence]:
        ticker = inputs.get("ticker", "UNKNOWN")
        
        # Mock fundamentals
        pe_ratio = 25.4
        result = "undervalued" if pe_ratio < 20 else "overvalued"
        
        evidences = []
        evidences.append(Evidence(
            id=str(uuid4()),
            source_type="analysis",
            source_ref="10-K",
            claim=f"{ticker} has a P/E ratio of {pe_ratio}, considering it {result}",
            confidence=0.85,
            tags=["valuation", "fundamental"]
        ))
        
        return evidences
