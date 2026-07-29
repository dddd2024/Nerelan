# Unattended v0 security boundary

The platform accepts only normalized, repository-relative paths explicitly
approved by a bounded work item. Empty scopes, repository-wide patterns,
absolute paths, traversal, and symlink escape fail closed. Each attempt gets
one workspace below `.var/unattended/{workflow-id}/{attempt}`.

Secret boundaries:

- `GITHUB_TOKEN` remains host-side and is never passed to OpenHands, Agent
  Canvas, LiteLLM, or a sandbox.
- each disposable OpenHands Attempt receives only the fixed local LiteLLM
  executor endpoint and its bounded execution credential, never the upstream
  provider credential or LiteLLM master key.
- the provider credential is a Docker Compose file secret mounted only at
  `/run/secrets/openai_api_key` in LiteLLM. The fixed wrapper reads it inside
  that container and immediately `exec`s the pinned LiteLLM command.
- the LiteLLM executor credential is a native Virtual Key limited to
  `unattended-v0`, chat-completion/model-discovery routes, a daily budget,
  bounded RPM/TPM, and one parallel request. It has no management authority.
- the Virtual Key file is mounted only into the one-shot bootstrap. The
  trusted adapter supplies it in the LLM request; it is absent from the
  Attempt container environment.
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
- only the separate trusted `SandboxController` process may address Docker;
- the AI-controlled Agent Server container has no Docker socket;
- sandbox work is restricted to its single RW Attempt-workspace bind;
- the root filesystem is read-only, temporary paths are tmpfs, all
  capabilities are dropped, `no-new-privileges` is set, and CPU, memory, and
  PID counts are bounded;
- the Attempt joins only an internal network shared with LiteLLM, with no
  public egress or control-service attachment;
- the adapter rejects path traversal and symlinks before submitting work.

Agent output is evidence, not platform acceptance. Deterministic acceptance
checks outside the agent decide whether an attempt passed.
