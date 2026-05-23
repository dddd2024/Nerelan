```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260523_engineering_pytest_result_provenance",
  "round_id": "round_20260523_engineering_pytest_result_provenance",
  "based_on_decision_id": "decision_20260523_engineering_pytest_result_provenance",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/project_state.py",
    "tests/test_project_state.py",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent\\project_state.py",
    "python -m pytest -q tests\\test_project_state.py",
    "python -m pytest -q tests\\test_project_state.py -k \"archive or pytest_result or report\"",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state"
  ],
  "generated_artifacts": [
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md"
  ],
  "next_suggested_task": []
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-23 Pytest result provenance hygiene

Result: `SUCCESS` / `ACCEPTED`. pytest_result.txt now carries a machine-readable pytest_result_summary header, new parsing/validation helpers gate report consistency, and status/lint-report expose mismatch signals. The active pytest_result.txt was overwritten to only reference this decision.

## Required Audit

| check | result |
|---|---|
| 当前 pytest_result.txt 是否包含多个 decision | 是，原文件混入 decision_20260523_samplereverse_sidecar_hooks_installed_observation_blocker 与 decision_20260523_engineering_artifact_hygiene_sidecar_health_schema 记录。 |
| codex_report_summary 关键字段 | report_id=report_20260523_engineering_artifact_hygiene_sidecar_health_schema，round_id=round_20260523_engineering_artifact_hygiene_sidecar_health_schema，based_on_decision_id=decision_20260523_engineering_artifact_hygiene_sidecar_health_schema，status=SUCCESS。 |
| decision_meta.decision_id | decision_20260523_engineering_pytest_result_provenance。 |
| pytest_result 是否能匹配 report based_on_decision_id | 旧文件无法匹配；现已重写为匹配当前 decision。 |
| project_state.py 中读取路径 | status_summary 与 lint_report 读取 pytest_result.txt 并调用 validate_pytest_result_for_report。 |
| pytest_result 写入语义 | 之前无统一写入函数（手动追加）；新增 write_pytest_result helper 以覆盖写入并写入 header。 |
| solve_reports 是否需要读取 | 不需要；未读取。 |
| runtime probe 是否运行 | 未运行。 |

## Changes

- **pytest_result header**: 新增 pytest_result_summary 解析/校验 helper，兼容 legacy 无 header 文件。
- **覆盖写入 helper**: write_pytest_result 提供覆盖写入语义与 header 格式，避免旧轮记录残留。
- **status/lint-report 接入**: status 输出与 lint-report 增加 pytest_result_status/decision_id/report_id/round_id/matches_report 字段。
- **active pytest_result.txt**: 重写为仅含当前 decision 的测试记录。

## Verification

| command | result |
|---|---|
| `python -m py_compile reverse_agent\project_state.py` | passed |
| `python -m pytest -q tests\test_project_state.py` | `112 passed` |
| `python -m pytest -q tests\test_project_state.py -k "archive or pytest_result or report"` | `46 passed, 66 deselected` |
| `python -m reverse_agent.project_state status --state-dir project_state` | `pytest_result_matches_report: True` |
| `python -m reverse_agent.project_state lint-report --state-dir project_state` | `lint-report: OK` (warnings: round_id mismatch, round_manifest missing) |

## Git Diff --stat

```
project_state/codex_execution_report.md | 100 +++++++---------
project_state/pytest_result.txt         |  98 ++++------------
reverse_agent/project_state.py          | 166 ++++++++++++++++++++++++++-
tests/test_project_state.py             | 196 +++++++++++++++++++++++++++-----
4 files changed, 394 insertions(+), 166 deletions(-)
```

No samplereverse runtime probes were executed.
