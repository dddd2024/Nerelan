# Native Agent vs Nerelan Controlled A/B Benchmark & Bottleneck Audit (2026-11-25, #1267)

> Scope: empirical baseline measurement on `dddd2024/Nerelan` under #1267 (`cost_quality_benchmark.py`). No general savings claim beyond measured tasks.

## 1. Controlled A/B Results

| Task & Frozen Base | Arm | Outcome & Independent Checks | Wall / Active Time | Attempts / Calls | Usage / Cost (`cli_reported` vs `observed`) |
|---|---|---|---|---:|---|
| **#1501** (`a7468696`, `test_owner_window.py`) | **Native Sonnet (full tools)** | Pass (`36+,1-`, `134 passed in 16.77s`, diff clean) | `56.65s` (+23.24s verify) | `1` (18 tools) | `in=20, cw=34,962, cr=274,263, out=5,107` / `$0.2184` |
| **#1501** (`a7468696`, **matched no-Bash**) | **Native Sonnet (`--restricted`, no Bash)** | Pass (`36+,1-`, `135 passed in 16.73s`, diff clean) | `56.05s` (+19.79s verify) | `1` (19 tools) | `in=26, cw=25,476, cr=238,536, out=5,103` / `$0.1768` |
| **#1501** (observed Nerelan `agent_team`) | **Nerelan Platform** | `COMPLETED` (`ab5a100b86b3`) | `648.0s` (`11.6x`) / `439.0s` active | `3` tasks | `in=75,161, out=1,753, cr=1,079,424` (`deepseek` unknown; `$0` settled) |
| **#1504** (`bbc20139`, 4 `pytest` targets) | **Native Sonnet (full tools)** | Confirmed base already satisfies Part 1 (**78 passed in 3.83s**, 0 edits; frontend not run) | `28.98s` (+7.99s verify) | `1` (6 tools) | `in=12, cw=21,758, cr=128,258, out=1,464` / `$0.1145` |
| **#1504** (observed Nerelan `agent_team`) | **Nerelan Platform** | Still `RUNNING` (`claude-opus` hit trailing-whitespace hygiene after 91s) | `19,774s (~5.5h)` / `3,446s` active | `11` attempts | `in=563,072, out=41,835, cr=5,917,304, cw=105,500` + `$1.0944` |

## 2. Three-Bucket Cost Separation (Latest 500 Magpie Priced Requests = $14.2279)

- **Supervision & one-time development (`antigravity`)**: 152 calls, **$13.5261 (`95.1%`)** — reflects external diagnosis, patch iterations, and review orchestration, not steady-state single-task execution cost.
- **Steady-state platform execution**: `claude` Magpie **$0.6598 (`4.6%`)** + `opencode` **$0.0418 (`0.3%`)** (plus unpriced/subscription CLI turns such as `$0.18`–`$1.09`/turn).
- **Probes (`Python-urllib`)**: 226 calls, **$0.0002**.

## 3. Structural Findings & Wiring Audit

1. **Native Agent confinement asymmetry**:
   - `CodexExecutor` already preserves Codex's built-in `Bash`/test loop via `--sandbox workspace-write -c windows.sandbox="elevated"`.
   - `ClaudeCodeExecutor` strips `Bash` (`--restricted --tools Read,Glob,Grep,Edit,Write`) because Claude CLI on Windows lacks an OS-level folder sandbox; yet Arm A2 proves that even without `Bash`, mature single-shot execution completes cleanly in `56s / \$0.18` once upstream stalls, premature stream-byte cutoffs, and stale quota lockouts are removed.
2. **Existing modules implemented but under-wired**:
   - **Single-agent fast path (`orchestration_selector.py`)**: `goal_service._resolve_orchestration_mode()` stays hardcoded on `"sequential_team"` unless `measured_*` break-even data exists (`multi_account` flag on).
   - **Context recovery (`context_recovery.py`)**: `281` `Durable context rebuilt` events hit the `16 KiB` compaction ceiling `128` times (`45.6%`), yet `task_evidence` has **`0` `ContextSummary` and `0` `ContextHandoff`** rows because automatic retry paths never trigger summarization.
   - **Quota calibration (`platform_quota_calibrations`)**: Only 1 historical entry (`c38efd6a74a2`); Claude (`dd0832f93b53`) remained uncalibrated (`p80=30%` / `weekly p80=6%`) because stale readings past `AGED_MAX_SECONDS=3600` locked admissions until the 5-day weekly reset (`2026-11-30T04:59:00Z`) instead of returning `until=None` for next-tick re-evaluation.
3. **Cumulative stream limit on O(1) parsers**:
   - Native `--output-format stream-json --verbose` replays full tool results inside `user` lines (~`20 KiB/call` on `#1501`, ~`56 KiB/call` on `#1552`, `84%–85%` of total bytes). Because `ClaudeStreamJson` and `CodexJsonl` drop parsed lines every `\n` while bounding memory via `max_frame_bytes` and `max_events`, cumulative `max_stream_bytes` cutoffs killed valid multi-step coding turns. Bounding `max_progress_bytes` / `max_discarded_bytes` (uncounted noise/blank lines) and `max_events` preserves memory safety without truncating normal tool activity.
