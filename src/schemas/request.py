from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class RequestInput(BaseModel):
    ticker: str
    horizon: str = Field(pattern="^(1w|1m|3m|1y)$")
    risk_profile: str = Field(pattern="^(conservative|normal|aggressive)$")
    portfolio_context: Optional[str] = None
    requested_at: datetime = Field(default_factory=datetime.utcnow)
