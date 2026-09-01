# Issue #492 — R3 v10 local preflight handoff

## Locked authority

- Decision: `decision_20260901_issue492_final_visual_golden_r3_v10`
- Branch: `owner/issue492-final-visual-golden-r3-v10`
- Locked base: `0feeb3f35ef164591678caba96fb46477b366f52`
- Activation head: `c04df2046eff98e2c1a348d58a4faae10bebd883`
- Current phase: local bootstrap / preflight only

This handoff does not broaden the activated Decision. If any instruction below conflicts with `project_state/decision_packet.md`, the activated Decision wins and execution must fail closed.

## Required local execution

Use a dedicated clean worktree for the exact v10 branch. Before running anything, fetch and prove both `origin/main` and the merge-base remain exactly `0feeb3f35ef164591678caba96fb46477b366f52`, and prove branch HEAD is exactly `c04df2046eff98e2c1a348d58a4faae10bebd883`.

Run, in order:

```powershell
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
python -m reverse_agent.project_gate transition-command-plan --state-dir project_state
python -m reverse_agent.project_gate transition-lint --state-dir project_state
python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre
```

Success condition is an actual repository-owned `PRE_EXECUTION_AUTHORIZED` result with zero blockers.

Only these generated gate paths may change in this phase:

```text
project_state/gates/command_plan.json
project_state/gates/startup_snapshot.json
project_state/gates/bootstrap_state.json
project_state/gates/transition_command_plan_preview.json
project_state/gates/transition_preflight_result.json
```

If successful, commit only those generated artifacts and fast-forward push the v10 branch. Do not force-push.

## Fail-closed conditions

Stop immediately and report exact evidence if any of the following occurs:

- `origin/main` is no longer the locked base;
- branch HEAD or merge-base differs from the locked values before execution;
- transition lint fails;
- transition preflight is anything other than `PRE_EXECUTION_AUTHORIZED`;
- any path outside the five generated gate paths changes in this phase;
- the activated Decision would need editing;
- a dependency/browser install, browser run, snapshot update, provider/model call, credential read, Ready transition, merge, workflow dispatch or workflow rerun would be required.

Do not patch the immutable v10 Decision in place. A Decision-contract defect requires a fresh successor round.

## Next phase only after preflight success

Do not perform this phase until the generated preflight is committed and server-side readback confirms `PRE_EXECUTION_AUTHORIZED`. The subsequent bounded implementation is limited to replaying the three accepted test-side visual files and the exact 24 locked PNG blobs already authorized by the v10 Decision, followed by deterministic non-browser validation and Draft-PR publication/binding.
