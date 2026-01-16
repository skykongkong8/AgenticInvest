from typing import List, Dict, Optional
from pydantic import BaseModel
from enum import Enum
from .request import RequestInput
from .evidence import Evidence
from .plan import ResearchPlan

class Verdict(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    DO_NOT_TOUCH = "DO_NOT_TOUCH"

class Signals(BaseModel):
    volatility_20d: Optional[float] = None
    drawdown_20d: Optional[float] = None
    news_red_flags: List[str] = []
    
    # New V1 features
    momentum_score: float = 0.0     # -1.0 to 1.0
    volatility_risk: float = 0.0    # 0.0 to 1.0
    event_risk: float = 0.0         # 0.0 to 1.0
    sentiment_score: float = 0.0    # -1.0 to 1.0
    uncertainty: float = 0.0        # 0.0 to 1.0
    conflict_score: Optional[float] = None

class VerdictReport(BaseModel):
    request: RequestInput
    signals: Signals
    research_plan: ResearchPlan
    evidence: List[Evidence]
    verdict: Verdict
    rationale: Dict[str, str]  # e.g., Keys: "bull_case", "bear_case", with citations
    risks: List[str]
    next_actions: List[str]
