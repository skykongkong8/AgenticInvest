# Core Feature Report: Dynamic Task Decomposition

## Overview

**Dynamic Task Decomposition** is the central intelligence mechanism of the `AgenticInvest` system. Unlike traditional linear pipelines that run a fixed sequence of steps, this Orchestrator adapts its execution plan in real-time based on the findings (Evidence) from previous steps.

This architecture allows the system to be efficient (skipping unnecessary deep dives) while remaining thorough (automatically expanding scope when risks are detected).

---

## 1. Where the Magic Happens (Code Location)

The core logic resides in two files within the `src/orchestrator/` module:

### A. The Orchestration Loop (`src/orchestrator/flow.py`)

This is the "Brain" that manages the lifecycle of the research run.

- **Location**: `src/orchestrator/flow.py`
- **Key Method**: `run(self, ticker, horizon, risk_profile)`

**Mechanism:**

1.  **Initial Plan**: Calls `self.planner.create_base_plan()` to generate the standard set of tasks (Price, News, Fundamentals).
2.  **Execution & Synthesis**: Runs the base tasks and converts raw Evidence into `Signals` (e.g., calculation volatility %, sentiment score).
3.  **Feedback Loop**: Passes the _current state_ (Request + Evidence + Signals) to the `TriggerEngine`.
4.  **Dynamic Expansion**: If the Trigger Engine returns new tasks, the Flow **appends** them to the execution queue immediately and runs them.

```python
# excerpt from src/orchestrator/flow.py
signals = self.synthesizer.build_signals(evidences)
new_tasks = self.triggers.evaluate(request, evidences, signals)

if new_tasks:
    # Key moment: The plan expands dynamically
    new_evidences = self._execute_tasks(new_tasks, run_dir)
    evidences.extend(new_evidences)
```

### B. The Trigger Engine (`src/orchestrator/triggers.py`)

This is the "Decision Logic" that contains the decomposition rules.

- **Location**: `src/orchestrator/triggers.py`
- **Key Method**: `evaluate(self, request, evidences, signals)`

**Mechanism:**
It evaluates specific conditions ("Triggers") and returns a list of _new_ `ResearchTaskSpec` objects if those conditions are met.

**Implemented Triggers:**

1.  **Volatility Spike**: If `volatility_20d > 40%`, it dynamically spawns an `OptionsLiquidityCrew` to investigate hedging costs and gamma exposure.
2.  **Regulatory Red Flags**: If keywords (e.g., "SEC", "lawsuit") appear in news, it spawns a `RegulationLegalCrew` to read court filings.
3.  **Insufficient Evidence**: If the total evidence count is too low, it spawns a fallback research task.

```python
# excerpt from src/orchestrator/triggers.py
if signals.volatility_20d and signals.volatility_20d > 0.40:
    new_tasks.append(ResearchTaskSpec(
        name="options_liquidity_analysis",
        crew="OptionsLiquidityCrew",
        ...
    ))
```

---

## 2. Walkthrough Example: The TSLL Run

We can see this feature in action using the `TSLL` run which you just executed.

1.  **Phase 1: Static Decomposition**
    The Planner scheduled the standard 3 agents.

    - `PriceCrew` -> Analyzed charts.
    - `NewsCrew` -> Scanned headlines.
    - `FundamentalsCrew` -> Checked ratios.

2.  **Phase 2: Signal Synthesis**
    The `PriceCrew` found high volatility (simulated for TSLL). The `NewsCrew` found "lawsuit" mentions in the mock data.

    - _Resulting Signal_: `volatility_20d: 0.55` (Hypothetical high value)
    - _Resulting Signal_: `news_red_flags: ["lawsuit"]`

3.  **Phase 3: Dynamic Decomposition (Trigger Event)**
    The Orchestrator sent these signals to `triggers.evaluate()`.

    - **Trigger 1 Fired**: Volatility > 0.40. -> **Action**: Spawn `OptionsLiquidityCrew`.
    - **Trigger 2 Fired**: Red Flags detected. -> **Action**: Spawn `RegulationLegalCrew`.

4.  **Phase 4: Expanded Execution**
    The system paused final verdict generation to execute these two new tasks, gathering specialized evidence that was NOT in the original plan.

---

## 3. Why This Implementation is "Agentic"

A script follows a list of commands. An Agent **perceives, decides, and acts**.

In this codebase:

- **Perception**: `src/orchestrator/synthesis.py` (Turning raw data into structured Signals).
- **Decision**: `src/orchestrator/triggers.py` (Deciding if the current information is sufficient or if risks exist).
- **Action**: `src/orchestrator/flow.py` (Modifying its own future actions by appending tasks).

This separation of concerns makes the system highly extensible. You can add a new "Scenario" (e.g., Merger Arbitrage) simply by adding a new Trigger rule, without rewriting the main orchestration flow.
