```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_generic_static_evidence_bridge_v1",
  "round_id": "round_20260619_generic_static_evidence_bridge_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

建立一个通用的 static evidence bridge：把 IDA/Ghidra/strings/objdump/static triage 等工具产物转换为项目现有的 `StructuredEvidence` 和 solver dispatch plan。

本轮主线是 `tool_integration`。目标不是专门求解 `affine_8cfebe03`，而是建设可复用的工具产物桥接层。`affine_8cfebe03` 只能作为 fixture / acceptance case，用来验证桥接层能处理 input string + compare context + candidate transform function 这一类证据组合；不得把 sample_id、函数名、字符串、candidate 或 flag 写死进模块逻辑。

本轮完成后，后续每类题目都应能复用同一条链路：

```text
Tool Artifact -> StructuredEvidence -> solver profile hints -> solver dispatch plan
```

本轮不生成 candidate，不生成 flag，不运行样本，不运行 solver，不运行 runtime validation。若桥接层输出 solve-ready plan，也只能作为下一轮 `reverse_solving` 的输入。

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 `samplereverse` / `collect_missing_evidence` 建议，且 `execution_scope=decision_packet_controls_current_round`。它不是本轮执行权威，本轮执行以本 `project_state/decision_packet.md` 为准。

当前 `current_state.json` 仍是 `samplereverse` 的 sample-state，`artifact_refs={}`，best candidates 为空，多个 runtime/static artifact 字段为空。它不能作为本轮 tool integration 的 current sample evidence。

当前 `artifact_index.json` 对 `samplereverse` 记录大量 `freshness=missing` artifact。这些是历史/backlog 状态。上一轮 claim-aware gate policy 已经确认：非样本主线不能被 unclaimed historical/backlog sample artifacts 错误阻塞，但 reverse_solving 或 claimed evidence 仍必须保持 strict freshness。

`negative_results.json` 继续有效：不要回到旧 `sample_solver` blind search，不要只扩 beam/budget/topN，不要把 `compare_semantics_agree=false` candidates 当 primary frontier，不要提交完整 `solve_reports/`，不要重复 `samplereverse` 已失败的 exact2/H1-H3/transform-trace 方向。

已有相关能力必须复用：

- `reverse_agent/evidence.py` 已有 `StructuredEvidence` dataclass 以及 material evidence helpers；不得新建不兼容的第二套 evidence model。
- `reverse_agent/tool_runners.py`、`reverse_agent/tool_capability_inventory.py`、`reverse_agent/local_reverse_single_sample_static_triage.py`、`reverse_agent/local_reverse_targeted_static_reextract.py` 等工具接口已存在；先检查再复用，不重复实现 IDA/Ghidra/debugger runner。
- `project_state/local_reverse_solver_tool_capability_map.json`、`project_state/structured_evidence_gap_report.json`、`project_state/local_reverse_cipher_static_evidence_profile.json` 等历史产物可作线索，但不能无 provenance 地当 current evidence。
- `project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json` 记录历史上 `affine_8cfebe03` 的 IDA output blocker 已修复；它只说明此样本适合作为 acceptance fixture，不授权本轮直接求解。
- `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json` 记录历史 IDA static evidence：有 `_strncmp` compare context、input-oriented strings、candidate function hints 和 next action。它可以作为 fixture 输入/格式线索，但不能被标记为 current reverse-solving evidence，除非本轮有界重建并登记 provenance；本轮默认不运行 IDA/Ghidra。

本轮核心判断：现在真正缺的不是训练队列刷新，而是通用 bridge，让成熟工具输出可以稳定进入 solver dispatcher。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行任何本地样本可执行文件。

不要生成 candidate、flag、密码、key 或最终答案。

不要运行 solver、harness、runtime probe、sidecar、emulator、debugger hook、GUI workflow 或 frontend workflow。

不要运行 IDA/Ghidra/OllyDbg/x64dbg。如果发现需要当前 IDA/Ghidra 输出才能完成，本轮停止并报告下一轮 bounded static extraction 需求。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要上传、复制或提交本地样本二进制。

不要修改 `.codex-skills/`。

不要新建重复的 IDA/Ghidra/debugger runner、corpus scanner、solver 或 harness。

不要把 `affine_8cfebe03` 写成专用逻辑。禁止出现 `if sample_id == "affine_8cfebe03"` 这类分支，除非只在测试 fixture 名称、artifact 产物说明或 acceptance report 中出现。

不要把历史 `affine_8cfebe03` static artifact 标记为 current solving evidence。

不要把本轮扩展成批量训练集刷新或单样本求解。

## 4. Files To Inspect

默认先读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

现有证据/工具/调度能力：

1. `reverse_agent/evidence.py`
2. `reverse_agent/pipeline.py`
3. `reverse_agent/tool_runners.py`
4. `reverse_agent/tool_capability_inventory.py`
5. `reverse_agent/local_reverse_single_sample_static_triage.py`
6. `reverse_agent/local_reverse_targeted_static_reextract.py`
7. `reverse_agent/local_reverse_training_status.py`
8. `reverse_agent/local_reverse_training_review.py`
9. `reverse_agent/local_reverse_corpus.py`
10. `reverse_agent/probes/gui.py`
11. `reverse_agent/profiles/samplereverse.py`
12. existing solver/dispatcher modules discovered by search; inspect before modifying

Fixture / acceptance inputs, read boundedly only:

1. `project_state/local_reverse_affine_8cfebe03_static_triage.json`
2. `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json`
3. `project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json`
4. `project_state/local_reverse_cipher_static_evidence_profile.json`
5. `project_state/local_reverse_solver_tool_capability_map.json`
6. `project_state/structured_evidence_gap_report.json`

Do not read complete heavy-history directories.

## 5. Required Audit

Before implementation, audit and record:

1. Worktree is `F:\reverse-agent` and repository root is correct.
2. Startup `git status --short` is recorded. If dirty files exist, record baseline and do not overwrite unrelated work.
3. `decision_meta.status=APPROVED`.
4. `mainline=tool_integration`.
5. `reverse-agent-iteration@v2` is active in `.codex-skills/registry.json`.
6. `task_packet.json` is advisory, not execution authority.
7. Existing tool interfaces for IDA/Ghidra/debugger/static triage are checked before adding code.
8. Existing `StructuredEvidence` in `reverse_agent/evidence.py` is reused or extended compatibly.
9. No mature tool capability is reimplemented.
10. No solver, runtime validation, sample execution, IDA/Ghidra/debugger run, harness, GUI or frontend workflow is invoked.
11. Historical affine artifacts are classified as fixture/provenance examples, not current solving evidence.
12. Implementation does not hardcode `affine_8cfebe03` outside tests/reports/fixture paths.
13. Any produced solver dispatch plan has explicit readiness state such as `not_solve_ready`, `needs_current_static_provenance`, or `solver_profile_hint_only` unless current evidence was built in this round.

Bridge capability audit must answer:

1. Which tool artifact schemas are currently supported: static triage JSON, static evidence summary JSON, cipher static profile JSON, strings-only artifact, runtime trace artifact, etc.
2. Which evidence families are normalized: input evidence, compare evidence, constant/array evidence, transform evidence, crypto signature evidence, GUI input evidence, anti-debug evidence.
3. Which solver profile hints can be emitted: string compare, xor, affine/shift, lookup table, RC4, DES/AES, hash/domain, GUI check, anti-debug precondition.
4. Which evidence is insufficient for solving and why.

## 6. Implementation Scope

Preferred implementation is a small generic bridge module plus tests.

Allowed source files:

- `reverse_agent/evidence.py`
- `reverse_agent/static_evidence_bridge.py`
- `reverse_agent/solver_dispatch_plan.py`
- `reverse_agent/tool_capability_inventory.py` only if needed to register bridge capability metadata
- `reverse_agent/pipeline.py` only if needed to expose existing pipeline integration without running tools

Allowed tests:

- `tests/test_static_evidence_bridge.py`
- `tests/test_solver_dispatch_plan.py`
- `tests/test_evidence.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed generated artifacts:

- `project_state/static_evidence_bridge_report.json`
- `project_state/static_evidence_bridge_report.md`
- `project_state/solver_dispatch_plan.json`
- `project_state/static_evidence_bridge_capability_matrix.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260619_generic_static_evidence_bridge_v1/*`

Implementation requirements:

1. Build a generic adapter that accepts dict-like static artifacts and returns `list[StructuredEvidence]` plus a solver dispatch plan.
2. Evidence kinds must be generic, e.g. `StaticInputEvidence`, `StaticCompareEvidence`, `StaticConstantEvidence`, `StaticTransformHintEvidence`, `StaticCryptoSignatureEvidence`, `StaticGuiInputEvidence`, `StaticAntiDebugEvidence`.
3. Compare detection must be rule-based on artifact content, not sample_id: `strcmp`, `strncmp`, `memcmp`, `CompareStringA`, comparison blocks, compare callsites.
4. Input detection must be rule-based on input APIs/strings: `scanf`, `gets`, `fgets`, `ReadFile`, `GetDlgItemTextA/W`, `__input`, prompt-like strings.
5. Transform hints must be conservative: arithmetic/bitwise/loop/table evidence can recommend solver profile but cannot become solve-ready without sufficient constants and provenance.
6. Crypto signatures must be profile hints only unless enough structured material exists: RC4 KSA/PRGA, DES/AES tables, MD5/SHA constants, Base64 table or material evidence.
7. The solver dispatch plan must include `readiness`, `recommended_solver_profiles`, `required_missing_evidence`, `source_artifacts`, and `provenance_notes`.
8. `affine_8cfebe03` may appear only in tests and generated reports as acceptance fixture; production logic must pass the same tests with synthetic generic artifacts.
9. Preserve backward compatibility with existing `StructuredEvidence` fields: `kind`, `source_tool`, `summary`, `payload`, `confidence`, `derived_candidates`.
10. Do not generate candidates or final answers.

Acceptance cases:

1. Synthetic static triage artifact with `__input` + `_strncmp` + compare context returns input and compare evidence and recommends `string_compare` profile.
2. Synthetic artifact with xor/arithmetic loop and constants returns transform hint and recommends `xor` or `affine_shift` profile, but remains not solve-ready if target constants are incomplete.
3. Synthetic RC4-like artifact returns crypto signature evidence and recommends `rc4` profile only as a hint.
4. Historical `affine_8cfebe03` fixture can be parsed into evidence and a dispatch plan, but readiness must be no stronger than `needs_current_static_provenance` unless rebuilt in this round.
5. No test relies on executing a binary or launching IDA/Ghidra/debugger.

## 7. Tests

Must run and write results to `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m pytest tests/test_static_evidence_bridge.py tests/test_solver_dispatch_plan.py tests/test_evidence.py tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If `tests/test_solver_dispatch_plan.py` or `tests/test_evidence.py` do not exist and no matching code is changed, create only the tests that correspond to changed modules and record the reason in the report.

If final-check passes and `gate_profile_plan.closeout_allowed=true`, close the round and rerun final-check:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_generic_static_evidence_bridge_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/codex_execution_report.md` must include a valid `codex_report_summary` with matching `based_on_decision_id`, `round_id`, `files_changed`, `tests_ran`, and `generated_artifacts`.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. Cannot confirm repository root `F:\reverse-agent`.
2. `decision_meta` is missing or not `APPROVED`.
3. `mainline` is not `tool_integration`.
4. `reverse-agent-iteration@v2` is not active.
5. Required implementation needs running IDA/Ghidra/debugger/runtime probe/sample/solver/harness.
6. Existing mature tool interface already provides equivalent bridge behavior and only needs documentation; in that case, do not duplicate it, produce a capability audit instead.
7. Existing evidence model cannot be extended compatibly without a larger schema migration.
8. Bridge implementation would require reading complete `solve_reports/` or complete `PROJECT_PROGRESS_LOG.txt`.
9. Code would hardcode `affine_8cfebe03` behavior in production modules.
10. Tests require executing binaries or launching external reverse tools.
11. `pytest_result.txt` lacks real command output.
12. report/decision/pytest_result IDs mismatch.
13. final-check has any FAIL.
