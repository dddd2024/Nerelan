# Native Codex execution

Nerelan's native `codex` executor runs the installed CLI directly, independently
of OpenCode. It uses the same Goal/TaskStore, repository checks, durable leases,
checkpoints, functional checks and accepted-artifact handoff as other executors.
It supports **single** mode. Sequential roles and native session continuation
are not supported and are rejected; the adapter never substitutes OpenCode or
the deterministic fixture executor.

## Setup and readiness

The trusted host can opt into the provider-free CLI capability and managed-login
probe with `REVERSE_AGENT_CODEX_ENABLED=1`. Set `REVERSE_AGENT_CODEX_EXE` to the
installed native executable if it is not discoverable on PATH. Startup and CI
make zero model calls. With no explicit probe, Codex remains visible as an
unready executor. A successful CLI help/login-status probe proves launch
capability and existing ChatGPT login, **not** model entitlement, quota,
inference success or independent acceptance.

In Settings, create a separate Connection with Provider `codex`, authentication
`external_cli_session`, and session metadata URL `https://chatgpt.com`. The
provider preset fills these fields. This URL is metadata, not an API relay.
Connection identity is `openai` / `codex-cli` / `codex` for upstream, protocol and
executor namespace. OpenCode auth probes never set its availability, and an
OpenCode binding cannot reuse this native Connection.

Create a Binding selecting Codex, that Connection and an explicitly selected
native model ID. IDs do not carry an OpenCode provider prefix. The model field
does not imply a discovered or entitled model catalog. Browser and Nerelan
code never read or copy the CLI auth file or accept an API key for this
Connection. Existing saved OpenCode, DeepSeek and Agnes configuration is not
migrated or rewritten by adding a native Connection.

## Execution and evidence

Native tasks require a saved native Binding and the configured repository's
exact origin identity. The HTTP Task creator and Goal materializer freeze the
trusted source HEAD as an exact base; artifact consumers use their accepted
producer commit. The shared preparation helper creates a fresh linked worktree
outside the configured source and refuses existing destinations. Recovery
retains the persisted workspace/head and native executor, and does not
redispatch a completed accepted role.

The CLI receives structured argv, explicit cwd/model, `--json`, `--ephemeral`,
`--ignore-user-config`, explicit `read-only` or `workspace-write` sandbox and
noninteractive approval policy. It does not receive `--ignore-rules`, a sandbox
bypass, arbitrary extra writable directories, provider keys, endpoint overrides
or OpenCode configuration. Saved managed login remains owned by the CLI. The
OpenAI provider is explicit. A workspace `.codex/config.toml` is rejected without
reading it, because it could replace provider or hook authority.
The
normal Task path uses workspace-write; read-only is available to trusted callers.

JSONL parsing bounds frames, total output and event count, projects allowlisted
progress fields, and redacts before public truncation. Timeouts terminate only
the owned process tree through the existing process-confinement helper. CLI
exit, malformed/incomplete streams, terminal ordering and missing final messages
remain separate failures. A readable final response is persisted in Task events.

Reported CLI token counts are shown only when valid. The usage ledger records
`UNKNOWN`, without numeric zeros, because native CLI output does not supply all
required reasoning/cache-write/cost facts. Subscription tokens are not converted
to fabricated dollar cost. Internal CLI provider requests are not observable
from a single `turn.completed` event; an invocation/time bound is not proof of
an exact underlying provider-request count. Live trials require applicable
authority whose budgets can actually be met and evidenced.

CLI exit zero proves no functional acceptance. The host still runs approved
functional checks, verifies Goal/run/lease/base/head/tree/report identities, and
retains accepted artifacts through the existing verifier. Validation-only
artifact consumers run host checks without a second model dispatch. A terminal
Task remains ready for independent review, and the UI explicitly states that
different-model review and final acceptance are pending.

## Validation boundaries

Provider-free protocol, real local subprocess/Git, HTTP/SQLite, Goal,
functional-check and durable-recovery fixtures cover the native integration.
They are not real model execution, account entitlement, model contribution,
independent-model review, natural CI or mainline landing evidence. Those require
separate actual observations. Draft publication does not authorize Ready/Merge.
