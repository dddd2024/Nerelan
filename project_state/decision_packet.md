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

Repair the editable-install packaging bootstrap on existing Draft PR #5, then establish an external, non-self-referential remote attestation boundary. Work only on branch `agent/terminal-status-propagation-seal-restart-rework-v3`.

Produce one final validation commit `S`. After `S` is pushed, do not mutate the branch. CI, State Gate, and Decision Preflight must be observed against exactly `S`; the independent auditor returns the verdict without committing a receipt.

## 2. Current Evidence

- `project_state/decision_packet.md` is the sole task authority; `task_packet.json` is background only.
- Current mainline is `project_governance`.
- v4 remains historical `REWORK_REQUIRED` evidence and is read-only.
- PR #5 is open, Draft, unmerged, and targets `main`.
- All three current PR checks fail at `Install package`.
- The workflows use Python 3.13 and `python -m pip install -e .`.
- No root `pyproject.toml`, `setup.py`, or `setup.cfg` was found; missing packaging metadata is the leading hypothesis and must be confirmed from full logs.
- Existing command-plan, execution-log, report-summary, final-check, closeout, archive, context, state-manifest, seal, and CI mechanisms must be reused.
- Current sample-oriented state/artifact files and reverse-solving negative results are read-only and non-blocking.
- Context packet and workstream registry exist; roadmap entries are not execution authority.
- Allowed capabilities are local deterministic Python, clean virtual environments, focused tests, read-only GitHub observation, and controlled push to the existing branch.
- Reverse tools, model APIs, Runner dispatch, Web runtime, databases, cleanup apply, and other mainlines are not allowed.
- Final acceptance requires all three remote checks to pass for exact `S`, with PR head still equal to `S`.

## 3. Do Not Do

Do not create another branch or PR, merge, edit v4 evidence, modify `reverse_agent/*`, expand to another mainline, introduce a heavy packaging framework, add speculative dependencies, use `git add -A`, force-push, rebase, push to `main`, or create any post-check commit that changes the attested HEAD.

Do not modify Skills, frontend, Runner, Job, User Solve, reverse-solving, roadmap, database, cleanup, sample, tool-integration, full `solve_reports`, or `PROJECT_PROGRESS_LOG.txt`.

## 4. Files To Inspect

Inspect current governance evidence, v4 archive, Skill registry, context packet, workstream registry, current state/artifact/negative-result summaries, root packaging inventory, the three workflow files, imported modules, complete workflow job logs, branch/HEAD, and PR metadata.

Do not inspect unrelated source trees unless a clean install or focused test identifies a concrete in-scope dependency.

## 5. Required Audit

The final report must separately verify branch/PR identity; v5 Decision ancestry and locks; exact install error; minimal packaging fix; dependency provenance; Python 3.13 compatibility; clean editable install; workflow import checks; focused tests; changed-file scope; v4 immutability; report/log/context/state/archive/seal consistency; final commit `S`; absence of later branch mutations; terminal CI, State Gate, and Decision Preflight results for exact `S`; prohibited Git operations; and final recommendation consistency.

Each answer must name the artifact or Git observation, field/step, concrete value, status, and item-specific conclusion.

## 6. Implementation Scope

1. Verify branch, PR, and HEAD.
2. Lock this Decision and a branch-bound command-plan before substantive work.
3. Capture and classify the complete `Install package` error.
4. If missing metadata is confirmed, add one minimal standard root `pyproject.toml` with package discovery for `reverse_agent`, Python 3.13-compatible metadata, and only proven dependencies.
5. Change `.github/workflows/ci.yml`, `state-gate.yml`, or `decision-preflight.yml` only if the minimal metadata cannot support their existing install command.
6. Optionally add deterministic `tests/test_packaging_metadata.py`.
7. Validate in an isolated virtual environment using editable install, workflow import checks, and focused pytest suites.
8. Generate v5 report, pytest, current gate artifacts, context, state manifest, archive, and local seal. Local evidence must record remote attestation as pending, not accepted.
9. Create and push one final validation commit `S`.
10. After `S`, do not mutate the branch. External audit reads GitHub checks directly.

Allowed implementation paths:

```text
pyproject.toml
.github/workflows/ci.yml
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
tests/test_packaging_metadata.py
selected existing focused tests
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/gates/*.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260717_ci_packaging_bootstrap_and_external_attestation_rework_v5/*
```

All `reverse_agent/*`, v4 archive/seal files, Skills, frontend, Runner, User Solve, reverse-solving, roadmap, databases, and cleanup paths are forbidden.

## 7. Tests

The locked command-plan must include equivalent clean-environment validation:

```text
python -m venv <temporary-path>
<temporary-python> -m pip install --upgrade pip
<temporary-python> -m pip install -e .
<temporary-python> -c "import reverse_agent.project_gate; import reverse_agent.project_state; import reverse_agent.post_final_evidence_sync; import reverse_agent.decision_preflight"
<temporary-python> -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_post_final_evidence_sync.py tests/test_decision_preflight.py tests/test_project_state.py tests/test_packaging_metadata.py -q
```

If `tests/test_packaging_metadata.py` is not created, command-plan must explicitly omit it with an evidence-backed reason.

Then run the selected governance report, log, final-check, closeout, context/state sync, archive, and local seal pipeline.

External acceptance requires:

```text
CI = completed/success
State Gate = completed/success
Decision Preflight = completed/success
PR head SHA = S
workflow head SHA = S
no later branch commit
```

## 8. Stop Conditions

Stop with `BLOCKED` or `REWORK_REQUIRED` if authority locks fail; the exact install error cannot be obtained; the fix requires another mainline or forbidden path; dependencies cannot be justified; clean installation/import/tests fail; Python 3.13 cannot be retained without broader work; workflow changes exceed the named files; v4 evidence changes; current evidence disagrees; unrelated changes cannot be excluded; publication requires a prohibited Git operation; any commit is added after `S`; PR head changes during attestation; or any remote check fails or remains nonterminal for `S`.

Do not expand scope to solve a Stop Condition.
