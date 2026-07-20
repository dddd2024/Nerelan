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

This commit should not exist. Restore the full v10 packet from parent commit `a991dc44dabab83241973ae1f4100ff06a3dffb9`.

## 2. Current Evidence

The parent contains the full packet.

## 3. Do Not Do

Do not execute this truncated file.

## 4. Files To Inspect

Parent commit only.

## 5. Required Audit

Stop.

## 6. Implementation Scope

None.

## 7. Tests

None.

## 8. Stop Conditions

Always.
