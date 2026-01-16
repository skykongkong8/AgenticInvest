from typing import List
from src.schemas.evidence import Evidence
from src.schemas.report import Signals

class Synthesizer:
    def build_signals(self, evidences: List[Evidence]) -> Signals:
        # Base Raw Signals
        volatility = None
        drawdown = None
        red_flags = []
        
        # New Features Accumulators
        sentiment_sum = 0.0
        sentiment_count = 0
        
        momentum_sum = 0.0
        momentum_count = 0
        
        event_risk_score = 0.0
        uncertainty_accum = 0.0
        
        for ev in evidences:
            # 1. Parse Volatility/Drawdown (Price)
            if "volatility" in ev.tags and "Volatility for" in ev.claim:
                try:
                    val_str = ev.claim.split(" is ")[-1].replace("%", "")
                    volatility = float(val_str) / 100.0
                except:
                    pass
            
            if "drawdown" in ev.tags and "drawdown for" in ev.claim:
                    try:
                         val_str = ev.claim.split(" is ")[-1].replace("%", "")
                         drawdown = float(val_str) / 100.0
                    except:
                        pass
            
            # 2. News/Legal Red Flags
            if "legal" in ev.tags and "red flags" in ev.claim:
                # "Identified potential red flags: flag1, flag2"
                flags = ev.claim.split(": ")[-1].split(", ")
                red_flags.extend(flags)
                event_risk_score = max(event_risk_score, 0.9) # High risk if red flags
            
            # 3. Sentiment Extraction
            if "sentiment" in ev.tags or "news" in ev.source_type:
                # Mock logic: look for keywords in claim
                if "record breaking" in ev.claim or "positive" in ev.claim or "Buy" in ev.claim:
                    sentiment_sum += 0.8
                    sentiment_count += 1
                elif "lawsuit" in ev.claim or "negative" in ev.claim:
                    sentiment_sum -= 0.8
                    sentiment_count += 1
                    
            # 4. Momentum/Valuation
            if "valuation" in ev.tags:
                if "undervalued" in ev.claim:
                    momentum_sum += 0.5
                    momentum_count += 1
                elif "overvalued" in ev.claim:
                    momentum_sum -= 0.5
                    momentum_count += 1
                    
            # 5. Uncertainty
            # If evidence confidence is low, uncertainty is high
            uncertainty_accum += (1.0 - ev.confidence)

        # Compute Final Feature Scores
        final_sentiment = sentiment_sum / sentiment_count if sentiment_count > 0 else 0.0
        final_momentum = momentum_sum / momentum_count if momentum_count > 0 else 0.0
        
        # Volatility Risk mapping
        vol_risk = 0.0
        if volatility:
            if volatility > 0.4: vol_risk = 0.9
            elif volatility > 0.2: vol_risk = 0.5
            else: vol_risk = 0.1
            
        # Uncertainty normalization
        avg_uncertainty = uncertainty_accum / len(evidences) if evidences else 1.0

        return Signals(
            volatility_20d=volatility,
            volatility_risk=vol_risk,
            drawdown_20d=drawdown,
            news_red_flags=red_flags,
            event_risk=event_risk_score,
            sentiment_score=final_sentiment,
            momentum_score=final_momentum,
            uncertainty=avg_uncertainty,
            conflict_score=0.1 
        )
