# OpenCode Real Executor Proof — Issue #131 v2

Date: 2026-08-08

This is the v2 evidence report. The historical v1 reports
(`opencode-real-executor-2026-08-08.md` / `.json`) are left immutable.

## 1. Repository authority

- Repository: `dddd2024/reverse-agent`
- Local path: `F:/reverse-agent`
- Branch: `owner/issue131-opencode-real-executor-v1`
- Current main / base SHA (`origin/main`): `e4e23028c6c78c4ab9a8e032677e71370ace7627`
- Starting head (v1 final head): `29d44637ed7c33db390d5cf1bf64ae2f77609c0b`
- Merge-base(`origin/main`, branch): `e4e23028c6c78c4ab9a8e032677e71370ace7627`

## 2. Active v2 Decision

- decision_id: `decision_20260808_issue131_opencode_real_executor_v2`
- round_id: `round_20260808_issue131_opencode_real_executor_v2`
- follows_last_decision_id: `decision_20260808_issue131_opencode_real_executor_v1`
- previous_audit_outcome: `ISSUE131_V1_BLOCKED_CLI_NOT_FOUND_WITH_PACKAGE_NAME_FALSE_NEGATIVE`
- risk_tier: `R3`
- activation_base_sha: `e4e23028c6c78c4ab9a8e032677e71370ace7627`
- required_branch: `owner/issue131-opencode-real-executor-v1`
- starting_head: `29d44637ed7c33db390d5cf1bf64ae2f77609c0b`
- Owner-created v2 Decision commit: `88503d6817e71025164292d31b171b68a5dc7913`
- HEAD at report start (after gates commit): `aca47436d243503a95078167db8e16e47698b566`

Confirmed authorized:
- `package_installation_allowed = true`, allowed package `npm:opencode-ai@latest`.
- `opencode_invocation_allowed = true`.

Confirmed forbidden (all remain forbidden):
- Codex invocation, OpenHands invocation, provider configuration mutation,
  credential value access, product code mutation, PR creation, Ready, merge,
  main push, release/deploy, multi-agent, force push, rebase.

## 3. Gate generation (before installation)

Generated in order:

1. `startup-snapshot` -> `startup-snapshot: PASSED`
2. `transition-command-plan` -> `transition-command-plan: PASSED`, commands: 20
3. `transition-lint` -> `transition-lint: PASSED` (all checks PASS:
   transition_contract, decision_approved, active_skills, command_plan_identity,
   command_plan_provenance, command_plan_contract errors=[])
4. `transition-preflight --mode pre` -> `PRE_EXECUTION_AUTHORIZED`

Preflight:
- gate_status: `PRE_EXECUTION_AUTHORIZED`
- decision_id: `decision_20260808_issue131_opencode_real_executor_v2`
- round_id: `round_20260808_issue131_opencode_real_executor_v2`
- branch: `owner/issue131-opencode-real-executor-v1`
- base / merge_base: `e4e23028c6c78c4ab9a8e032677e71370ace7627`
- decision_commit: `88503d6817e71025164292d31b171b68a5dc7913`
- blocking_reasons: `[]`
- all capability / path / network / risk-floor enforcement: PASS

Gate commit: `aca47436d243503a95078167db8e16e47698b566`
Commit message: `gates: generate Issue131 OpenCode executor proof v2`

## 4. Official package metadata

Command (authorized by Decision):

```
npm view opencode-ai name version dist-tags.latest
```

Result (exit 0):

```
name = 'opencode-ai'
version = '1.18.15'
dist-tags.latest = '1.18.15'
```

- official npm package name: `opencode-ai`
- observed npm package version: `1.18.15`

Note: v1 mistakenly queried `npm view opencode`, which is NOT the official
package name. This v2 query uses the exact authorized name `opencode-ai`.

## 5. CLI installation and verification

Install command (authorized, only this package):

```
npm install -g opencode-ai@latest
```

Result: success (`added 3 packages`).

Post-install verification (all exit 0):
- `where.exe opencode` -> `C:\Users\wjc27\AppData\Roaming\npm\opencode`
  and `C:\Users\wjc27\AppData\Roaming\npm\opencode.cmd`
- `opencode --version` -> `1.18.15`
- `opencode run --help` -> succeeded

- OpenCode executable path: `C:\Users\wjc27\AppData\Roaming\npm\opencode`
- OpenCode CLI version: `1.18.15`

Locally observed `opencode run` flags confirmed present:
- `--model` / `-m` : present (provider/model format)
- `--dir` : present
- `--format` : present (choices: `default`, `json`)
- `--agent` : present
- `--auto` : present (auto-approve permissions)
- also present: `--print-logs`, `--log-level`, `--command`, `--continue`,
  `--session`, `--fork`, `--share`, `--file`, `--title`, `--attach`,
  `--password`, `--username`, `--port`, `--variant`, `--thinking`, `--interactive`

## 6. Provider / model selection (credential-safe metadata only)

`opencode models` output (identifiers only; no auth/config/env values printed):

```
opencode/big-pickle
opencode/deepseek-v4-flash-free
opencode/laguna-s-2.1-free
opencode/ling-3.0-tiny-free
opencode/longcat-2.0-free
opencode/mimo-v2.5-free
opencode/nemotron-3-ultra-free
opencode/north-mini-code-free
sensetime/deepseek-v4-flash
sensetime/sensenova-6.7-flash-lite
sensetime/sensenova-u1-fast
```

Qualifying already-visible non-OpenAI SenseNova-family model exists. Selected
the same SenseNova family currently driving the development environment:

- provider ID: `sensetime`
- model ID: `sensenova-6.7-flash-lite`
- non_openai: true

No provider configuration was read, printed, copied, or mutated. No auth files,
API keys, tokens, cookies, headers, or environment values were accessed.

## 7. Fixture

Fixture directory (outside repository): `F:/reverse-agent-labs/issue131-opencode-executor`

Prepared contents:
- `input.txt` with exact content `alpha`

This is the only directory that was recreated/reset. The reverse-agent source
tree was NOT used as the Agent working directory.

## 8. Real executor run (separate `opencode run` child process)

Command executed:

```
opencode run --model sensetime/sensenova-6.7-flash-lite \
  --dir F:\reverse-agent-labs\issue131-opencode-executor \
  --format json --auto --print-logs <task>
```

Task text:
```
Read input.txt. Run one harmless shell command that prints the current working
directory. Create output.txt containing exactly: alpha-ok. Verify output.txt by
reading it back or by another deterministic local command. Only report PASS after
verification succeeds. Do not access files outside the current fixture directory.
```

This is a separately spawned `opencode run` CLI child process (session
`ses_020e7866bffeHHm6hBiVP6DAJo`), NOT the outer development Agent session.

Process exit status: `0`

## 9. Sanitized runtime evidence summary

All evidence below is taken from the child process's own JSON events / logs.
No secret values are included.

- OpenCode CLI child process really started: true
  - `run=a16324ed`, `creating instance`, directory=fixture
  - LLM runtime selected: `llm.runtime=ai-sdk`, `llm.provider=sensetime`,
    `llm.model=sensenova-6.7-flash-lite`
- Selected provider/model non-OpenAI SenseNova: true
  - providerID=`sensetime`, modelID=`sensenova-6.7-flash-lite` (repeated in every
    `stream` event)
- `input.txt` was actually read: true
  - `tool_use` event, tool=`read`, filePath=`.../input.txt`,
    output content = `1: alpha`
- A real shell/tool action occurred: true
  - `tool_use` event, tool=`bash`, shell=
    `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.EXE`
- Working-directory command actually ran: true
  - command = `Get-Location | Select-Object -ExpandProperty Path`
  - workdir = `F:\reverse-agent-labs\issue131-opencode-executor`
  - output = `F:\reverse-agent-labs\issue131-opencode-executor`, exit=0
- `output.txt` was actually created: true
  - `tool_use` event, tool=`write`, filePath=`.../output.txt`,
    input.content = `alpha-ok`, output = `Wrote file successfully.`
- Verification action actually occurred: true
  - `tool_use` event, tool=`read`, filePath=`.../output.txt`,
    output content = `1: alpha-ok`
- OpenCode process completed successfully: true
  - `exiting loop`, `disposing instance`; exit status = 0
- JSON/action events provide evidence of real execution: true
  - JSON `step_start` / `tool_use` / `step_finish` events present for all four
    steps (read input, bash cwd, write output, read output verify)

## 10. Independent deterministic verification (post-process)

Independently verified after the child process exited, using Python/PowerShell
filesystem reads (NOT Agent prose):

- `output.txt` exists: true
- UTF-8 byte sequence: `97,108,112,104,97,45,111,107`
  (which decodes to the literal string `alpha-ok`, no BOM, no trailing newline)
- exact_match(`alpha-ok`): true

If output had contained extra prose, quotes, markdown, or any other content,
this would have been classified `output_exact_match = false`.

## 11. Safety / non-exposure

- credential_exposure: FALSE
  - No auth files read, no env values printed, no API keys / tokens / cookies /
    Authorization headers exposed. Only provider/model identifiers observed via
    the credential-safe `opencode models` command.
- repository_source_mutation: FALSE
  - The fixture directory is outside the repository. The reverse-agent source
    tree was not used as the Agent working directory and no product code was
    modified by the child process or by this verification round.

## 12. Runtime outcome

- fixture executed: true
- input_read: true
- tool_used: bash (PowerShell `Get-Location | Select-Object -ExpandProperty Path`)
- cwd_command_executed: true
- output_created: true
- output_exact_match: true
- verification_executed: true
- process_exit_status: 0

Therefore:

- REAL_SINGLE_AGENT_EXECUTOR_PATH_ESTABLISHED = TRUE
- SELECTED_EXECUTOR_PATH = OPENCODE_RUN
- INTEGRATION_SURFACE_RECOMMENDATION = OPENCODE_RUN_CHILD_PROCESS

This proves the first real quota-independent single-Agent executor path for
Issue #127. It does NOT mean #126 is complete, that Codex works, that native
MultiAgent works, or that a cross-provider architecture is decided.

Recommended #127 next action: use the separately spawned `opencode run` CLI
child process (with `--model`, `--dir`, `--format json`) as the real
quota-independent executor surface, bound to an already-configured
non-OpenAI provider/model, behind the existing reverse-agent governance / gate
layer. Owner to decide whether to keep this as the baseline executor or to add
formal integration scaffolding in a later Decision.

## 13. Repository path audit

`git diff --name-only 29d44637ed7c33db390d5cf1bf64ae2f77609c0b..HEAD` (v2 delta
from v1 final head):

```
project_state/decision_packet.md
project_state/gates/bootstrap_state.json
project_state/gates/command_plan.json
project_state/gates/startup_snapshot.json
project_state/gates/transition_command_plan_preview.json
project_state/gates/transition_preflight_result.json
```

All within allowed v2 repository paths. `project_state/decision_packet.md` is the
Owner-created Decision change. The five gate files are generated artifacts.
No product source appears.

`git diff --name-only e4e23028c6c78c4ab9a8e032677e71370ace7627..HEAD`
(full delta from activation base):

```
docs/research/opencode-real-executor-2026-08-08.json
docs/research/opencode-real-executor-2026-08-08.md
project_state/decision_packet.md
project_state/gates/bootstrap_state.json
project_state/gates/command_plan.json
project_state/gates/startup_snapshot.json
project_state/gates/transition_command_plan_preview.json
project_state/gates/transition_preflight_result.json
```

The two `opencode-real-executor-2026-08-08.*` files are historical v1
governance/research paths already present in this branch (they were NOT modified
in v2). No `reverse_agent/**`, `frontend/**`, `tests/**`, `.github/**`,
dependency, provider config, credential, or `project_state/mainline_merge_intents/**`
path appears.

- PRODUCT_DELTA = ZERO

`git diff --check e4e23028c6c78c4ab9a8e032677e71370ace7627..HEAD`: exit 0.

## 14. Local state at report time

- Local HEAD (after gate commit, before report commit):
  `aca47436d243503a95078167db8e16e47698b566`
- Pre-existing untracked artifacts (protected, untouched):
  `.frontend_stage/`, `.platform_v1_runtime/`, `task_workspaces/`
- Development Agent model/session used for this verification round:
  `sensenova-6.7-flash-lite` (this outer session is NOT the executor under test;
  the executor evidence comes from the separate `opencode run` child process above).

## 15. Result

All runtime evidence passes. Terminal outcome:

```
ISSUE131_V2_OPENCODE_REAL_EXECUTOR_READY_FOR_OWNER_AUDIT
```
