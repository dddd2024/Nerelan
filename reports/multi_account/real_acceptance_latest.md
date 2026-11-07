# 真实账户验收报告

生成时间：2026-11-07T05:23:19.586501+00:00　真实调用：是　Magpie 0.1.3186

真实账户：**11 个 / 11 个 provider**（claude, codex, copilot, minimax-code, opencode-zen-free, openrouter, raccoon, trae-cn, workbuddy, workbuddy-ai, zcode）

## 结论：**11/11 通过**

| 验收项 | 结果 | 证据 |
|---|---|---|
| 多账户整合（真实） | PASS | `{"accounts": 11, "providers": ["claude", "codex", "copilot", "minimax-code", "opencode-zen-free", "openrouter", "raccoon", "trae-cn", "workbuddy", "workbuddy-ai", "zcode"], "provider_list": "claude,codex,copilot,minimax-code,opencode-zen-fr` |
| 状态感知（真实落库后读回） | PASS | `{"written": 11, "visible": 11, "perceived": 11, "states": {"FRESH": 6, "STALE": 3, "UNKNOWN": 2}, "health": {"HEALTHY": 6, "STALE": 3, "UNKNOWN": 2}}` |
| 调度选中真实可用账户 | PASS | `{"decision": "use", "account": "2826269bbabf", "provider": "minimax-code", "health": "HEALTHY", "headroom": 100.0, "reason": "best_headroom"}` |
| 异常容错（真实池 + 注入故障） | PASS | `{"failed_account": "7605419d1a61", "failed_provider": "copilot", "real_error_rate": 0.8571, "decision": "reroute", "next_account": "2826269bbabf", "next_provider": "minimax-code"}` |
| 真实账户调用（延迟/成本/失败分类） | PASS | `{"calls": [{"account": "claude-code", "ok": true, "seconds": 8.33, "cost_usd": 0.00197374, "priced": true, "attempts": 1, "error": null, "kind": null, "diagnostic": ""}, {"account": "codex", "ok": true, "seconds": 18.67, "cost_usd": null, "` |
| 未知成本不被当成免费 | PASS | `{"priced_calls": 1, "unpriced_calls": 1, "spent_units": 0.001974, "note": "an unpriced attempt is recorded and flagged, not dropped"}` |
| 成本上限（真实 30 天花费） | PASS | `{"real_30d_cost_usd": 58.6993, "cap_usd": 59.6993, "deny_reason": "cost_budget_exhausted", "allow_decision": "degrade", "unpriced_calls_30d": 2338}` |
| 告警与真实池状态一致（不误报 / 不静默） | PASS | `{"observed": {"HEALTHY": 6, "DEGRADED": 0, "EXHAUSTED": 0, "ABNORMAL": 0, "STALE": 3, "UNKNOWN": 2}, "actual": ["perception_partial"], "expected": ["perception_partial"], "budget_alerts": [], "perception_error": null}` |
| 健康真实池不被误调（自进化下限） | PASS | `{"real_pool_success_rate": 0.9647, "target": 0.85, "policy_version": 0, "audit_entries": 0}` |
| 自进化（真实错误率驱动 + 可审计可回滚） | PASS | `{"samples_resampled_from": "7605419d1a61", "measured_error_rate": 0.8571, "policy_version": 2, "audit_entries": 2, "reasons": ["unstable_revert", "unstable_revert"], "rollback_changed": true, "version_after_rollback": 3, "effective_back_to_` |
| 运行时长（真实时钟） | PASS | `{"at_start": "continue", "after_1.05s": "conclude", "reason": "run_deadline_reached", "elapsed_seconds": 1.051}` |

## 真实 30 天经济性（Magpie 观测）

| 指标 | 数值 |
|---|---|
| 调用 / 错误 / 重试 | 5502 / 194 / 43 |
| 成本（列表价） | $58.699296910959994 |
| 未计价调用 | 2338 |
| 输出 token / 计时样本 | 2171511 / 3071 |

## 真实调用

| 账户 | 成功 | 秒 | 成本(USD) | 已计价 | 尝试 | 失败类型 | 诊断 |
|---|---|---|---|---|---|---|---|
| claude-code | True | 8.33 | 0.00197374 | True | 1 | - | - |
| codex | True | 18.67 | None | False | 1 | - | - |

本次调用总花费：**$0.001974**

## 复现

```bash
python scripts/multi_account_real_acceptance.py --live
```

## 说明

- 账户身份只使用 Magpie 已截断的 sha256；不读取、不打印任何凭据。
- 故障注入作用于真实池中的真实账户（选真实 30 天错误率最高者），不是伪造账户。
- 未计价调用（codex CLI 不上报成本）会入账并标记 `priced=false`，而不是当作免费。
- 真实失败不会被吞掉：CLI 的 stderr/stdout 尾部经脱敏后按生产同一套词表分类（`account_abnormal` / `quota_exhausted` / `transient` / `task_failed`），只有传输类失败允许再打一次，账户级失败直接交给切换。
