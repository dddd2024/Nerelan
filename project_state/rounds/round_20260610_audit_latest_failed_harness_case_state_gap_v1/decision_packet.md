```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260610_audit_latest_failed_harness_case_state_gap_v1",
  "round_id": "round_20260610_audit_latest_failed_harness_case_state_gap_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"],
  "registry_active": true,
  "based_on_state_digest": "7ee702d3b2b6e31ff52b17c9d74ecc21ccb6ee0a81c88a8d526458985b4b0153",
  "generated_at": "2026-06-10T11:15:00Z"
}
```

# Decision Packet

## Objective

Audit the state gap behind `latest harness case has errors` / missing `case_results`.

## Implementation Scope

- Bounded metadata inspection of latest harness run
- Determine root cause (real failure vs state-builder diagnostic gap)
- If real failure: record precise report, do not modify source code
- If state-builder bug: implement minimal fix

## Stop Conditions

- If real failed/unusable artifact: do not change source code
- Record precise report explaining next required evidence-producing action
