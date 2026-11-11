# Nerelan

Nerelan is a local-first, governed multi-Agent development platform. Give it a final goal; it persists a specification and plan, decomposes work into dependent tasks, coordinates reusable Agent runtimes, survives restarts, validates results, and can prepare an allowlisted Draft PR for review.

## Quick start

1. **Install the requirements below.** Get a local checkout of this repository. In PowerShell, change to its directory and install the Python and frontend packages:

   ```powershell
   python -m pip install -e .
   npm --prefix frontend ci
   ```

   Sign in to GitHub CLI with `gh auth login`. Use a repository where you have permission to push a task branch and open a PR.
2. **Start Nerelan.** Run `.\dev-up.ps1`. It opens the authenticated Nerelan client. For a desktop icon, run `.\create_desktop_shortcut.ps1` once, then double-click **Nerelan**. The desktop launcher can install missing frontend packages with `npm ci`; `dev-up.ps1` does not install packages. Startup does not call a model.
3. **Connect a model.** In settings, open **AI 资源与账号** (`/settings/resources`) and choose **新建连接**. Enter your provider, Base URL and authentication details, then save. Under **模型与路由** (`/settings/models`), choose **新建绑定** and save an enabled binding with executor `opencode`, that connection and a Model ID your provider supports. A connection alone is not a binding. Codex and Claude Code account sessions are managed by their own CLIs; sign in through the CLI first if using either tool.
4. **Give the first goal.** On the home page, enter a small request, such as “Fix a typo in README.md and run git diff --check.” Open **输入选项**, check **仓库** (`owner/name`), and select the matching **执行模式** and **模型绑定**. The repository must match the local source checkout. By default this is the launcher checkout; to work on another local checkout, start with `.\dev-up.ps1 -SourceDir C:\path\to\repo`. Click **创建并审阅目标**. This saves a draft; it does not start work.
5. **Review and run.** In **审批与继续**, click **生成计划**, inspect the plan, then click **批准当前计划**. Select the autonomy duration, check **确认启动当前计划**, and click **启动运行**. These are manual steps. The coordinator needs an active owner-confirmed window before it executes tasks.
6. **Review the result and open a Draft PR.** Follow the goal's progress and open its task details to inspect changed files, checks and evidence. For a validated task with changed files, click **发布草稿 PR**. This needs an active window for the same repository with `open_draft_pr` permission and working GitHub access. The task page then shows a **Draft PR #…** link to GitHub. Publication is a manual step on this path; execution finishing does not mean the change has been independently accepted or merged.
7. **Stop the local stack.** Run `.\dev-down.ps1` from the launcher checkout. It stops only the recorded process trees from that launch. Closing the client window alone does not shut down the stack. Task history remains available after a restart.

### Requirements

- Windows with PowerShell for these launcher scripts.
- Python 3.13+ and the repository's Python packages.
- Node.js 22.22.0+ with npm and the locked frontend packages.
- Git and GitHub CLI (`gh`); GitHub authentication and repository write access for Draft PR publication.
- One agent command-line tool: OpenCode, Codex CLI or Claude Code CLI. **The launcher currently requires OpenCode; support for starting with only Codex CLI or Claude Code CLI is in progress.** Keep `opencode` on `PATH` even when selecting another executor.
- At least one usable model connection and binding, or an authenticated agent CLI session with a matching binding.

### If something goes wrong

- **Missing command or package:** check that Python, Node.js, npm and OpenCode are on `PATH`, and run the install commands above. Desktop launch failures point to `%LOCALAPPDATA%\Nerelan\launcher.log`; direct launch failures are recorded in `.platform_v1_runtime/devup.fail.log`.
- **Client does not open or a port is occupied:** check `.platform_v1_runtime/combined-trusted-host.log` and `.platform_v1_runtime/frontend-vite.log`. The default ports are 4173, 8765 and 8766. The launcher refuses to stop unknown processes. Use `dev-down.ps1` for its own stack and resolve any other port conflict manually. Use the launcher to open the authenticated client.
- **No model binding or authentication failure:** check the saved connection in **AI 资源与账号** and the enabled executor/connection/Model ID binding in **模型与路由**. For Codex or Claude Code, check login in the corresponding CLI. Inspect the task's events for the actual failure.
- **Goal stays idle or publication is unavailable:** check **审批与继续**, the active window's repository, expiry and permissions, and task validation evidence. A saved draft is not a running task. **发布草稿 PR** appears only for a validated task with changes and a matching active publication window.

## For contributors

### Architecture

The repository and Python package retain the legacy `reverse-agent` / `reverse_agent` technical identifiers during the staged brand migration. Those identifiers are compatibility surfaces, not the current product name.

The product deliberately reuses mature components:

- GitHub Spec Kit-compatible `Goal → Specification → Plan → Tasks` artifacts;
- LangGraph topology and checkpoints for sequential or parallel teams;
- OpenCode as the repository executor and model-session adapter;
- OpenHands Agent Canvas patterns for the dark web workspace;
- GitHub as repository, checks, review, and publication truth.

Repository-owned code is the thin trust layer: authority snapshots, autonomy policies, durable claims, idempotency, evidence, secret confinement, exact-path publication, and deterministic acceptance.

### Local services and storage

On Windows, run `.\create_desktop_shortcut.ps1` once to put a **Nerelan** icon on the desktop. Double-clicking it starts the stack with no console window, shows a small "starting" window, and opens the Nerelan client. Double-clicking again reopens a closed client. On the first launch of a checkout without `frontend/node_modules`, the desktop launcher installs the locked frontend dependencies once (`npm ci`); a stale runtime record from an old launcher version with no live processes is set aside automatically. Launcher output goes to `%LOCALAPPDATA%\Nerelan\launcher.log`, and a failure shows a message box that points to it.

For compatibility, you can also double-click `launch_reverse_agent.bat`. The launcher starts loopback-only services. The frontend is served at `http://127.0.0.1:4173`; use the launcher's authenticated client to control tasks:

```text
Frontend       127.0.0.1:4173
Model Control  127.0.0.1:8765
Task API       127.0.0.1:8766
Coordinator    enabled, inert until an owner activates a bounded window
```

Task history lives in a host-owned store (`%LOCALAPPDATA%\Nerelan\platform-v1\tasks.sqlite3` on Windows, `$XDG_DATA_HOME/Nerelan/platform-v1/` elsewhere), so it no longer depends on which checkout or worktree started the launcher. On the first start after upgrading, `dev-up.ps1` names the previous `.platform_v1_runtime/tasks.sqlite3`; the host copies it once with SQLite's online backup while the new store is absent and never modifies the original. If that copy cannot be verified, startup fails instead of opening an empty history. `REVERSE_AGENT_TASK_DB_PATH` / `REVERSE_AGENT_TASK_DB_DIR` still select an explicit store and skip adoption.

### Product workflow

```text
natural-language goal
-> persistent specification and editable plan
-> owner approval and bounded autonomous window
-> dependency-aware multi-Agent execution
-> durable checkpoint / reconciliation / resume
-> deterministic validation and sanitized evidence
-> allowlisted task branch and Draft PR
-> governed exact-head review and acceptance
```

The browser never receives shell authority, direct filesystem access, raw provider credentials, or merge authority. The coordinator is off unless the trusted host enables it, and it remains inert without an active owner-confirmed window. Draft publication never force-pushes, rebases, marks ready, merges, tags, releases, or deploys.

### Platform APIs

The loopback Task API exposes:

- `/api/goals` for persistent goal planning, approval, amendment, and launch;
- `/api/windows` for owner-activated time, repository, capability, WIP, task, and retry budgets;
- `/api/platform/status` and `/api/capabilities` for product readiness;
- `/api/tasks` for execution truth, events, changed files, validation, and evidence;
- `/api/tasks/{id}/publish` for idempotent allowlisted Draft-PR publication.

Provider-free tests cover the entire control path. Real model/API probes are separate R3 operations and are never part of ordinary startup or CI.

### Authority model

Path A / Path B are legacy governance flows; see [legacy governance v1](docs/agents/legacy-governance-v1.md) for their authority snapshots, Decisions, Command Plans and authorization states.

An autonomous window is execution policy, not repository-development authority. It cannot expand its own repositories, capabilities, duration, budgets, or publication boundary.

### Verification

```powershell
python -m pytest -q
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run build
python -m reverse_agent.freshness --registry governance/freshness-registry.json --repository-root .
git diff --check
```

Renovate proposes dependency updates without automerge. The freshness registry records the owner, upstream source, pinned/compatible version, evidence path, and review age for mature platform components.

### Reference documents

- [AGENTS.md](AGENTS.md) — repository authority, risk, publication, and stop rules
- [active roadmap](docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md)
- [source-of-truth matrix](docs/architecture/SOURCE_OF_TRUTH_MATRIX.md)
- [R1 Work Item template](.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml)
- [legacy `run-closeout` reference](docs/run_closeout.md) — historical compatibility only
