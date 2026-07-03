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

## Session Bundle

`UserSolveSessionBundle` packages the user-facing result, trace summary,
fallback decision, validation status, evidence status, missing-evidence summary,
public message, next action, and developer-only audit references into one
in-memory contract. It is the future UI/API boundary shape, but it is not a
Web/API endpoint, database row, queue job, scheduler task, upload-ingestion
record, runner dispatch, or persistent `project_state/solve_tasks` artifact.

Default session serialization is user-safe and redacts internal project-state
paths, report paths, command-plan paths, and developer trace references.
Developer serialization is explicit and may retain those references for audit
use. Session validation preserves the lower-level rules: `candidate_found` may
remain pending validation, `verified` requires passed validation and complete
evidence, missing evidence maps to deep-analysis/fallback guidance, and
fallback decisions remain non-executing metadata.
