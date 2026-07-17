```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260717_ci_packaging_bootstrap_and_external_attestation_rework_v5",
  "round_id": "round_20260717_ci_packaging_bootstrap_and_external_attestation_rework_v5",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Complete one bounded `project_governance` rework round on Draft PR #5 branch `agent/terminal-status-propagation-seal-restart-rework-v3`.

Repair the editable-install packaging bootstrap that causes CI, State Gate, and Decision Preflight to fail at `Install package`, then use an external, non-self-referential audit of the exact final validation commit. The full approved scope, evidence requirements, tests, and stop conditions are defined by this v5 Decision.

## 2. Current Evidence

- `decision_packet.md` is the task authority; `task_packet.json` is background only.
- v4 remains historical `REWORK_REQUIRED` evidence and must not be edited.
- The three current PR checks fail at `python -m pip install -e .`.
- The workflows use Python 3.13 and the branch has no root `pyproject.toml`, `setup.py`, or `setup.cfg`.
- Existing command-plan, execution-log, report-summary, final-check, closeout, archive, context, state-manifest, and seal mechanisms must be reused.
- Final acceptance requires all three remote checks to pass for one exact final commit, with no later branch mutation.

## 3. Do Not Do

Do not create another branch or PR, merge, rewrite v4 evidence, modify `reverse_agent/*`, expand to another mainline, add speculative dependencies, introduce a heavy packaging framework, use `git add -A`, force-push, rebase, push to `main`, or create a post-check receipt commit that changes the attested HEAD.

## 4. Files To Inspect

Inspect current governance evidence, the v4 archive, `.codex-skills/registry.json`, root packaging files, the three workflow files, workflow job logs, imported modules, branch/PR metadata, and current HEAD. Do not inspect unrelated source trees unless a clean install or focused test identifies a concrete in-scope dependency.

## 5. Required Audit

The final report must separately verify branch/PR identity, Decision ancestry and locks, exact install error, minimal packaging fix, dependency provenance, clean editable installation, import checks, focused tests, changed-file scope, v4 immutability, report/gate/archive/seal consistency, final validation commit identity, absence of later branch commits, and terminal status of CI, State Gate, and Decision Preflight for that exact commit.

## 6. Implementation Scope

1. Lock this Decision and a branch-bound command-plan before substantive work.
2. Capture and classify the exact `Install package` failure.
3. If missing metadata is confirmed, add one minimal standard root `pyproject.toml`; declare only proven dependencies and package discovery for `reverse_agent`.
4. Change the three workflow files only when required by clean-install evidence.
5. Optionally add deterministic `tests/test_packaging_metadata.py`.
6. Validate in a clean temporary virtual environment using editable install, import checks, and the focused workflow test suites.
7. Generate current v5 report, pytest, gate, context, state-manifest, archive, and local seal evidence.
8. Create and push one final validation commit `S` to the existing branch.
9. After pushing `S`, do not mutate the branch. The independent auditor reads GitHub checks for `S` directly.

Allowed implementation paths:

```text
pyproject.toml
.github/workflows/ci.yml
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
tests/test_packaging_metadata.py
selected existing focused tests
current v5 project_state evidence and round archive
```

## 7. Tests

The locked command-plan must include equivalent clean-environment validation:

```text
python -m venv <temporary-path>
<temporary-python> -m pip install --upgrade pip
<temporary-python> -m pip install -e .
<temporary-python> -c "import reverse_agent.project_gate; import reverse_agent.project_state; import reverse_agent.post_final_evidence_sync; import reverse_agent.decision_preflight"
<temporary-python> -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_post_final_evidence_sync.py tests/test_decision_preflight.py tests/test_project_state.py tests/test_packaging_metadata.py -q
```

Then run the selected governance closeout pipeline and push final commit `S`. External acceptance requires `CI`, `State Gate`, and `Decision Preflight` all to be `completed/success` for `S`, with PR head still equal to `S`.

## 8. Stop Conditions

Stop with `BLOCKED` or `REWORK_REQUIRED` if locks fail, the exact install error cannot be obtained, the fix requires another mainline or forbidden path, clean installation or focused tests fail, v4 evidence changes, local evidence disagrees, unrelated changes cannot be excluded, publication requires a prohibited Git operation, any commit is added after final validation commit `S`, or any of the three checks fails or does not reach terminal success for `S`.

Do not expand scope to solve a Stop Condition.
