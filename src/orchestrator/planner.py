from typing import List
from uuid import uuid4
from src.schemas.request import RequestInput
from src.schemas.plan import ResearchPlan, ResearchTaskSpec

class Planner:
    def create_base_plan(self, request: RequestInput) -> ResearchPlan:
        tasks = []
        
        # Base Tasks
        tasks.append(ResearchTaskSpec(
            id=str(uuid4()),
            name="price_analysis",
            description="Fetch and analyze OHLC price data, volatility, and drawdowns.",
            crew="PriceCrew",
            inputs={"ticker": request.ticker, "horizon": request.horizon},
            parallelizable=True
        ))
        
        tasks.append(ResearchTaskSpec(
            id=str(uuid4()),
            name="news_analysis",
            description="Fetch news and sentiment analysis.",
            crew="NewsCrew",
            inputs={"ticker": request.ticker, "days": 30},
            parallelizable=True
        ))
        
        tasks.append(ResearchTaskSpec(
            id=str(uuid4()),
            name="fundamental_analysis",
            description="Analyze basic fundamental ratios.",
            crew="FundamentalsCrew",
            inputs={"ticker": request.ticker},
            parallelizable=True
        ))
        
        return ResearchPlan(tasks=tasks)
