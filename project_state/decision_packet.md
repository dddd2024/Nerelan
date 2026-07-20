```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260720_ci_preflight_bootstrap_order_rework_v10",
  "round_id": "round_20260720_ci_preflight_bootstrap_order_rework_v10",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Use the immediately preceding committed v10 Decision content in Git history as the sole full task authority for `decision_20260720_ci_preflight_bootstrap_order_rework_v10`. This file update is invalid and must not be used.

## 2. Current Evidence

This placeholder must never become current authority.

## 3. Do Not Do

Do not execute this placeholder.

## 4. Files To Inspect

Inspect Git history and restore the full v10 Decision from commit `3f0b8e6cc870f1be0899d06a7af2421f84307e1d`.

## 5. Required Audit

Stop.

## 6. Implementation Scope

None.

## 7. Tests

None.

## 8. Stop Conditions

Always stop.
