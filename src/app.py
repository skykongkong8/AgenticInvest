from .orchestrator.flow import OrchestratorFlow

def run_research(ticker: str, horizon: str = "1m", risk_profile: str = "normal"):
    flow = OrchestratorFlow()
    return flow.run(ticker, horizon, risk_profile)
