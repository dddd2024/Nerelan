```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260611_affine_rank1_static_triage_status_overlay_v1",
  "round_id": "round_20260611_affine_rank1_static_triage_status_overlay_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

推进本地逆向训练集的下一小步：对 evaluation queue rank 1 的 `affine_8cfebe03` 做有界静态 triage，并让 triage 结果能被 training status overlay 消费。

本轮只允许完成三件事：

1. 修正或补齐 `local_reverse_single_sample_static_triage` 与 `local_reverse_training_status` 之间的 artifact/schema 对接，使 static-only triage artifact 可以稳定影响 `training_status` / `evaluation_queue`。
2. 在本地样本可解析时，对 `affine_8cfebe03` 运行一次静态 triage，生成 `project_state/local_reverse_affine_8cfebe03_static_triage.json` 并登记到 `artifact_index.json`。
3. 重建 `project_state/local_reverse_training_status.json`、`project_state/local_reverse_evaluation_queue.json` 和 GitHub-safe `training_materials/local_reverse/status_overlay.json`，确认 `affine_8cfebe03` 不再停留在未解释的 `inventory_only` 状态。

## 2. Current Evidence

- 上一轮 command-output / artifact-summary completeness 已 ACCEPTED；当前可以进入训练集推进，不再继续修补报告格式。
- `project_state/local_reverse_training_status.json` 显示本地训练集共有 50 个样本，其中 1 个 solved、2 个 blocked、47 个 inventory_only。
- `project_state/local_reverse_evaluation_queue.json` 的 rank 1 是 `affine_8cfebe03`，只允许 `static_triage`，明确禁止 `runtime_probe`、`bruteforce`、`upload_binary`。
- `project_state/local_reverse_affine_tool_capability_audit.json` 已确认应复用现有 `static_feature_extractor`、`tool_runners`、`local_reverse_ida_summary`、`local_reverse_single_sample_static_triage` 等能力，不得新建重复 affine 专用 runner。
- `reverse_agent/local_reverse_single_sample_static_triage.py` 已是 static-only adapter，声明不执行目标二进制、不生成 candidate。
- `reverse_agent/local_reverse_training_status.py` 已有 static handoff overlay 入口，但需要核对它是否能消费 `single_sample_static_triage` 产物，特别是 success/blocked schema、`status`、`tool_status`、`static_only`、`executed_sample`、`runtime_validated`、`candidate` 等字段。
- `artifact_index.json` 仍主要是历史 sample artifacts；本轮只允许为当前静态 triage artifact 做有界登记，不得把 stale artifact 当 current evidence。

## 3. Do Not Do

- 不运行样本二进制。
- 不运行 solver、candidate search、bruteforce、runtime probe、debugger、hook、emulator、sidecar。
- 不上传或提交任何本地样本二进制。
- 不读取完整 `solve_reports/`。
- 不创建 affine 专用重复模块，例如 `local_reverse_affine_extractor.py`、`local_reverse_affine_ida.py`。
- 不绕过现有 `static_feature_extractor`、`tool_runners`、`local_reverse_single_sample_static_triage`、`local_reverse_training_status`。
- 不把 `BINARY_NOT_FOUND`、`LOCAL_REVERSE_ROOT missing`、`IDA executable missing` 这类环境问题误记为样本本身已 blocked。
- 不生成 candidate、known_candidate 或 solved 状态。
- 不把旧 stale artifact 登记为 current。

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `.codex-skills/registry.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/local_reverse_affine_tool_capability_audit.json`
- `project_state/artifact_index.json`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/static_feature_extractor.py`
- `reverse_agent/tool_runners.py`
- `tests/test_local_reverse_single_sample_static_triage.py`
- `tests/test_local_reverse_training_status.py`
- `tests/test_project_state.py`

Optional, only if directly needed and bounded:

- `reverse_agent/local_reverse_ida_summary.py`
- `reverse_agent/local_reverse_targeted_static_reextract.py`
- `training_materials/local_reverse/README.md`

## 5. Required Audit

Codex must:

1. Confirm repository root is `F:\reverse-agent`.
2. Confirm this decision is active and `status` is `APPROVED`.
3. Confirm skill profiles are active in `.codex-skills/registry.json`.
4. Confirm `affine_8cfebe03` is still queue rank 1 and that allowed actions are only static triage.
5. Inspect existing static triage and training status overlay code before modifying anything.
6. Add or update tests proving:
   - static triage artifacts always keep `executed_sample: false`, `runtime_validated: false`, `candidate: null`, `known_candidate: ""`;
   - successful static triage artifacts can be consumed by training status as `needs_triage` or an equivalent non-solved/non-runtime static state;
   - blocked static triage artifacts caused by real static analysis blockers can be consumed as blocked;
   - environment blockers such as missing local binary/root/tool do not falsely mark the sample as solved and do not create candidate evidence.
7. If schema changes are needed, make them in the existing modules only. Prefer explicit fields such as `status`, `training_status_hint`, `tool_status`, and `blocked_reason` over implicit inference.
8. Run bounded static triage for `affine_8cfebe03` only if the local sample resolves. If the local root or sample is missing, stop with `BLOCKED` and record the environment blocker; do not fabricate artifact success.
9. If static triage succeeds, add the resulting artifact to `artifact_index.json` under `latest_artifacts_v2` with `freshness: current`, `kind: local_reverse_static_triage`, `sample_id: affine_8cfebe03`, and the artifact path.
10. Rebuild training status and queue after the artifact_index update.
11. Verify that `affine_8cfebe03` is no longer an unexplained `inventory_only` entry if static triage succeeded. If it remains `inventory_only`, report `FAILED` or `BLOCKED` with the exact reason.
12. Write a complete `codex_execution_report.md` and `pytest_result.txt`, archive the round, and run post-archive lint/status/doctor checks.

## 6. Implementation Scope

Allowed source/test changes:

- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/local_reverse_training_status.py`
- `tests/test_local_reverse_single_sample_static_triage.py`
- `tests/test_local_reverse_training_status.py`

Allowed generated or updated project_state / metadata files:

- `project_state/local_reverse_affine_8cfebe03_static_triage.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `training_materials/local_reverse/status_overlay.json`
- `project_state/artifact_index.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260611_affine_rank1_static_triage_status_overlay_v1/*`

Allowed only if tests show they must be touched:

- `tests/test_project_state.py`

Disallowed:

- `.codex-skills/`
- local sample binaries under `E:\reverse` or any other sample root
- `solve_reports/` bulk reads or commits
- solver/runtime/debugger/IDA/Ghidra runner rewrites
- new affine-specific runner modules
- candidate generation or validation code

## 7. Tests

Run and record exact outputs:

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m pytest tests/test_local_reverse_single_sample_static_triage.py tests/test_local_reverse_training_status.py -q
python -m pytest tests/test_local_reverse_inventory.py tests/test_local_reverse_single_sample_static_triage.py tests/test_local_reverse_training_status.py tests/test_project_state.py -q
python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id affine_8cfebe03 --queue project_state/local_reverse_evaluation_queue.json --inventory project_state/local_reverse_inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_affine_8cfebe03_static_triage.json
python -m reverse_agent.local_reverse_training_status --inventory project_state/local_reverse_inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_training_status.json --queue-out project_state/local_reverse_evaluation_queue.json --github-status-out training_materials/local_reverse/status_overlay.json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_affine_rank1_static_triage_status_overlay_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

If the static triage command exits non-zero because local sample root or binary is unavailable, Codex must stop and write `codex_execution_report.md` with `status: BLOCKED`, preserving all tests and diagnostics run before the blocker.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- The active decision does not match this packet.
- Skill profiles are missing or inactive.
- `affine_8cfebe03` is no longer queue rank 1 and no replacement rationale is written.
- Local sample root or `affine.exe` cannot be resolved.
- Static triage requires executing the sample.
- IDA/Ghidra/debugger/runtime execution becomes necessary.
- A candidate, known_candidate, solved status, or runtime validation would be required to proceed.
- Artifact registration would require treating stale artifacts as current.
- Training status remains unchanged after a successful static triage artifact.
- Any required pytest/lint/status/doctor command fails.
- Final git status has unexplained files.
