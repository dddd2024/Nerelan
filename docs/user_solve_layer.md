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
