# Unattended v0 security boundary

The platform accepts only normalized, repository-relative paths explicitly
approved by a bounded work item. Empty scopes, repository-wide patterns,
absolute paths, traversal, and symlink escape fail closed. Each attempt gets
one workspace below `.var/unattended/{workflow-id}/{attempt}`.

Secret boundaries:

- `GITHUB_TOKEN` remains host-side and is never passed to OpenHands, Agent
  Canvas, LiteLLM, or a sandbox.
- OpenHands receives only the fixed local LiteLLM endpoint configuration,
  never the upstream model-provider credential.
- the provider credential is a Docker Compose file secret mounted only at
  `/run/secrets/openai_api_key` in LiteLLM. The fixed wrapper reads it inside
  that container and immediately `exec`s the pinned LiteLLM command.
- tracked configuration contains variable names only; no value belongs in Git,
  test output, probe output, or uploaded evidence.

The maintainer-only credential flow for the later independent probe is:

```text
hidden terminal input or password-manager export
-> temporary regular file outside the repository
-> chmod 0600
-> set UNATTENDED_OPENAI_API_KEY_FILE to that non-secret path
-> secret-preflight (only PRESENT/MISSING and PASS/FAIL)
-> run the separately authorized audit
-> delete the temporary file
-> revoke the provider key
```

Never place a provider value in `.env`, a Work Item, task argument, Issue, PR,
CLI argument, tracked file, log, hash, header, or evidence artifact. The
preflight intentionally fails outside WSL/Linux because its `0600` guarantee
depends on POSIX permissions.

Docker boundaries:

- the reverse-agent worker has no Docker socket mount and cannot create
  containers directly;
- only the OpenHands host-side sandbox controller receives the socket;
- sandbox work is restricted to the attempt workspace;
- the adapter rejects path traversal and symlinks before submitting work.

Agent output is evidence, not platform acceptance. Deterministic acceptance
checks outside the agent decide whether an attempt passed.
