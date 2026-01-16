from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class Evidence(BaseModel):
    id: str
    source_type: str  # price|news|filing|analysis
    source_ref: str
    claim: str
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_snippet: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
