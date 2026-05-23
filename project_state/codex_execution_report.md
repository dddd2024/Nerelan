```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260523_engineering_artifact_hygiene_sidecar_health_schema",
  "round_id": "round_20260523_engineering_artifact_hygiene_sidecar_health_schema",
  "based_on_decision_id": "decision_20260523_engineering_artifact_hygiene_sidecar_health_schema",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    ".gitignore",
    "reverse_agent/project_state.py",
    "reverse_agent/sidecar_health.py",
    "reverse_agent/strategies/compare_aware_search.py",
    "tests/test_project_state.py",
    "tests/test_compare_aware_search_strategy.py",
    "tests/test_sidecar_health.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent\\project_state.py reverse_agent\\sidecar_health.py reverse_agent\\strategies\\compare_aware_search.py",
    "python -m pytest -q tests\\test_project_state.py",
    "python -m pytest -q tests\\test_compare_aware_search_strategy.py -k \"sidecar_health or compare_lhs_last_writer or archive\"",
    "python -m pytest -q tests\\test_compare_aware_search_strategy.py",
    "python -m pytest -q tests\\test_sidecar_health.py"
  ],
  "generated_artifacts": [],
  "next_suggested_task": [
    "Confirm whether to untrack historical project_state/rounds snapshots using git rm --cached."
  ]
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-23 Engineering artifact hygiene + sidecar health schema

Result: `SUCCESS` / `ACCEPTED`. archive-round now defaults to minimal snapshots with explicit flags for state snapshots and git diff, .gitignore blocks new large round artifacts, and sidecar_health normalization is introduced with compare_lhs_last_writer payloads augmented while preserving legacy flat fields.

## Required Audit

| check | result |
|---|---|
| archive-round 默认归档哪些文件 | 默认仅归档 `decision_packet.md`、`codex_execution_report.md`、`pytest_result.txt` 与 `round_manifest.json`。 |
| git_diff.patch 是否默认生成 | 否，只有 `--include-diff` 才会生成。 |
| rounds 下主要 diff 膨胀来源 | `git_diff.patch`、`current_state.json`、`artifact_index.json` 体积占比最高，其次是 `codex_execution_report.md` / `decision_packet.md`。 |
| 历史大文件是否已被 Git 跟踪 | 是，`project_state/rounds/*/{git_diff.patch,current_state.json,artifact_index.json,negative_results.json,model_gate.json,task_packet.json}` 已被跟踪。建议仅在人工确认后执行 `git rm --cached`。 |
| sidecar 字段重复出现层 | compare_aware_search 的 candidate payload、`_compare_lhs_last_writer_stage_fields` 聚合、final artifact 与 tests fixture 中重复出现 hook/message/subprocess/lifecycle 字段。 |
| compare_aware_search 搬运代码位置 | `_compare_lhs_last_writer_stage_fields` 与 `build_compare_lhs_last_writer_provenance_audit_payload`。 |
| tests fixture 重复校验位置 | `tests/test_compare_aware_search_strategy.py` 中 compare_lhs_last_writer 系列测试。 |
| GPT 审计入口文件保留 | `project_state/*.json` active 文件未删除，decision/report/pytest 入口保持。 |
| runtime probe 执行情况 | 未运行任何 samplereverse runtime probe。 |

## Changes

- **archive-round minimal mode**: 默认仅归档 markdown 报告与 pytest 结果，新增 `--include-state-snapshot` 与 `--include-diff` 显式开关，并在 round_manifest 写入 `archive_mode`、`included_diff`、`included_state_snapshot`、`omitted_files`。
- **.gitignore**: 忽略 round 目录内的 `git_diff.patch` 与完整 state snapshot 文件，阻止新一轮归档污染。
- **sidecar_health**: 新增 `reverse_agent/sidecar_health.py`，提供 normalize/summarize/merge；compare_lhs_last_writer 的 observations 与 final artifact 追加 `sidecar_health` 视图，同时保留旧 flat 字段。
- **tests**: 更新 archive_round 预期与新增 sidecar_health 单测，覆盖 minimal/flags 行为与健康字段归并。

## Compatibility Notes

旧的 flat 字段仍保留在 compare_lhs_last_writer artifact 与 candidate metadata 中；新增 `sidecar_health` 为附加字段，不影响现有消费者。

## Git Tracking Advisory

已检测到历史 round 大文件被 Git 跟踪。如需解除跟踪（不删除本地文件），请人工确认后执行：

```bash
git rm --cached project_state/rounds/*/git_diff.patch
git rm --cached project_state/rounds/*/artifact_index.json
git rm --cached project_state/rounds/*/current_state.json
git rm --cached project_state/rounds/*/negative_results.json
git rm --cached project_state/rounds/*/model_gate.json
git rm --cached project_state/rounds/*/task_packet.json
```

## Verification

| command | result |
|---|---|
| `python -m py_compile reverse_agent\project_state.py reverse_agent\sidecar_health.py reverse_agent\strategies\compare_aware_search.py` | passed |
| `python -m pytest -q tests\test_project_state.py` | `106 passed` |
| `python -m pytest -q tests\test_compare_aware_search_strategy.py -k "sidecar_health or compare_lhs_last_writer or archive"` | `18 passed, 176 deselected` |
| `python -m pytest -q tests\test_compare_aware_search_strategy.py` | `194 passed` |
| `python -m pytest -q tests\test_sidecar_health.py` | `3 passed` |

## Git Diff --stat

```
.gitignore                                       |  7 +++
project_state/pytest_result.txt                  | 27 +++++++++
reverse_agent/project_state.py                   | 77 +++++++++++++++++++++---
reverse_agent/strategies/compare_aware_search.py | 51 +++++++++++-----
tests/test_compare_aware_search_strategy.py      |  3 +
tests/test_project_state.py                      | 76 +++++++++++++++--------
```

新增文件：`reverse_agent/sidecar_health.py`, `tests/test_sidecar_health.py`。
