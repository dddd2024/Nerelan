# OpenHands Reuse Map

This document records the exact OpenHands 1.8.0 source-to-target mappings for
the reverse-agent Frontend V1 adaptation on branch
`agent/frontend-v1-openhands-ui`.

- **Upstream repository:** OpenHands/OpenHands
- **Upstream tag:** 1.8.0
- **Upstream commit:** `c7a765d900df294cbbf0f405ae26c9cbbd0fcc29`
- **Upstream license:** MIT
- **Clone path:** `F:/reverse-agent-upstreams/OpenHands-1.8.0`

reverse-agent does **not** fork OpenHands, does not copy its frontend or Agent
Loop, and does not build a second control platform. The reuse is structural
adaptation only — OpenHands runtime, sandbox, backend API, model, and
credential code is not imported.

## Source-to-target reuse map (exact upstream paths)

| OpenHands 1.8.0 source path | Upstream component | reverse-agent target path | Reuse type | Modifications | License |
|---|---|---|---|---|---|
| `src/routes/root-layout.tsx` | `MainApp()` | `frontend/src/components/app-shell.tsx` | structurally-ported | Dark `h-screen flex flex-col md:flex-row bg-base` shell; OpenHands logo/backend/status bars → reverse-agent identity; `Outlet` → workspace children; omitted telemetry/backend onboarding/env-switch lazy components (fixture-only) | MIT |
| `src/components/features/sidebar/sidebar.tsx` | `Sidebar()` (desktop rail + mobile drawer) | `frontend/src/components/sidebar.tsx` + `frontend/src/components/app-shell.tsx` (mobile drawer) | structurally-ported | OpenHands 1.8.0 desktop sidebar: `hidden md:flex`, 60px collapsed / 300px expanded with collapse toggle; mobile: hamburger trigger (`md:hidden`) + fixed left drawer (`w-[min(300px,85vw)]`, `md:hidden`) + backdrop + overlay. Structurally ported to reverse-agent with fixture-only nav items; logo, nav links, new-task button, task-list toggle preserved. | MIT |
| `src/components/features/sidebar/sidebar-rail-body.tsx` | Logo + collapse toggle + nav + conversation list | `frontend/src/components/sidebar.tsx` (rail body) | structurally-ported | `OpenHandsLogoButton` → RA text logo button; `SidebarNavLink` → compact `NavLink` with `sidebar-nav-{label}` test ID; `Plus` icon → New Task; conversation-list slot → task-list toggle; BackendSelector at bottom → omitted | MIT |
| `src/components/features/sidebar/sidebar-layout.ts` | Layout class constants | `frontend/src/index.css` (`@theme inline`) | structurally-ported | `sidebarNavListClassName`, `sidebarNavRowClassName`, `SIDEBAR_ICON_BUTTON_CLASS` → `@theme` tokens (`--ra-sidebar-nav-*`) | MIT |
| `src/components/features/conversation-panel/conversation-panel.tsx` | `ConversationPanel()` (overlay panel) | `frontend/src/components/conversation-panel.tsx` | structurally-ported | Paginated conversations → fixture task list; OpenHands card actions (delete/stop/pin) → disabled read-only; dark `bg-black/80` overlay with `absolute h-full w-full` | MIT |
| `src/components/features/conversation-panel/conversation-card/conversation-card.tsx` | `ConversationCard` | `frontend/src/components/conversation-panel.tsx` (`ConversationCard`) + `frontend/src/components/task-card.tsx` | structurally-ported | Title → `#issueNumber — task.title`; OpenHands model badge → reverse-agent permission-profile badge; repository → branch; sandbox status → reverse-agent RunState dot | MIT |
| `src/components/features/conversation-panel/conversation-card/conversation-card-header.tsx` | Status dot + title | `frontend/src/components/task-card.tsx` (`StatusDot`) | structurally-ported | `SandboxStatusIndicator` color map → `runStateStyle()` reverse-agent color map; same `w-1.5 h-1.5 rounded-full` dot | MIT |
| `src/components/features/conversation-panel/conversation-card/conversation-card-footer.tsx` | Repo link + date | `frontend/src/components/task-card.tsx` | structurally-ported | `ConversationRepoLink` → branch `span`; `formatTimeDelta` → ISO date text; compact layout preserved | MIT |
| `src/components/features/conversation-panel/conversation-card/conversation-card-skeleton.tsx` | `ConversationCardSkeleton` | `frontend/src/components/conversation-panel.tsx` (`ConversationCardSkeleton`) | structurally-ported | Same `skeleton-stagger` + `skeleton` class pattern from `tailwind.css`; fixture-only no `compact` variant | MIT |
| `src/components/features/home/home-header/home-header.tsx` | `HomeHeader` (title + GuideMessage) | `frontend/src/components/task-inbox.tsx` (Section header) | structurally-ported | GuideMessage → Section header with icon + count; same text-size and spacing pattern | MIT |
| `src/routes/home.tsx` | `HomeScreen` (landing page) | `frontend/src/routes/home.tsx` + `frontend/src/components/task-inbox.tsx` | structurally-ported | `RecentConversations` section → reverse-agent category sections (Needs Owner Attention, Running, Recent); `NewConversationCard` → NewTaskComposer; redirect to `/tasks` for fixture-only mode | MIT |
| `src/components/features/home/new-conversation/new-conversation.tsx` | New conversation card | `frontend/src/components/new-task-composer.tsx` | structurally-ported | OpenHands "Start from scratch" card → reverse-agent New Task input; same card layout with icon + title + description | MIT |
| `src/components/features/conversation-panel/new-conversation-button.tsx` | New conversation button (sidebar) | `frontend/src/components/sidebar.tsx` (New Task button) | structurally-ported | `Plus` icon + `aria-label` + tooltip → same pattern with "新建任务" label | MIT |
| `src/components/features/chat/chat-input-container.tsx` | Chat input container (composer dock) | `frontend/src/components/new-task-composer.tsx` | structurally-ported | OpenHands input + model picker + send button → reverse-agent input + PermissionSelector + send; same `relative flex items-end` container pattern | MIT |
| `src/components/features/chat/interactive-chat-box.tsx` | Interactive chat box | `frontend/src/components/new-task-composer.tsx` | structurally-ported | Textarea + action buttons → task input + permission selector; `ChatSendButton` → circular send button; `ChatStopButton` → cancel button; same `flex gap-2` row layout | MIT |
| `src/components/features/chat/custom-chat-input.tsx` | Custom chat input (model selector) | `frontend/src/components/permission-selector.tsx` | structurally-ported | `ChatInputModel` dropdown → PermissionSelector dropdown; same `aria-haspopup="listbox"` + `aria-expanded` pattern; ChatGPT-style icon + title + description layout | MIT |
| `src/components/features/chat/chat-input-model.tsx` | Model profile picker | `frontend/src/components/permission-selector.tsx` | structurally-ported | OpenHands LLM profile dropdown → reverse-agent permission-profile dropdown; same option-row with icon + label + description + checkmark | MIT |
| `src/components/features/chat/chat-send-button.tsx` | Send button | `frontend/src/components/new-task-composer.tsx` | structurally-ported | Circular send button with SVG icon; same `h-8 w-8 rounded-full` pattern | MIT |
| `src/components/features/chat/generic-event-message.tsx` | Generic event message | `frontend/src/components/activity-stream.tsx` + `frontend/src/components/timeline.tsx` | structurally-ported | Event message with avatar + content + timestamp; same `flex gap-3` layout; status color variants (green/yellow/red/grey) mapped to reverse-agent RunState | MIT |
| `src/components/features/chat/model-messages.tsx` | Model message rendering | `frontend/src/components/activity-stream.tsx` | structurally-ported | Message bubble with avatar + text; same `prose` markdown-body styling; `ChatStatusIndicator` → reverse-agent state dot | MIT |
| `src/components/features/conversation/conversation-main/conversation-main.tsx` | ConversationMain (workspace split) | `frontend/src/components/task-detail.tsx` | structurally-ported | `useResizablePanels` horizontal split → manual mouse-drag with `leftWidth` state; left = ActivityStream, right = tab panel; `px-3 md:p-0` padding preserved | MIT |
| `src/routes/conversation.tsx` | Conversation route wrapper | `frontend/src/components/task-detail.tsx` | structurally-ported | `p-3 md:p-0 flex flex-col h-full gap-3` → same layout; header + workspace + composer | MIT |
| `src/components/features/conversation/conversation-name-with-status.tsx` | Name + status dot + badges | `frontend/src/components/task-detail.tsx` (header) | structurally-ported | Conversation name → `#issueNumber — task.title`; LLM model badge → permission-profile badge; status dot + badges row; same `flex items-center gap-3` pattern | MIT |
| `src/components/features/conversation/conversation-tabs/conversation-tabs.tsx` | Tab navigation | `frontend/src/components/task-detail.tsx` (rightTab nav) | structurally-ported | Conversation tabs (Messages, Artifacts, Tool Calls) → right-panel tabs (Changed Files, Evidence, Authority); same horizontal icon tab strip with `role="tablist"` | MIT |
| `src/components/features/conversation-panel/compact-conversation-row.tsx` | Compact row | `frontend/src/components/task-card.tsx` | structurally-ported | `skeleton-round` + title + secondary text → same compact structure; `hover:bg-[#454545]` hover pattern preserved | MIT |
| `src/components/features/conversation-panel/conversation-status-dot.tsx` | Status dot | `frontend/src/components/task-card.tsx` | structurally-ported | `status` → `runStateStyle().dot`; same `w-1.5 h-1.5 rounded-full` pattern | MIT |
| `src/components/features/conversation-panel/conversation-panel-wrapper.tsx` | Panel wrapper (portal) | `frontend/src/components/conversation-panel.tsx` | structurally-ported | `absolute h-full w-full` overlay panel with portal-style positioning; task list replaces conversation list | MIT |
| `src/components/features/conversation-panel/start-task-card/start-task-card.tsx` | Start task card | `frontend/src/components/new-task-composer.tsx` | structurally-ported | Start-task card → New Task composer; same card-with-icon layout | MIT |
| `src/components/features/diff-viewer/file-diff-viewer.tsx` | File diff viewer | `frontend/src/components/diff-viewer.tsx` | structurally-ported | Hunk headers (`@@` lines), green additions (`#014b01AA`), red deletions (`#750000AA`), `font-mono text-xs`; simplified to plain `<pre>` without Monaco | MIT |
| `src/routes/changes-tab.tsx` | Changes tab | `frontend/src/components/changes-panel.tsx` | structurally-ported | File list with status icon + path + ± counts; `FileDiffViewer` inline expand; same `border-b` card list pattern | MIT |
| `src/components/features/diff-viewer/empty-changes-message.tsx` | Empty changes | `frontend/src/components/empty-state.tsx` | structurally-ported | Icon + centered text "No changes yet"; same `flex flex-col items-center` pattern | MIT |
| `src/components/features/diff-viewer/loading-spinner.tsx` | Loading spinner | `frontend/src/components/loading-state.tsx` | structurally-ported | Spinner + label; same `role="status"` + `aria-live="polite"` pattern | MIT |
| `src/components/features/conversation-panel/hooks-empty-state.tsx` | Empty state | `frontend/src/components/empty-state.tsx` | structurally-ported | `Clock` icon + muted text; same centered layout | MIT |
| `src/components/shared/buttons/openhands-logo-button.tsx` | Logo button | `frontend/src/components/sidebar.tsx` | structurally-ported | OpenHands logo SVG → reverse-agent "RA" text; same button pattern | MIT |
| `src/components/shared/buttons/styled-tooltip.tsx` | Tooltip | `frontend/src/components/sidebar.tsx` (title attrs) | structurally-ported | `hover:bg-[var(--oh-surface-raised)]` → `hover:bg-ra-tertiary`; tooltip pattern preserved via `title` | MIT |
| `src/components/shared/navigation-link.tsx` | NavLink | `frontend/src/components/sidebar.tsx` | structurally-ported | OpenHands `NavigationLink` → React Router `NavLink`; same active/inactive styling | MIT |
| `src/index.css` | Global styles + tokens | `frontend/src/index.css` | structurally-ported | Cool-grey palette (`#0B0E14` → `--ra-base`, `#21252F` → `--ra-sidebar`, etc.); `@import` Google Fonts preserved; skeleton animation + custom scrollbar + markdown-body preserved | MIT |
| `src/themes/color-themes.ts` | Color theme definitions | `frontend/src/index.css` (`@theme inline`) | structurally-ported | `--cool-grey-*` → `--ra-*` tokens; `--oh-accent` → `--ra-accent`; green/red status → `--ra-status-success`/`--ra-status-error` | MIT |
| `tailwind.config.js` | Tailwind config | `frontend/src/index.css` (`@theme inline` + `@layer base`) | structurally-ported | Color palette + typography plugin → `@theme` + `@layer` in CSS; dark mode class preserved | MIT |

## Not reused (concrete incompatibilities)

| OpenHands source | Reason not reused |
|---|---|
| `src/api/**` | Backend API layer — reverse-agent uses fixture-only data, no API calls from browser |
| `src/hooks/query/**` | React Query data fetching hooks — replaced with fixture hooks (`useTasks`, `useTask`) |
| `src/stores/**` | Zustand state stores — replaced with local React state |
| `src/context/**` | Context providers for backend config — not applicable in fixture-only mode |
| `src/i18n/**` | i18n system — reverse-agent uses inline Chinese text |
| `src/services/**` | Telemetry services — not applicable in fixture-only mode |
| `src/routes/launch.tsx`, `onboarding/**` | Launch/onboarding — reverse-agent goes straight to tasks |
| `src/components/features/terminal/**` | Terminal component — not needed (no shell execution from browser) |
| `src/components/features/browser/**` | Browser tool — not needed (no real browser control) |
| `enterprise/**` | Explicitly forbidden by Issue #117 |
| `src/components/features/backends/**` | Backend management — fixture-only, no real backends |
| `src/components/features/onboarding/**` | Onboarding flow — reverse-agent skips onboarding |
| `src/components/features/alerts/**` | Alert banner — replaced by `ErrorState` pattern |
| `src/components/features/command-menu/**` | Command menu — not needed for fixture prototype |
| `src/components/features/skills/**` | Skills marketplace — not needed |
| `src/components/features/mcp-page/**` | MCP settings — out of scope for this Work Item |

## Invariants preserved from the repository governance model

- `merge_pr` and `push_main` are independent toggles (no implicit enabling)
- Deployment is not implied by network write access
- `secrets` must not be `raw_values`
- `autonomousWindow.expiresAt` must be a valid future ISO date when enabled
- All budgets must be positive integers

## What is NOT reused

- OpenHands Agent Loop / runtime executor
- OpenHands sandbox / runtime / database
- OpenHands backend API code (`src/api/**`)
- OpenHands enterprise source (`enterprise/**`)
- Real credentials, model APIs, or production mutation APIs
