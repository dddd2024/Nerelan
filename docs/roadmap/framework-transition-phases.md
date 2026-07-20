# Framework transition phases

Roadmap entries order work; only `project_state/decision_packet.md` authorizes execution.

1. `legacy-control-plane-disposition` — inventory PR #5, choose owners and baseline, and close locally.
2. `selective-capability-integration` — transplant minimal packaging and the two reviewed workflow compatibility hunks.
3. `trust-layer-schema-foundation` — define EvidenceUnit, Claim, Counterevidence, ToolAction, validation, and R2/R3 authorization contracts without runtime dispatch.
4. `github-truth-adapter` — consume immutable branch/PR/check/release facts from GitHub with provenance.
5. `bmad-planning-adapter` — map discovery, PRD, architecture, and stories to structured planning inputs; never authorize commands.
6. `langgraph-shadow-runtime` — run one non-dispatching shadow graph against fixtures and compare state transitions with the compatibility path.
7. `web-workbench-transition` — route User Solve through accepted adapters while preserving manual mode until parity is proven.

The first follow-on Decision is `decision_20260720_selective_capability_integration_v1`. Its scope is limited to `.gitignore`, `pyproject.toml`, `tests/test_packaging_metadata.py`, and the `fetch-depth: 0` plus `--allow-consumed` hunks in State Gate and Decision Preflight. It explicitly excludes framework installation, PR #5 round archives, wholesale `project_gate.py` transplantation, runtime dispatch, and User Solve changes.
