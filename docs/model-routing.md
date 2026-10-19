# Context and evidence routing

Task plans declare `context_need` (input tokens) and `needs`. The host reserves
the context packet's byte budget at selection and rechecks its measured UTF-8
size immediately before execution, using a conservative one-byte/token bound.
All models must pass executor, Owner, context, modality, quota, willingness and
review-independence checks. A pin cannot bypass those checks. Unknown models
can receive easy work; difficulty 3–5 requires measured evidence. An Owner capability-table entry is provisional
until calibration or real runs establish evidence. Names do not establish capability.

The following JSON files live beside `model_setup_state.json`. They contain no
credentials. Missing configuration uses conservative defaults; malformed Owner
configuration blocks selection.

`model_routing_overrides.json`:

```json
{
  "bindings": {
    "binding-id": {
      "exclude": false,
      "max_difficulty": 4,
      "allowed_content": ["code", "security_simulation"],
      "denied_content": ["writing"],
      "notes": "Owner judgment"
    }
  },
  "connections": {"free-gateway": {"cost_class": "free"}},
  "paid_api_windows": [],
  "reset_buffer": 0.03
}
```

Content classes are task kinds or `security_simulation`; modalities belong in
`needs`. Explicit connection costs are `free`, `subscription`, or `paid_api`.
Native sessions default to subscription; keyless and explicit free model ids
default to free. The Owner-observed WorkBuddy, WorkBuddy-AI, Trae-CN and
OpenCode Zen free namespaces default to free; Copilot is a limited subscription.
Other API connections default to paid. API keys never imply
free access. To allow paid inference, the Owner names an active window in
`paid_api_windows` (or provides `allow_paid_api` in trusted window authority).
The window must still authorize and budget the work. Paid models never receive
exploration tasks and are never probed without this window allowance.

`model_capabilities.json`:

```json
{
  "version": 1,
  "models": {
    "deepseek-v4.1-flash": {
      "tiers": {"code": 4, "analysis": 4},
      "notes": "Owner supplied benchmark judgment; not a measured result"
    }
  }
}
```

Keys match exact model ids, optionally without the provider namespace. Measured
kind/difficulty buckets take precedence over this table; the last-resort prior
is unproven tier 2. Trait precedence is Owner override, measured observation,
catalog metadata, then conservative context/modality defaults.

Availability is distinct from catalog discovery. The existing host discovery
path records sanitized listings from every enabled connection; routing binds
their models to compatible executors and preserves existing bindings. Listings
also carry Magpie traits and native endpoints. Sanitized listings persist in
`model_catalog_observations.json`; availability remains separate. Responses-only models use the
Responses adapter and an endpoint-bound relay lease. Namespaced Claude Code
model ids are accepted only for API relay mode.

The host checks recent successful tasks or `model_availability.json`. Successful
requests and entitlement failures cache for 24 hours; transient errors for five
minutes. Probes have a global one-minute rate limit and issue only `Reply OK`
through the host credential relay. Runtime probing requires the existing live
model-control opt-in plus `REVERSE_AGENT_ROUTING_PROBES=1`, and an active
window that does not prohibit model/provider calls. Native Owner subscriptions and Magpie `codex/*` and
`claude/*` are never probed; they need recent successful work or an injected
verified observation. No startup or CI inference is enabled. Discovery failures
do not establish availability. Dispatch entitlement errors invalidate the
pairing and trigger another route without capability-failure evidence.

Refusals use the maintained patterns in `routing_inputs.py`, plus explicit
executor policy reports. Text heuristics apply only without substantive file
changes. Refusal attempts update content-class willingness, not capability.
Unknown refusal risk has a conservative 25% scoring prior; measured low-refusal
models are preferred. Retries obey the window retry budget, preserve difficulty and the original authorization statement, exclude
previous refusing model identities, and use the same or higher tier. Exhausting
the candidates produces `BLOCKED no_willing_model` with refusal evidence.

The reset-signal input is an injected read-only mapping: `state`,
`expected_reset_at` (UTC ISO or epoch), `announcement_id`, and `validated`.
Here `validated` means an official global-reset announcement, not merely a
well-formed timestamp. Explicit personal/banked grant scopes are neutral.
Until PR #1247 supplies that reader, absence/fetch failure is `UNKNOWN`.
Only a validated `PLAN_ONLY` announcement with an absolute future time drains
Codex weekly quota toward the configurable 3% buffer. It never grants capacity
or bypasses real quota checks. Drain targets are split over remaining five-hour
windows; no tasks are generated. `reset_decision(..., demand=False)` records
`NO_DEMAND`. After the stated time or on `REFRESH_QUOTA`, the host invalidates its
quota cache and reads the existing subscription-quota path before routing.
A failed refresh retains prior quota evidence and makes the forecast neutral.
Persistently low quota after 15 minutes marks the source unreliable and returns
to normal cost. Decision events record the announcement, target, buffer,
adjustment, capability source, chosen model and exclusions. Selection failures
project as blocked activity in run details.

## Calibration hook

`calibration_suite_v1.json` fixes five small real tasks and their independent
acceptance checks, covering every task kind. Run three samples per case.
`routing_capabilities.calibration_profiles` is the pure ingestion hook: it turns
versioned, independently checked outcomes into the same `task_buckets` shape as
`model_profiles.compute_agent_profiles`. Pass these profiles to `select_model`
or combine them with real-run buckets by retaining sample counts. Refusals do
not count as capability failures. The host suite runner, durable calibration
result publication, and Settings editor remain follow-ups; this change does
not run calibration models automatically. CLI exit success alone cannot set
the calibration success boolean.
