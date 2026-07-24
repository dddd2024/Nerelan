# Architecture Spine v1

Architecture Spine v1 is a non-dispatching vertical slice for ordinary engineering workflow state.

```text
Planning Reference -> GitHub Work Item -> Workflow Identity -> R0-R3 Risk
  R0/R1 -> Standard Path
  R2/R3 -> Trust Authorization Port
  -> Deterministic Acceptance Gate
```

Planning artifacts are read-only context and never command authority. GitHub Work Items provide task identity. GitHub branch, pull-request, and check data are stored only as sourced, timestamped cache observations; GitHub remains authoritative.

The deterministic classifier routes read-only work to R0, bounded local edits to R1, workflow/dependency/network/publication work to R2, and binary execution/debugging/secrets/destructive work to R3. Unknown operations block. Conflicting known operations select the highest risk.

The shadow runtime uses LangGraph as its only workflow runtime and an in-memory checkpointer. Its nodes validate fixtures, classify risk, request authorization, and calculate acceptance. They do not execute shell commands, mutate repositories, access networks, invoke models, or run reverse-engineering tools.

R2/R3 requests cross a narrow `TrustAuthorizationPort`. The compatibility adapter reuses transition validation without reading legacy closeout, final-check, seal, report-summary, context-sync, or publication mirrors. R0/R1 bypass that port.

This slice does not install BMAD, dispatch coding agents, mutate GitHub, run unknown binaries, merge pull requests, or begin the Binary Evidence Firewall workstream.
