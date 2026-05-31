```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260531_local_reverse_samples_ignore",
  "round_id": "round_20260531_local_reverse_samples_ignore",
  "based_on_decision_id": "decision_20260531_local_reverse_samples_ignore",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    ".gitignore",
    "README.txt",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "git diff --check",
    "git status --short",
    "git check-ignore -v local_reverse_samples/",
    "python -m py_compile reverse_agent/harness.py",
    "python -m pytest -q tests/test_harness.py",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ]
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-31 Local Reverse Samples Ignore Convention

Result: `SUCCESS` / `ACCEPTED`.

This round executed `decision_20260531_local_reverse_samples_ignore`. It was an
engineering-branch documentation and Git hygiene change only: no samplereverse
runtime probe, no Base64/RC4 breakpoint probe, no IDA/Olly/Frida automation, no
candidate/frontier/budget change, and no full `solve_reports/` read.

## Audit Answers

1. `.gitignore` now ignores `local_reverse_samples/`.
2. `README.txt` now explains that `local_reverse_samples\` is for local reverse
   training samples, notes, attachments, and harness `case.json` files.
3. `README.txt` explicitly says the directory is ignored by Git and not uploaded
   to GitHub.
4. `README.txt` includes a harness `case.json` example using
   `local_reverse_samples/crackme_sha256_001/sample.exe`.
5. `README.txt` includes the matching `python -m reverse_agent.harness
   --dataset .\local_reverse_samples\crackme_sha256_001\case.json --run-name
   crackme_sha256_001` command.
6. No real `.exe`, `.dll`, `.bin`, `.zip`, `.7z`, or `.rar` sample file was
   added.
7. `.codex-skills/` was not modified.
8. No reverse runtime probe was run.
9. The samplereverse solving mainline was not changed.
10. `local_reverse_samples/` was created only as a local ignored directory for
    `git check-ignore` verification and does not appear in Git diff.

## Code Changes

- Added `local_reverse_samples/` to `.gitignore`.
- Documented the local sample directory convention in `README.txt`.
- Updated this report and `project_state/pytest_result.txt` so the active
  decision is consumed by the closeout artifacts.

## Verification

```text
git diff --check
passed

git status --short
passed; changed files are limited to .gitignore, README.txt, and project_state closeout files

git check-ignore -v local_reverse_samples/
passed; .gitignore:8:local_reverse_samples/

python -m py_compile reverse_agent/harness.py
passed

python -m pytest -q tests/test_harness.py
passed: 5 passed

python -m reverse_agent.project_state lint-decision --state-dir project_state
passed

python -m reverse_agent.project_state lint-report --state-dir project_state
passed

python -m reverse_agent.project_state status --state-dir project_state
passed; decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
```

## Next Bottleneck

This engineering branch is complete. The next reverse-solving decision can
return to the existing sample-state blocker only after this local sample
directory convention is accepted.
