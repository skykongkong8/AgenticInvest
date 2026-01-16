import logging
import os
from datetime import datetime
from typing import List

from src.schemas.request import RequestInput
from src.schemas.report import VerdictReport
from src.schemas.evidence import Evidence
from src.schemas.plan import ResearchTaskSpec, ResearchPlan
from src.utils.io import write_json, write_text, write_jsonl

from .planner import Planner
from .triggers import TriggerEngine
from .synthesis import Synthesizer
from .verdict import VerdictEngine

# Import Crews
from src.crews.price_crew import PriceCrew
from src.crews.news_crew import NewsCrew
from src.crews.fundamentals_crew import FundamentalsCrew
from src.crews.options_liquidity_crew import OptionsLiquidityCrew
from src.crews.regulation_legal_crew import RegulationLegalCrew
from src.crews.debate_crew import DebateCrew

logger = logging.getLogger(__name__)

class OrchestratorFlow:
    def __init__(self):
        self.planner = Planner()
        self.triggers = TriggerEngine()
        self.synthesizer = Synthesizer()
        self.verdict_engine = VerdictEngine()
        
        self.crews = {
            "PriceCrew": PriceCrew(),
            "NewsCrew": NewsCrew(),
            "FundamentalsCrew": FundamentalsCrew(),
            "OptionsLiquidityCrew": OptionsLiquidityCrew(),
            "RegulationLegalCrew": RegulationLegalCrew(),
            "DebateCrew": DebateCrew()
        }

    def run(self, ticker: str, horizon: str, risk_profile: str) -> str:
        run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ticker}"
        run_dir = f"runs/{run_id}"
        os.makedirs(run_dir, exist_ok=True)
        
        request = RequestInput(ticker=ticker, horizon=horizon, risk_profile=risk_profile)
        self._log_event(run_dir, "RUN_STARTED", {"ticker": ticker, "run_id": run_id})
        
        # 1. Plan
        plan = self.planner.create_base_plan(request)
        self._log_event(run_dir, "PLAN_CREATED", {"task_count": len(plan.tasks)})
        write_json(f"{run_dir}/plan.json", plan.model_dump())
        
        # 2. Execute Base Plan
        evidences = self._execute_tasks(plan.tasks, run_dir)
        
        # 3. Synthesis & Triggers
        signals = self.synthesizer.build_signals(evidences)
        new_tasks = self.triggers.evaluate(request, evidences, signals)
        
        if new_tasks:
            self._log_event(run_dir, "TRIGGERS_FIRED", {"new_tasks": [t.name for t in new_tasks]})
            new_evidences = self._execute_tasks(new_tasks, run_dir)
            evidences.extend(new_evidences)
            
            # Re-synthesize
            signals = self.synthesizer.build_signals(evidences)
            
        write_json(f"{run_dir}/evidence.json", [e.model_dump() for e in evidences])
        
        # 4. Verdict
        verdict_label, rationale, confidence = self.verdict_engine.compute_verdict(signals, evidences)
        
        report = VerdictReport(
            request=request,
            signals=signals,
            research_plan=plan, # Note via basic plan, in real app update with new tasks
            evidence=evidences,
            verdict=verdict_label,
            rationale=rationale,
            risks=signals.news_red_flags,
            next_actions=["Monitor earnings", "Check regulatory updates"]
        )
        
        # 5. Output
        write_json(f"{run_dir}/final_report.json", report.model_dump())
        self._render_markdown(f"{run_dir}/final_report.md", report)
        
        self._log_event(run_dir, "run_COMPLETE", {"verdict": verdict_label})
        logger.info(f"Run completed. Verdict: {verdict_label}. Output: {run_dir}")
        return run_dir

    def _execute_tasks(self, tasks: List[ResearchTaskSpec], run_dir: str) -> List[Evidence]:
        results = []
        for task in tasks:
            logger.info(f"Executing task: {task.name} with {task.crew}")
            self._log_event(run_dir, "TASK_STARTED", {"task": task.name})
            
            crew_inst = self.crews.get(task.crew)
            if crew_inst:
                task_evidences = crew_inst.execute(task.inputs)
                results.extend(task_evidences)
                self._log_event(run_dir, "TASK_FINISHED", {"task": task.name, "evidence_count": len(task_evidences)})
            else:
                logger.error(f"Crew {task.crew} not found!")
                
        return results

    def _log_event(self, run_dir: str, event_type: str, data: dict):
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            **data
        }
        write_jsonl(f"{run_dir}/events.jsonl", event)

    def _render_markdown(self, path: str, report: VerdictReport):
        md = f"""# Market Research Report: {report.request.ticker}

**Verdict**: {report.verdict.value}  
**Confidence**: {0.8}  
**Date**: {report.request.requested_at}

## Executive Summary
{report.rationale['bull_case']}
{report.rationale['bear_case']}

## Signals
- Volatility (20d): {f"{report.signals.volatility_20d:.2%}" if report.signals.volatility_20d is not None else "N/A"}
- Red Flags: {len(report.signals.news_red_flags)}

## Key Evidence
"""
        for ev in report.evidence:
             cid = f"[{ev.id[:6]}]"
             md += f"- **{cid}** [{ev.source_type}] {ev.claim} (Conf: {ev.confidence})\n"
             
        md += "\n## Risks\n"
        for r in report.risks:
            md += f"- {r}\n"
            
        md += "\n---\n**Disclaimer**: Not financial advice. This report is generated by an AI system for research purposes only."
            
        write_text(path, md)
