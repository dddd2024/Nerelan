# P0-2 optimization validation, 2026-10-14

The follow-up implements deterministic compression, bounded on-demand retrieval,
explicit AI summary triggers and durable cross-Agent recovery. It adds no model
calls to startup or CI, new state database, dependencies or governance changes.

## Real interface result

[`live-result.json`](live-result.json) records the authenticated Task API probe
on source commit `da75582f6eb45b933f7c06ca87e47477e7854317`, after merging current
main's P0-3 resource-management changes. The final evidence commit adds documents
only; per-file SHA-256 values bind the product/runtime modules actually loaded.
`code_sha256` hashes the Windows clone bytes; `code_sha256_lf` normalizes CRLF
to LF and matches all nine files in the final candidate regardless of checkout
newline conversion.

The probe created and approved a real Goal/Plan and launched its bounded Task
without executing product development. Its 80 historical events are explicitly
controlled stress fixtures, not claims about earlier model work. Each phase ran
in a separate process against the same persistent TaskStore:

1. Prepare Goal/Task and stress history; exit with zero model calls.
2. Explicit authenticated summary POST used the saved native Claude Opus planner,
   saved its non-authoritative source-bound summary, wrote a handoff and exited.
3. A new host process restored the handoff as `gpt-reviewer`. A real saved-native
   GPT call consumed that rebuilt packet; task ID, Goal ID/revision, Git head and
   authority matched exactly. The summary survived restart, and on-demand
   retrieval returned a bounded match. The activated window was stopped.

Both real calls completed. The restored packet is 16,273 UTF-8 bytes inside its
16,384-byte budget. The retrieval response is 2,216 bytes inside its 4,096-byte
budget. Native token fields are retained exactly as reported. Cash costs and
remaining subscription quotas are UNKNOWN. This proves the mechanisms and fact
recovery on controlled input; it does not prove summary quality on arbitrary real
history, lower costs, a successful P0-4 paired benchmark, or execution acceptance.

An earlier successful probe on `2febae02462d9db5b48596501beebf22cf968781` is
preserved externally at `C:/ncb-context-optimization-20261014/result.json`. The
checked-in result is the repeat on the integrated source above.

## Verification

- Context/optimization and native/OpenCode adapters plus new usage ledger:
  `234 passed, 2 skipped` after integration.
- Context/optimization, trusted host and Task HTTP suites:
  `273 passed, 4 skipped` before the main merge; latest context-specific regression
  was separately rerun, `7 passed`.
- Context/optimization and durable execution: `113 passed, 1 skipped`, with the
  existing intentional crash-seam thread warning.
- Independent integration-head context checks: `37 passed, 1 skipped`.
- `git diff --check` passed. Exact final-head CI and independent verdict are
  recorded in the PR; these local runs do not substitute for landing gates.

Focused cases cover Unicode budgets, long-history original retrieval, stale
snapshots, secret redaction, post-model input races, duplicate summary requests,
completed summary/handoff restart, fresh status overlay, changed execution,
changed visibility/Git scope, malformed cache and missing usage. A process-loss
reservation deliberately remains unknown/RUNNING and makes zero automatic retries.

## Reproduction

[`live_probe.py`](live_probe.py) is an explicitly invoked native-model probe,
never a CI test. It needs already authorized native planner/GPT account bindings
and managed CLI login. It reads public binding/configuration through the existing
host and delegates credential use to existing runtime adapters; no secrets are
printed or archived. Use a new empty root and a clean frozen source checkout:

```powershell
$env:NERELAN_CONTEXT_PROBE_SOURCE = (Get-Location).Path
$env:NERELAN_CONTEXT_PROBE_ROOT = 'C:/nerelan-new-context-probe'
python docs/benchmarks/context-optimization-20261014/live_probe.py prepare
python docs/benchmarks/context-optimization-20261014/live_probe.py summarize
python docs/benchmarks/context-optimization-20261014/live_probe.py recover
```

The second and third phases import the frozen clone, not a later edited checkout.
Existing roots are refused during preparation. Failure receipts remain in the
probe root; they must not be presented as successful live validation.
