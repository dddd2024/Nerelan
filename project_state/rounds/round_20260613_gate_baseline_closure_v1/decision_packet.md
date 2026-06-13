```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_gate_baseline_closure_v1",
  "round_id": "round_20260613_gate_baseline_closure_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

关闭上一轮 `COMPLETED_WITH_LIMITATIONS` 中遗留的工程门禁问题。本轮目标是让 preflight、report-summary、final-check、pytest 和 report 状态形成可审计闭环。

## 2. Current Evidence

上一轮核心功能修复已完成，但报告仍列出四类限制：preflight 对只读检查项误判；summary/final 受历史 dirty files 影响；仍有两个既有测试失败；某个上轮已修改文件无法被当前 gate 正确区分为历史改动还是本轮改动。

## 3. Do Not Do

不推进新功能；不处理新样本；不扩大上一轮功能范围；不修改长期 skill；不修改训练材料；不跳过 gate；不降低验收标准。

## 4. Files To Inspect

读取 project_state 默认文件、上一轮报告、pytest 结果、gate 结果、round baseline、artifact index、project gate/state 源码及相关测试。

## 5. Required Audit

确认 decision 权威；确认上一轮功能修复不重复实现；用 round baseline 区分历史改动与本轮改动；定位 preflight 误判原因；定位 final gate 受历史 dirty files 影响的原因；解释并处理两个既有测试失败；报告本轮真实修改文件和历史 dirty files。

## 6. Implementation Scope

允许最小修改 project gate/state 逻辑、对应测试、project_state 报告和 gate 输出。不得修改上一轮功能模块、长期 skill、训练材料或历史产物目录。若必须越界，停止并报告 BLOCKED。

## 7. Tests

必须记录位置确认、git 状态、preflight、command-plan、doctor、pytest 指定集合、lint-report、report-summary、final-check、diff 文件名。验收要求：preflight 不再误判；doctor/lint-report 不再 mismatch；summary/final 真实运行；pytest 无新增失败；report 的 decision_id 和 round_id 匹配本轮。

## 8. Stop Conditions

preflight 仍失败且无法修复时停止。final-check 仍因历史 dirty files 失败且无法归因时停止。出现新增测试失败时停止。需要越过 Implementation Scope 时停止。
