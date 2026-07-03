# User Solve Layer

The User Solve Layer is a pure result-contract layer above the existing pipeline,
harness, job, and runner machinery. It does not execute samples, tools, runners,
debuggers, subprocesses, network calls, or remote dispatch.

Default user output contains a compact status, validation status, evidence
status, message, answer, and candidates. Internal engineering references such as
`project_state` artifacts and command-plan/report paths are redacted from default
serialization. Developer serialization is explicit and may retain trace
references for audit work.

`candidate_found` is allowed while validation is pending. `verified` is allowed
only when validation passed and a usable answer or candidate exists. Evidence
gaps map to non-terminal deep-analysis statuses unless a policy or environment
blocker requires a blocked result.

## Trace And Fallback Metadata

`UserSolveTaskTrace` records the task id, user-facing status, engineering
status, candidate sources, fallback step records, missing evidence, validation
record, artifact references, and ordering metadata. User serialization redacts
internal project-state references by default; developer serialization is the
explicit audit path.

`FallbackLadder` is a non-executing policy contract. Its ordered steps are
`fast_strings`, `ida_summary`, `targeted_decompile`,
`constant_material_extract`, `solver_attempt`, and `runtime_validation`. Static
steps can be selected automatically from synthetic state. Steps that imply local
execution, dynamic validation, solver activity, or other elevated capability
remain blocked unless explicitly authorized elsewhere, and the ladder itself
never executes or dispatches them.
