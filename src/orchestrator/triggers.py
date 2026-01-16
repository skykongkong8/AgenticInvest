from typing import List, Optional
from src.schemas.evidence import Evidence
from src.schemas.plan import ResearchTaskSpec, ResearchPlan
from src.schemas.report import Signals
from src.schemas.request import RequestInput
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

class TriggerEngine:
    def evaluate(self, request: RequestInput, evidences: List[Evidence], signals: Signals) -> List[ResearchTaskSpec]:
        new_tasks = []
        
        # 1. Volatility Spike
        if signals.volatility_20d and signals.volatility_20d > 0.40: # 40% threshold example
            logger.info("TRIGGER: Volatility spike detected")
            new_tasks.append(ResearchTaskSpec(
                id=str(uuid4()),
                name="options_liquidity_analysis",
                description="Investigate options flow and liquidity due to high volatility.",
                crew="OptionsLiquidityCrew",
                inputs={"ticker": request.ticker},
                parallelizable=False
            ))

        # 2. Legal/Regulatory
        if signals.news_red_flags:
            logger.info("TRIGGER: Legal/Regulatory red flags detected")
            new_tasks.append(ResearchTaskSpec(
                id=str(uuid4()),
                name="legal_analysis",
                description="Deep dive into identified legal risks.",
                crew="RegulationLegalCrew",
                inputs={"ticker": request.ticker, "issues": signals.news_red_flags},
                parallelizable=False
            ))
            
        # 3. Conflicting Evidence (Mock logic: if we have mixed sentiment strong signals)
        # Simplified: Check if we have both strong buy and strong sell signals (not impl in mock thoroughly, but placeholder)
        
        # 4. Insufficient Evidence
        if len(evidences) < 3: # Arbitrary low number
             new_tasks.append(ResearchTaskSpec(
                id=str(uuid4()),
                name="supplementary_research",
                description="Gather more evidence due to low count.",
                crew="NewsCrew", # Fallback to more news
                inputs={"ticker": request.ticker, "days": 90},
                parallelizable=True
            ))
            
        return new_tasks
