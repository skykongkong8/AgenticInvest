# Project Constitution (Global Rules)

**Project:** CrewAI Dynamic Market Research Orchestrator (Scenario 1: Single US Stock, Event-Driven Deep Research)  
**Audience:** Antigravity (code generation agent) + human reviewers  
**Language:** All Antigravity prompts MUST be in English.

---

## R0. Scope and Goal

- **Input:** `ticker`, `horizon` (`1w|1m|3m|1y`), `risk_profile` (`conservative|normal|aggressive`), optional `portfolio_context`.
- **Output:**
  1. `final_report.json` (machine-consumable)
  2. `final_report.md` (human-readable)
- The system provides **evidence-based decision support**, not certainty or guaranteed outcomes.
- Verdict labels (fixed enum):
  - `STRONG_BUY`, `BUY`, `HOLD`, `SELL`, `STRONG_SELL`, `DO_NOT_TOUCH`

---

## R1. Responsibility Separation (Non-Negotiable)

- **Orchestrator (Flow)** is responsible for: planning, dynamic task decomposition, scheduling, evidence aggregation, synthesis, final decision.
- **Agents** are responsible for: research, analysis, writing, and producing structured outputs.
- **Tools** are responsible for: data retrieval (prices/news), parsing, calculation, and caching.
- Do NOT hide critical logic inside prompts. Implement orchestration logic explicitly in code/policy.

---

## R2. Evidence-First Contract

All agent work products must be recorded as **Evidence** objects and stored in the run output.
Minimum Evidence schema (must exist in code):

- `id`
- `source_type` (e.g., `price|news|filing|analysis`)
- `source_ref` (URL, dataset key, or local cache reference)
- `claim` (single, testable statement)
- `confidence` (0.0–1.0)
- `timestamp` (ISO 8601)
- `raw_snippet` (optional, short excerpt)

**No verdict without cited evidence.** Every major claim in the final report must link to at least one Evidence item.

---

## R3. Stable JSON I/O Contracts

- Orchestrator input is a single dict conforming to `RequestInput` schema.
- Orchestrator output is a single dict conforming to `VerdictReport` schema.
- Top-level output keys are fixed and must always exist:
  - `request`, `signals`, `research_plan`, `evidence`, `verdict`, `rationale`, `risks`, `next_actions`

---

## R4. Dynamic Task Decomposition via Explicit Triggers Only

The orchestrator may spawn additional tasks/crews **only** when a trigger fires.
Triggers are centralized in a registry/config and evaluated deterministically.

Initial trigger set (extend later):

- `volatility_spike`: unusual volatility / sharp drawdown / gap events → spawn options/liquidity analysis
- `legal_or_regulatory`: news mentions lawsuit/regulator/recall/SEC/DOJ, etc. → spawn legal/regulatory analysis
- `earnings_window`: earnings or guidance update in last 30 days → spawn earnings call / guidance driver analysis
- `conflicting_evidence`: bull vs bear claims conflict materially → spawn debate/adjudication task
- `insufficient_evidence`: evidence count too low or missing key categories → spawn additional research

---

## R5. Parallelization Policy

- Data collection and summarization tasks **should** run in parallel when safe.
- Synthesis and verdict generation **must** run after all required evidence is collected.
- All parallel tasks must return structured outputs in the same schema to enable deterministic merging.

---

## R6. Quality Gates (Before Final Verdict)

The orchestrator must validate:

- Evidence count: `>= MIN_EVIDENCE_COUNT` (configurable; default 8)
- Coverage: at least 2 of 3 categories covered: `price`, `news`, `fundamental`
- Counter-argument exists: `bear_case` must not be empty; otherwise spawn a Bear task.
- Confidence sanity: if mean confidence < threshold → spawn additional research or downgrade verdict confidence.

---

## R7. Reproducibility and Run Artifacts

- Each run writes to `/runs/<timestamp>_<ticker>/`
- Store:
  - inputs
  - research plan
  - all evidence JSON
  - trigger log
  - final JSON + Markdown report
- Prefer low-temperature models for stability; keep planning templates consistent.

---

## R8. Observability (Structured Events)

The orchestrator emits JSONL event logs:

- `PLAN_CREATED`
- `TASK_SPAWNED`
- `TASK_FINISHED`
- `TRIGGER_FIRED`
- `VERDICT_COMPUTED`
- `RUN_SAVED`
  Each event must include `run_id`, `ticker`, timestamps, and relevant ids.

---

## R9. Safety / Compliance

- Always include a disclaimer: “Not financial advice.”
- Avoid language implying guarantees or certainty.
- Cite data sources whenever possible.
- Minimize personally identifying data; do not store sensitive user information.

---

## R10. Naming and Organization Conventions

- `schemas/` contains Pydantic models only.
- `orchestrator/` contains Flow + trigger engine + synthesis logic only.
- `crews/` contains Crew definitions and agent/task configs only.
- `tools/` contains external integrations, fetchers, caches.
- Keep all configs in `configs/` and load them centrally.

---

## R11. Default Output Style (Report)

- Start with a brief executive summary.
- Include:
  - Bull case vs Bear case
  - Key triggers and what would change the verdict
  - Risks and unknowns
  - Next actions checklist (what to monitor)

---

## R12. Future Extensions (Non-Blocking)

- Multi-ticker portfolio mode
- Backtesting hooks
- Risk scenario simulation
- Plug-in tool interface (MCP) for data providers
