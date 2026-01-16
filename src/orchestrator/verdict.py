from typing import List, Dict, Tuple
from src.schemas.report import Verdict, Signals
from src.schemas.evidence import Evidence

class VerdictEngine:
    def compute_verdict(self, signals: Signals, evidences: List[Evidence]) -> Tuple[Verdict, Dict[str, str], float]:
        score = 0.0
        rationale = {"bull_case": [], "bear_case": []}
        
        # 1. Feature-based Scoring
        
        # Sentiment
        if signals.sentiment_score > 0.3:
            score += 1.0
            rationale["bull_case"].append(f"Strong positive sentiment ({signals.sentiment_score:.2f}).")
        elif signals.sentiment_score < -0.3:
            score -= 1.0
            rationale["bear_case"].append(f"Negative sentiment ({signals.sentiment_score:.2f}).")
            
        # Momentum/Valuation
        if signals.momentum_score > 0:
            score += 1.0
        elif signals.momentum_score < 0:
            score -= 1.0
            
        # Risks
        if signals.volatility_risk > 0.7:
            score -= 0.5
            rationale["bear_case"].append(f"High volatility risk ({signals.volatility_risk:.1f}).")
            
        if signals.event_risk > 0.5:
            score -= 2.0
            rationale["bear_case"].append(f"Significant event/regulatory risk detected.")
            
        # 2. Evidence Citation Mapping
        # We try to link specific evidence to general points
        
        for ev in evidences:
            cid = f"[{ev.id[:6]}]"
            
            # Map evidence to bull/bear based on content (naive keyword matching)
            # In a real system, the Synthesizer would tag evidence as supporting bull or bear
            if "undervalued" in ev.claim or "positive" in ev.claim or "Buy" in ev.claim:
                rationale["bull_case"].append(f"{ev.claim} {cid}")
            elif "overvalued" in ev.claim or "negative" in ev.claim or "risk" in ev.claim or "red flags" in ev.claim:
                rationale["bear_case"].append(f"{ev.claim} {cid}")
                
        # 3. Determine Verdict
        confidence = max(0.0, 1.0 - signals.uncertainty)
        
        if score >= 1.5:
            verdict = Verdict.STRONG_BUY
        elif score >= 0.5:
            verdict = Verdict.BUY
        elif score <= -1.5:
            verdict = Verdict.STRONG_SELL
        elif score <= -0.5:
            verdict = Verdict.SELL
        else:
            verdict = Verdict.HOLD
            
        # 4. Final Formatting
        final_rationale = {
            "bull_case": "\n- ".join(rationale["bull_case"]) if rationale["bull_case"] else "No major bull signals.",
            "bear_case": "\n- ".join(rationale["bear_case"]) if rationale["bear_case"] else "No major bear signals."
        }
        
        # Prepend bullet if list is string
        if rationale["bull_case"]:
             final_rationale["bull_case"] = "- " + final_rationale["bull_case"]
        if rationale["bear_case"]:
             final_rationale["bear_case"] = "- " + final_rationale["bear_case"]
            
        return verdict, final_rationale, confidence
