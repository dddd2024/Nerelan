```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260531_local_sample_intake_solve_bootstrap",
  "round_id": "round_20260531_local_sample_intake_solve_bootstrap",
  "based_on_decision_id": "decision_20260531_local_sample_intake_solve_bootstrap",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/local_samples.py",
    "tests/test_local_samples.py",
    "README.txt",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent/local_samples.py",
    "python -m pytest -q tests/test_local_samples.py",
    "python -m pytest -q tests/test_harness.py",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "git diff --check",
    "git status --short",
    "git check-ignore -v local_reverse_samples/"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ]
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-31 Local Sample Intake And Solve Bootstrap

Result: `SUCCESS` / `ACCEPTED`.

This round executed `decision_20260531_local_sample_intake_solve_bootstrap`.
It added a local-only intake and solve-bootstrap CLI. It did not modify
`reverse_agent/harness.py`, `.codex-skills/`, samplereverse profile code, or
CompareAwareSearchStrategy, and it did not run any reverse runtime probe.

## Audit Answers

1. `python -m reverse_agent.local_samples add <file>` creates a case directory
   and generates `case.json` without requiring the user to hand-write it.
2. `add` copies the input file to `<samples_dir>/<case_id>/sample<ext>`.
3. Generated `case.json` uses the existing harness-compatible `{"cases": [...]}`
   format and is covered by `load_harness_cases`.
4. Generated `metadata.json` includes `sha256`, `size_bytes`, `original_path`,
   and `stored_sample_path`.
5. `add` generates a starter `notes.md` template.
6. Without `--case-id`, `add` generates `<sanitized_stem>_<sha256 prefix>`.
7. Existing case ids are not overwritten; the command raises a clear
   `case_id already exists` error.
8. `solve` locates the registered case from `metadata.json` and `case.json`.
9. `solve` generates `codex_task.md` with the expected local `solver.py` path,
   static-analysis checklist, harness command, and local-only constraints.
10. `solve` defaults to task generation only and does not run IDA, OllyDbg,
    Frida, runtime validation, or any runtime probe.
11. The optional `--run-static-harness` path calls the existing harness in
    Static Analysis mode and is covered with a monkeypatched harness entry.
12. No `local_reverse_samples/` contents or binary samples were added to Git.
13. `.codex-skills/` was not modified.
14. The samplereverse solving mainline was not modified.

## Code Changes

- Added `reverse_agent/local_samples.py` with `add` and `solve` subcommands.
- Added focused unit tests in `tests/test_local_samples.py` using only
  `tmp_path` fake samples.
- Updated `README.txt` so the default local workflow is `local_samples add`
  followed by `local_samples solve`; hand-written `case.json` remains documented
  as an advanced path.
- Updated this report and `project_state/pytest_result.txt` for the active
  decision.

## Verification

```text
python -m py_compile reverse_agent/local_samples.py
passed

python -m pytest -q tests/test_local_samples.py
passed: 10 passed

python -m pytest -q tests/test_harness.py
passed: 5 passed

python -m reverse_agent.project_state lint-decision --state-dir project_state
passed

python -m reverse_agent.project_state lint-report --state-dir project_state
passed

git diff --check
passed

git status --short
passed; changed files are reverse_agent/local_samples.py, tests/test_local_samples.py, README.txt, and project_state closeout files

git check-ignore -v local_reverse_samples/
passed; .gitignore:8:local_reverse_samples/
```

## Next Bottleneck

The local sample intake and bootstrap mechanism is ready. A follow-up local
solver round can now choose one ignored sample directory, read its
`codex_task.md`, and write that sample's ignored `solver.py` without changing
the project-wide samplereverse strategy.
