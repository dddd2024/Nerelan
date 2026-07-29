# Unattended v0 security boundary

The platform accepts only normalized, repository-relative paths explicitly
approved by a bounded work item. Empty scopes, repository-wide patterns,
absolute paths, traversal, and symlink escape fail closed. Each attempt gets
one workspace below `.var/unattended/{workflow-id}/{attempt}`.

Secret boundaries:

- `GITHUB_TOKEN` remains host-side and is never passed to OpenHands, Agent
  Canvas, LiteLLM, or a sandbox.
- OpenHands receives a LiteLLM endpoint credential, never the upstream model
  provider credential.
- provider credentials terminate at LiteLLM.
- tracked configuration contains variable names only; no value belongs in Git,
  test output, probe output, or uploaded evidence.

Docker boundaries:

- the reverse-agent worker has no Docker socket mount and cannot create
  containers directly;
- only the OpenHands host-side sandbox controller receives the socket;
- sandbox work is restricted to the attempt workspace;
- the adapter rejects path traversal and symlinks before submitting work.

Agent output is evidence, not platform acceptance. Deterministic acceptance
checks outside the agent decide whether an attempt passed.
