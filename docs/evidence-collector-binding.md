# Trusted collector execution binding

Scope: #1039, the A2a residual under #1010 / #379 / #653. This document is
not an authorization grant or independent acceptance record.

## What the existing collector now checks

`collect_live_evidence` continues to use the loaded `AuthorityBundle`, existing
Git/GitHub adapters, approved command selection, shell-free command runner and
`ExecutionEvidence` factory. No second store or verifier framework is introduced.

A missing runner does not establish test success. An empty selection of required
`phase=test` commands explicitly returns `passed: false` with
`required_test_commands_missing`. Optional and non-test commands remain excluded;
the collector never invents a replacement test command.

Before executing any selected command, the complete selected batch is checked:
its IDs must be nonempty strings, unique and present in the bundle's admitted ID
tuple; command text must be a string and parse under the existing shell policy.
A malformed later command blocks the entire batch before its first invocation.
Invalid-selection diagnostics contain an index and stable error code, not the
submitted command text. The externally loaded bundle is still the authority
boundary; this consistency check does not authenticate arbitrary Python objects.

A runner result must have its documented three-element tuple shape, a genuine
integer exit code and textual stdout/stderr. Boolean, floating-point, string or
missing exit codes cannot compare equal to zero and become success. A malformed
result raises `test_runner_result_invalid`; a genuine nonzero exit remains a
recorded test-command failure. Successful exit does not itself prove meaningful
test counts or complete functional coverage.

For the production `LiveGitAdapter`, Git resolves the actual worktree root with
`rev-parse --show-toplevel`. The collector passes that absolute canonical root as
the command runner's explicit `cwd`, including when observation started from a
subdirectory. A runner's unrelated default directory cannot supply passing tests
for the observed repository. A root observation failure has no cwd fallback.

The collector reobserves HEAD and the production worktree root before and after
each command, and again after GitHub workflow observation before creating live
evidence. Observed drift raises `head_changed_during_collection` or
`worktree_changed_during_collection`; observation errors propagate rather than
producing a successful live result. Initial wrong-head and workflow-validation
denials remain unchanged.

## Verification

`tests/platform_v1/test_collector_execution_binding.py` covers missing execution,
invalid command identity/text, whole-batch prevalidation, runner result types,
command/workflow observation drift and positive controls. Temporary real Git
repositories and fixed Python/pytest subprocesses test a wrong runner default
cwd, root resolution from a subdirectory and a real commit made during a test.
Bundle and GitHub observations in these tests are explicitly controlled doubles;
no real model/provider call or GitHub mutation is needed. Existing evidence
adapter tests are retained unchanged. The new file is selected by the existing
Platform V1 blocking suite, not only by a nonblocking diagnostic.

## What this does not prove

- The private Python factory token, injectable adapters and a `live` mode label
  are not isolation against hostile code already running in the trusted host.
  Protected verifier processes, execution identities and permission separation
  remain independent A2 work under #379.
- Root/HEAD observations are not an atomic filesystem snapshot. Dirty worktree
  changes, changes reverted between reads (ABA), other mutable refs and the final
  observation-to-use interval are not claimed solved here. Existing exact-artifact
  functional validation remains distinct from this collector.
- A successful approved command may still have inadequate tests. This slice
  prevents zero selected commands from passing; it does not inspect JUnit/TAP
  test counts or prove that every requirement has an admissible oracle. Those
  responsibilities remain with the existing functional validation contracts.
- Existing GitHub workflow observations are preserved, not upgraded to proof of
  a protected workflow version or GitHub App identity. Same-name workflow/source
  authenticity and signature/provenance requirements remain separate work.
- Local adapter tests and hosted CI are evidence of their stated test scope, not
  independent product acceptance, deployment, a complete autonomous owner or
  permission to mark a PR Ready/merge it. Publication authority remains Path A/B.

The intended boundary is narrow: a trusted collector must not claim a passing
execution that it did not select, did not receive a valid result for, or observed
against a different Git checkout. Other trust assumptions remain explicit.
