from datetime import datetime
from src.schemas.request import RequestInput
from src.schemas.evidence import Evidence

def test_request_input_validation():
    req = RequestInput(ticker="TSLA", horizon="1m", risk_profile="normal")
    assert req.ticker == "TSLA"
    
    try:
        RequestInput(ticker="TSLA", horizon="invalid", risk_profile="normal")
        assert False, "Should fail validation"
    except ValueError:
        pass

def test_evidence_serialization():
    ev = Evidence(
        id="123", source_type="news", source_ref="http", claim="test", confidence=0.9
    )
    data = ev.model_dump()
    assert data["confidence"] == 0.9
