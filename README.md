# CrewAI Dynamic Market Research Orchestrator

A production-grade skeleton for an event-driven deep research pipeline using CrewAI, Flow-based orchestration, and structured evidence gathering.

## Goal

Scenario 1: Single US Stock (ticker) Event-Driven Deep Research.

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # or
   pip install .
   ```
2. Run the CLI:
   ```bash
   python -m src.cli --ticker TSLA --horizon 1m --risk normal
   ```

## Architecture

- **Orchestrator**: Flow-based logic handling planning, triggers, and synthesis.
- **Agents**: CrewAI agents focused on specific research domains (Price, News, Fundamentals, etc.).
- **Tools**: Mock implementations for data fetching.
- **Artifacts**: All runs are saved to `runs/<timestamp>_<ticker>/`.

## Rules

See `docs/crewai_market_research_global_rules.md` for the project constitution.
# AgenticInvest
