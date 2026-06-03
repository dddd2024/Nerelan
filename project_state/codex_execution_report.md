```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_compare_site_extraction_doc_cleanup",
  "round_id": "round_20260603_local_reverse_compare_site_extraction_doc_cleanup",
  "based_on_decision_id": "decision_20260603_local_reverse_compare_site_extraction_doc_cleanup",
  "status": "PARTIAL",
  "acceptance_recommendation": "NEEDS_REVIEW",
  "files_changed": [
    "README.txt",
    "reverse_agent/local_reverse_compare_site.py",
    "tests/test_local_reverse_compare_site.py",
    "project_state/local_reverse_compare_site_result.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent\\local_reverse_runtime.py reverse_agent\\local_reverse_string_solver.py reverse_agent\\local_reverse_compare_site.py",
    "python -m pytest -q tests\\test_local_reverse_runtime.py tests\\test_local_reverse_string_solver.py tests\\test_local_reverse_compare_site.py",
    "python -m reverse_agent.local_reverse_compare_site --corpus-index project_state\\local_reverse_corpus_index.json --benchmark project_state\\local_reverse_solve_benchmark.json --string-result project_state\\local_reverse_string_solver_result.json --policy project_state\\local_reverse_runtime_policy.json --out project_state\\local_reverse_compare_site_result.json",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_compare_site_result.json"
  ],
  "next_suggested_task": "Add bounded xref/disassembly extraction around compare keyword strings before generating more candidates"
}
```

# Codex Execution Report

## Decision Alignment

This execution follows `project_state/decision_packet.md` for `decision_20260603_local_reverse_compare_site_extraction_doc_cleanup`.

The stale `samplereverse` fields in `project_state/task_packet.json` and `project_state/current_state.json` were treated as background only. The active mainline is `reverse_solving`, and this round's concrete direction is `local_reverse_compare_site_extraction_doc_cleanup`.

## Scope

This round only processed the three unsolved `ready_static_string_compare` targets from `project_state/local_reverse_string_solver_result.json`:

```text
4c69f173f2bd0211 -> 逆向课程2022春02/CPP2.exe
bcbd9979db015bfd -> 逆向课程2022春补考01/Cpp1.exe
18019fca52b389fe -> 逆向课程2024春01/sha_256.exe
```

No other challenge binary entered compare-site extraction. No `samplereverse` window discovery, compare handoff, Base64/RC4 breakpoint probe, material capture, crypto hook, candidate expansion, old `sample_solver`, GUI automation, full `solve_reports/` traversal, or full `PROJECT_PROGRESS_LOG.txt` read was performed.

No binary sample was copied into the repository, uploaded, committed, relocated, or encoded as hex/base64. `.codex-skills/` was not modified.

## Implementation

Added `reverse_agent/local_reverse_compare_site.py`, a bounded CLI and library module:

```text
python -m reverse_agent.local_reverse_compare_site --corpus-index project_state\local_reverse_corpus_index.json --benchmark project_state\local_reverse_solve_benchmark.json --string-result project_state\local_reverse_string_solver_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_compare_site_result.json
```

The module selects only prior string-solver targets with:

```text
solved=false
negative_result=NO_CANDIDATE_VALIDATED
missing_evidence=needs_compare_constant_or_disassembly
sample_id in {4c69f173f2bd0211, bcbd9979db015bfd, 18019fca52b389fe}
```

It reuses the existing indexed-path, sha256, runtime-policy timeout, and conservative runtime success semantics. Static extraction is bounded to ASCII / UTF-16LE strings, prompt/failure/success/candidate-string classification, PE compare import hints when available, and compare keyword strings. `capstone` availability is reported but not used for unbounded disassembly in this round.

README cleanup was limited to removing or rewriting the obsolete current-flow references to local sample add/solve commands and per-case solver scripts. The current README now points local training at `project_state/local_reverse_*.json` and the corpus/runtime/string-solver/compare-site modules.

## Result

Generated:

```text
project_state/local_reverse_compare_site_result.json
```

Summary:

```text
status=PARTIAL
target_count=3
solved_count=0
max_new_candidates_per_sample=30
max_runtime_validations_per_sample=30
blocked_reasons=[]
```

Per-target result:

```text
18019fca52b389fe -> compare_site_status=found, new_candidate_count=30, validated_candidate_count=30, solved=false, missing_evidence=new_candidates_failed_runtime_validation
4c69f173f2bd0211 -> compare_site_status=found, new_candidate_count=30, validated_candidate_count=30, solved=false, missing_evidence=new_candidates_failed_runtime_validation
bcbd9979db015bfd -> compare_site_status=found, new_candidate_count=30, validated_candidate_count=30, solved=false, missing_evidence=new_candidates_failed_runtime_validation
```

No `solved=true` result was emitted because none of the new bounded compare-site candidates produced runtime success output without failure semantics.

## Required Audit

- Current `decision_packet.md` was the execution authority.
- Previous string solver output was used as input; the string solver was not reimplemented.
- Mainline is `reverse_solving`; concrete direction is `local_reverse_compare_site_extraction_doc_cleanup`.
- Only the three specified unsolved `ready_static_string_compare` challenge binaries were processed.
- No challenge binary outside the specified three entered compare-site extraction.
- No executable outside indexed `E:\reverse` paths was run.
- No binary sample was copied, committed, uploaded, relocated, or encoded.
- `.codex-skills/` was not modified.
- Full `solve_reports/` and full `PROJECT_PROGRESS_LOG.txt` were not read.
- Compare-site extraction used bounded string/import/keyword evidence and capped new candidates and validations at 30 per sample.
- Runtime evidence was recorded for validated candidates, but no candidate satisfied the conservative success rule.
- All unsolved targets now have the sharper missing evidence `new_candidates_failed_runtime_validation`.
- README obsolete local sample add/solve and per-case solver flow references were cleaned from the current recommended workflow.
- Tests were run for this decision and recorded in `project_state/pytest_result.txt`.

## Validation

- `python -m py_compile reverse_agent\local_reverse_runtime.py reverse_agent\local_reverse_string_solver.py reverse_agent\local_reverse_compare_site.py` -> passed
- `python -m pytest -q tests\test_local_reverse_runtime.py tests\test_local_reverse_string_solver.py tests\test_local_reverse_compare_site.py` -> `21 passed`
- `python -m reverse_agent.local_reverse_compare_site --corpus-index project_state\local_reverse_corpus_index.json --benchmark project_state\local_reverse_solve_benchmark.json --string-result project_state\local_reverse_string_solver_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_compare_site_result.json` -> `local reverse compare-site extraction: status=PARTIAL targets=3 solved=0`
- `python -m reverse_agent.project_state lint-decision --state-dir project_state` -> OK
- `python -m reverse_agent.project_state lint-report --state-dir project_state` -> OK with expected `PARTIAL` and not-archived warnings
- `git diff --check` -> passed
