# Route cache efficiency: Trae CN versus the GLM group

Investigation for #1504 / #1267 / #296, based on repository head
`d034183eaacb5f5c99ff0aebe614feab72a85d7a`. Development was performed directly in
the Owner-assigned worktree, without platform dispatch or model calls, under the
explicit task instruction. No routing or runtime configuration was changed.

## Finding and limits

**[OBSERVED] The available Magpie request cache already has zero cache reads for
the Trae GLM route.** There is no positive Trae cache count in this source that
Nerelan's task-observation parser could have discarded. One sustained sequence
retains the same gateway session and account handle, so account rotation does
not explain its zeros. Current config generation enables `setCacheKey` for both
the direct and relay provider blocks and preserves both route names.

**[INFERRED] Investigate the Trae/Magpie reporting and forwarding boundary before
changing Nerelan routing or its OpenCode usage parser.** This is a bounded
localization, not proof that Trae does not implement caching. The JSONL is a
Nerelan-normalized Magpie export, not raw upstream usage: its importer converts
missing counters to zero. Without the original CSV/response and outbound request
fields, unsupported caching, omitted telemetry, a missing export field, and
upstream cache-key handling cannot be distinguished conclusively.

| Candidate cause | Evidence and disposition |
| --- | --- |
| (a) Trae does not support/report caching | Consistent with both sources; support versus reporting remains unverified. |
| (b) Positive Magpie cache reads dropped by the task parser | No such positive row found for this route. Parser fixtures retain positive reads for either model label. A missing raw CSV field is still possible. |
| (c) Wrong provider block, lost session, or account switching | Config fixtures enable the option in both blocks. The sustained Magpie sequence has one session and one account; request-body `prompt_cache_key` forwarding and the historical child config remain unverified. |
| (d) Other measurement limits | Three task observations are UNKNOWN timeouts; normalized Magpie zeros need not be explicit upstream zeros; the group workload predates the cached Magpie interval. |

No implementation defect causing these Trae zeros has been established, so this
change records the evidence and a proposed rule instead of a speculative fix.

## Sources and measurement window

**[OBSERVED]** SQLite was opened only with
`sqlite3.connect('file:F:/nerelan-run-data/tasks.sqlite3?mode=ro', uri=True)`.
The frozen observation interval is inclusive:
`2026-11-24T00:00:00Z` through `2026-11-28T08:45:38Z`. `created_at` is the
observation insertion time, not necessarily the upstream request time.

**[OBSERVED]** A single read of
`F:/nerelan-run-data/magpie_usage_cache.jsonl` at
`2026-11-28T09:45:15.879034Z` contained 1,909 rows, 1,105,830 bytes, SHA256
`9016f1459230d934cb168d4ffcc0a153ddc2994f8c6f9f94b7919d3435f55874`.
The byte count and digest identify that snapshot. Its UTC request-time coverage was
`2026-11-27T03:38:57Z` through `2026-11-28T09:44:49Z`. The live cache continues
to change; line numbers below refer to this snapshot. Only allowlisted usage
fields were inspected or quoted, with no configuration credentials read.

## Task observation totals

**[OBSERVED]** These are persisted observation counts, not verified upstream
call counts. Prefix `openai-compatible/` is omitted from the table only.
The ratio is `sum(cache_read) / (sum(input) + sum(cache_read))`, calculated from
known counters. All known cache-write counters here are zero; thus including
cache writes in the denominator gives the same ratio. NULL is not a zero read.

| Model route | Observation rows | Non-cached input units | Cache-read units | Read ratio | Distinct tasks |
| --- | ---: | ---: | ---: | ---: | ---: |
| trae-cn/glm-5.3-max | 127 | 6,004,808 | 0 | 0.000000 | 8 |
| group/nerelan-glm-5-3 | 64 | 328,452 | 3,634,880 | 0.917127 | 1 |
| agnes/agnes-2.5-flash | 453 | 3,893,544 | 23,239,168 | 0.856500 | 7 |
| minimax-code/MiniMax-M3 | 105 | 272,438 | 4,951,416 | 0.947847 | 3 |
| raccoon/raccoon-090dd3 | 37 | 747,564 | 706,061 | 0.485724 | 2 |

Trae comprises 106 `step_finish/PARTIAL` observations (5,172,469 input),
18 `assistant_message/OBSERVED` observations (832,339 input), and three
`timeout/UNKNOWN` observations with NULL input/cache counters. Therefore 124
numeric observations, rather than all 127 rows, support the zero ratio.
The group comprises 64 `step_finish/OBSERVED` rows, inserted on November 24
between `13:29:04Z` and `13:29:07Z`.

Exact selected SQLite fields, quoted as JSON projections:

```json
{"id":"usage-babb37fc1299b7fc874735cbf7b1eca709a18f51a2618573f000b0f5c14a47ce","task_id":"task-1795498956393-d0e421041949","model_id":"openai-compatible/trae-cn/glm-5.3-max","provider_id":"openai-compatible","source_kind":"step_finish","status":"PARTIAL","input_units":11132,"cache_read_units":0,"output_units":35,"created_at":"2026-11-24T06:40:38Z"}
{"id":"usage-70e6a60940144075d75189e267335bd9e373c9feac39151f4a6ab778fffc80e5","task_id":"task-1795847577459-2f73be0deb79","model_id":"openai-compatible/trae-cn/glm-5.3-max","source_kind":"step_finish","status":"PARTIAL","input_units":10960,"cache_read_units":0,"cache_write_units":0,"output_units":112,"reasoning_units":337,"created_at":"2026-11-28T06:56:33Z"}
{"id":"usage-477f00ec1b2dcfd406ab000d5e743fc35cbf234df80751a5872fb1e2ae1c5839","task_id":"task-1795525787015-156836ff9f24","model_id":"openai-compatible/group/nerelan-glm-5-3","provider_id":"openai-compatible","source_kind":"step_finish","status":"OBSERVED","input_units":33087,"cache_read_units":11008,"output_units":124,"created_at":"2026-11-24T13:29:04Z"}
{"id":"usage-447a4b883d13ceb7368dbeb111ce1622015e6c728573b15b9f7ed5c38eccd43e","task_id":"task-1795525787015-156836ff9f24","model_id":"openai-compatible/group/nerelan-glm-5-3","provider_id":"openai-compatible","source_kind":"step_finish","status":"OBSERVED","input_units":1846,"cache_read_units":44032,"output_units":143,"created_at":"2026-11-24T13:29:04Z"}
```

Joining `tasks.id = task_usage_observations.task_id` shows
`binding_ref=magpie-trae-cn-glm-5.3-max` for all eight Trae tasks and
`binding_ref=magpie-group-nerelan-glm-5-3` for the one group task. Both observation
labels use `provider_id=openai-compatible`; the route namespace is part of
`model_id`, not that provider field.

## Magpie request comparison

**[OBSERVED]** Exact filter `provider == 'trae-cn'` and
`asked_model == 'trae-cn/glm-5.3-max'` selects 75 unique request IDs:
65 status-200 rows and ten status-429 rows. Their counters total 3,160,177
input, zero cache reads, zero cache writes, 18,496 output, and 11,790 reasoning.
All ten 429 rows have zero token counters and provide no evidence about cache
effectiveness. All selected rows have `normalization_version=3`.

Of these 75 rows, 64 carry session `ses_ddf23a133ffeBGSpLlQe0XN9ne` and
account handle `acct_5c0db789fdef`: 63 successful rows and one 429. That sequence
totals 3,160,149 input with zero cache reads/writes. Two successful rows have a
NULL session and 14 input each. The remaining nine rows are 429s in two other
sessions, with the same account handle. No account rotation is visible here.

Exact selected JSONL fields (snapshot lines 1235, 1236, and 754 respectively):

```json
{"time":"2026-11-28T02:34:03-04:00","request_id":"2026-11-28T02:34:03-04:00:glm-5.3-max","asked_model":"trae-cn/glm-5.3-max","served_model":"glm-5.3-max","provider":"trae-cn","session":"ses_ddf23a133ffeBGSpLlQe0XN9ne","account_id":"acct_5c0db789fdef","status":200.0,"normalization_version":3,"tokens":{"cache_read":0,"cache_write":0,"input":1585,"output":444,"reasoning":431}}
{"time":"2026-11-28T02:34:06-04:00","request_id":"2026-11-28T02:34:06-04:00:glm-5.3-max","asked_model":"trae-cn/glm-5.3-max","served_model":"glm-5.3-max","provider":"trae-cn","session":"ses_ddf23a133ffeBGSpLlQe0XN9ne","account_id":"acct_5c0db789fdef","status":200.0,"normalization_version":3,"tokens":{"cache_read":0,"cache_write":0,"input":10960,"output":449,"reasoning":337}}
{"time":"2026-11-27T10:07:37-04:00","request_id":"2026-11-27T10:07:37-04:00:sn-glm-5-3","asked_model":"group/nerelan-glm-5-3","served_model":"sn-glm-5-3","provider":"raccoon","session":null,"account_id":"acct_3cab5d6b6c77","status":200.0,"normalization_version":3,"tokens":{"cache_read":0,"cache_write":0,"input":14,"output":3,"reasoning":2}}
```

The exact group filter selects only that **one** 14-input request, with zero
reads. `group/nerelan-glm-5-3-flash` is a different route and is excluded.
The group row demonstrates a Raccoon-served group request in this interval; it
cannot establish which account/provider served the November 24 task or validate
that earlier task's 0.917127 ratio against Magpie.

There is also one `asked_model=trae-cn/glm-5.3-max` row with
`provider=session-unknown`, NULL account, status 0, input 32,828 and cache reads
zero. It is excluded from the known-provider aggregate. It must not be added
as another confirmed upstream debit merely because its session matches.

**[INFERRED]** The November 28 task (62 numeric observations, 3,158,564 input)
and the long Magpie sequence have consistent input/cache totals after excluding
the initial 1,585-input request, but this is not request-level attribution.
No `agent_session_id` was found on this task's events. The quoted 10,960-input
rows also differ in output representation: OpenCode has 112 output plus 337
reasoning, while Magpie has 449 output including that reasoning. Neither totals
nor coincident token values substitute for task-to-request identity receipts.

## Config and parser checks

**[OBSERVED, source inspection at the base head]**

- `opencode_executor.build_binding_config_content` sets `options.setCacheKey=True`
  in both the leased `reverse-agent-relay` block and the non-leased
  `resolution.provider_id` block. `_extract_provider_facing_model` strips only
  the first provider prefix, retaining `trae-cn/glm-5.3-max` or
  `group/nerelan-glm-5-3`. Compaction is `{"auto":true,"prune":true}`.
- `_normalize_usage_metrics` reads `tokens.cache.read` into `cache_read_units`
  without a route-specific branch. The database's nonzero group observations
  establish that positive counts can reach persistence.
- `magpie_usage_ingest._TOKEN_COLUMNS` maps `cache_read` to `cache_read_tokens`.
  `_normalize` uses `int(_number(raw.get(column)) or 0)`. Thus these normalized
  exports do not preserve the distinction between an absent CSV value and an
  explicit zero. No original CSV was supplied, so a field mismatch/drop at that
  boundary is unverified; the cached JSONL alone cannot diagnose it.

**[OBSERVED, synthetic checks]** Eight in-process assertions passed: config
generation for each route under `auth_method=none` and leased `api_key` (four
cases), and parser preservation of cache reads 0 and 44,032 under each route
label (four cases). These used fixture IDs and an unused loopback URL, and made
no network calls. They prove current generated config and parser behavior,
not that a historical production child loaded this config or sent a cache key.

## Proposed rule: observed route cache ratio as an effective-cost input

**[INFERRED / PROPOSAL, not implemented]** Reuse `usage_ledger` counters and
`routing_inputs` cost inputs rather than adding a second ledger or hardcoding
a Trae penalty. For comparable eligible routes, estimate:

```text
R = sum(cache_read) / sum(input + cache_read + cache_write)
estimated_prompt_cost = expected_prompt_units * (
    fresh_fraction * fresh_input_price
  + R * cache_read_price
  + write_fraction * cache_write_price
)
```

Use route identity (binding/connection plus full requested namespace/model),
executor and configuration revision; keep the resolved provider/account cohort
when known. A group's resolved provider may change without changing its name.
Record time range, distinct attempts/sessions, sample size, status coverage,
unknown counter coverage and pricing basis alongside the ratio. Preserve
PARTIAL numeric usage as partial evidence and UNKNOWN as unknown. Deduplicate
observations within attempts; never add Magpie rows and task observations for
the same work into one token denominator. Exclude zero-token failures from
cache-effectiveness samples. Require trusted counter completeness before using
normalized Magpie zero values as measured misses.

Apply the estimate within existing capability, quota, authorization, money and
reliability constraints. Sparse, stale or untrusted samples fall back to existing
cost inputs. In particular, 64 observations from **one** group task do not yet
justify a stable advantage over Trae across tasks. Cache reporting quality and
observed cache efficiency should remain separate inputs. Reuse existing pricing
and Owner credit-multiplier information; a 0.1 ledger cache weight is a budget
convention, not measured Trae/Raccoon billing. Avoid double-discounting a
credit-per-token estimate that already reflects cache usage.

## Reproduction and verification

Run this SQL through the read-only URI above to reproduce the frozen table and
its coverage, without treating NULLs as zero:

```sql
SELECT model_id, source_kind, status, COUNT(*) AS observation_rows,
       COUNT(DISTINCT task_id) AS tasks,
       SUM(input_units) AS input, SUM(cache_read_units) AS cache_read,
       SUM(cache_write_units) AS cache_write,
       SUM(input_units IS NULL) AS unknown_input_rows,
       SUM(cache_read_units IS NULL) AS unknown_cache_rows,
       MIN(created_at) AS first_observation, MAX(created_at) AS last_observation
FROM task_usage_observations
WHERE created_at >= '2026-11-24T00:00:00Z'
  AND created_at <= '2026-11-28T08:45:38Z'
GROUP BY model_id, source_kind, status;
```

For JSONL, parse each line, select exact `asked_model` equality, additionally
require `provider=trae-cn` for the known-provider Trae aggregate, deduplicate by
`request_id`, then group by `(session, account_id, status)`. Sum
`tokens.input/cache_read/cache_write`; retain NULL coverage separately. Convert
offset timestamps to UTC before comparing intervals. Request IDs here can be
exporter-generated `time:served_model` identities, not raw upstream IDs.

**[OBSERVED, tests]** On the base head, the focused command was:

```powershell
$taskTestTemp = Join-Path (Get-Location) ('.pytest_cache/route-cache-' + [guid]::NewGuid().ToString('N'))
$env:TEMP = $taskTestTemp
$env:TMP = $taskTestTemp
New-Item -ItemType Directory -Path $taskTestTemp | Out-Null
python -m pytest -q tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_usage_ledger.py tests/platform_v1/test_magpie_usage_ingest.py --basetemp (Join-Path $taskTestTemp 'cases') --tb=short
```

Result: **258 passed, 2 skipped**, zero model/provider calls. Installed-tool
integration opt-in was not enabled. The first invocation using the default
system temp location had 226 passes, one skip and 33 fixture-setup errors
(`WinError 5` accessing `C:/Users/wjc27/AppData/Local/Temp/pytest-of-wjc27`);
the worktree-local temp rerun above resolved them without code changes.

**[OBSERVED, change scope]** This commit changes documentation only. It delivers
no measured token saving, metering correction, production config activation,
or routing behavior change. `git diff --check` passed; the new, untracked file
also passed a direct trailing-whitespace and final-newline audit. Staging and
committing were blocked by sandbox write denial on
`F:/nerelan/.git/worktrees/codex-cache-efficiency/index.lock`, outside the writable
worktree. The document remains untracked and no commit was created.
No push, `gh`, production mutation, full platform suite, CI, independent review
or live provider experiment was performed. Raw upstream cache support/reporting,
CSV column completeness and outbound key forwarding remain the exact evidence
gaps. A future authorized capture should compare allowlisted raw usage counters
and key presence across the OpenCode-to-Magpie and Magpie-to-Trae boundaries
without recording credentials or prompt content.
