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

Execute the full v10 bootstrap-order repair Decision contained in parent commit `46f51a311e66d56232547f7d469828f740f4eb8f`.

## 2. Current Evidence

This abbreviated marker must not replace the full parent Decision.

## 3. Do Not Do

Do not execute this marker as a standalone Decision.

## 4. Files To Inspect

Read the parent commit's full `project_state/decision_packet.md`.

## 5. Required Audit

Stop if the full parent Decision is not restored.

## 6. Implementation Scope

None in this marker.

## 7. Tests

None in this marker.

## 8. Stop Conditions

Always stop while this marker is current.
