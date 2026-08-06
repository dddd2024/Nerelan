# Visual Acceptance Evidence — Frontend V1 OpenHands Adaptation

This document records structural comparison between OpenHands 1.8.0 UI
components and the reverse-agent Frontend V1 adaptation, plus committed
target screenshots at the final exact HEAD.

## Final verification HEAD

```text
HEAD: 267d78f865d56fba1a54e3cd604e4066344c2d83
OpenHands upstream commit: c7a765d900df294cbbf0f405ae26c9cbbd0fcc29 (tag 1.8.0)
```

## Methodology

### Source (OpenHands 1.8.0)

The OpenHands upstream was cloned at tag `1.8.0`, commit
`c7a765d900df294cbbf0f405ae26c9cbbd0fcc29`, into
`F:/reverse-agent-upstreams/OpenHands-1.8.0`. The repository at that exact
commit was inspected for source paths and UI structure.

**Reference screenshots:** The OpenHands 1.8.0 repository contains no UI
screenshots (only favicons and an Electron icon). Capturing reference
screenshots requires running the OpenHands backend and/or frontend
development server, which is outside the authorized scope of this Work Item
(no live OpenHands runtime, Docker, or provider is permitted). No reference
screenshot files were captured.

### Target (reverse-agent)

Target screenshots were captured from `npm run dev` loopback
(`http://localhost:5173`) with deterministic fixtures at a HEAD
immediately preceding the fix-forward commits. The two fix-forward commits
changed only test assertions and ARIA role strings (`separator` →
`slider`), not visual rendering. No visual-regression change occurred
between the captured-screenshot HEAD and the final verification HEAD.

Screenshot viewport:
- Desktop: 1440×900
- Mobile: 390×844

### Side-by-side comparisons

The following comparisons are structural analysis, **not captured side-by-side
screenshots**. They map each OpenHands 1.8.0 source component to its
reverse-agent target adaptation and describe the corresponding visual
evidence files.

## Side-by-side comparisons

### 1. Root Layout — Sidebar + Workspace (OpenHands `root-layout.tsx`)

| OpenHands 1.8.0 | reverse-agent Frontend V1 | Notes |
|---|---|---|
| 60px collapsed / 300px expanded desktop sidebar (`hidden md:flex`); mobile: hamburger trigger + fixed left drawer `w-[min(300px,85vw)]` + backdrop + overlay (`md:hidden`) | `src/components/app-shell.tsx` + `src/components/sidebar.tsx` — same 60/300 collapsed/expanded desktop sidebar; same hamburger + fixed-drawer + backdrop mobile pattern | Sidebar is `hidden md:flex` on desktop, `md:hidden` on mobile; drawer `role="dialog"` with `aria-modal` and focus trap |
| Logo · New Conversation · Conversation Panel toggle · Nav links · User avatar | Logo (RA text) · New Task button · Task List toggle · Nav links (home/tasks/settings) | No user avatar (no auth in fixture mode) |
| Main workspace area | `src/components/app-shell.tsx` workspace outlet + `NewTaskComposer` dock | Same padding and gap structure (`p-3 md:p-0`, `gap-3`) |

### 2. Home Screen — Task Inbox (OpenHands `home.tsx` + `recent-conversations`)

| OpenHands 1.8.0 | reverse-agent Frontend V1 | Notes |
|---|---|---|
| RecentConversations section with h3 header | `src/components/task-inbox.tsx` — Section components with header (icon + title + count) | Categories: "需要 Owner 关注", "运行中", "最近任务" replacing conversation status groups |
| ConversationCard: status dot + title + model + date | `src/components/task-card.tsx` — same layout: status dot + `#issueNumber — title` | Permission profile badge replaces "model" field |
| Skeleton cards on loading | Inline `SkeletonCard` component (skeleton animation from OpenHands app.css) | Same `skeleton` / `skeleton-round` CSS classes |
| Empty state: icon + "No conversations yet" | `src/components/empty-state.tsx` — Clock icon + "未找到任务" | Same centered icon + text pattern |

### 3. Conversation Detail — ConversationMain (OpenHands `conversation-main.tsx`)

| OpenHands 1.8.0 | reverse-agent Frontend V1 | Notes |
|---|---|---|
| ConversationNameWithStatus header | `src/components/task-detail.tsx` — header with status dot, `←` back link, `#issueNumber`, branch, badges | Same dark rounded header (`rounded-lg border border-ra-border`) |
| ConversationTabs (Messages · Artifacts · Tool Calls · ...) | `src/components/task-detail.tsx` — RightPanelTab nav (Changed Files · Evidence · Authority) | Same horizontal tab nav with icons |
| Resizable horizontal split (chat left, tab panel right) | `src/components/task-detail.tsx` — same resizable split with `leftWidth` state + accessible separator resize handle | OpenHands `useResizablePanels` → manual mouse-drag implementation with `role="separator"` keyboard resize |
| ResizeHandle (draggable between panels) | `src/components/task-detail.tsx` — `<div role="separator">` with ArrowLeft/Right/Home/End | Same 1px transparent draggable strip, now keyboard-operable |

### 4. Activity Stream (OpenHands `generic-event-message.tsx`)

| OpenHands 1.8.0 | reverse-agent Frontend V1 | Notes |
|---|---|---|
| Model message: avatar icon + text + timestamp | `src/components/activity-stream.tsx` — same avatar circle + message bubble + time | Status dot colors mapped from OpenHands run state to reverse-agent RunState colors |
| GenericEventMessage: blue info, yellow warning, red error | `src/components/timeline.tsx` — same color variants | OpenHands status colors (#3b82f6, #f59e0b, #ef4444) replaced with reverse-agent design tokens |
| Tool call / result expandable | `src/components/evidence-panel.tsx` — collapsible EvidenceRow with raw JSON | Same expandable details pattern |

### 5. Changes / Diff View (OpenHands `file-diff-viewer.tsx`)

| OpenHands 1.8.0 | reverse-agent Frontend V1 | Notes |
|---|---|---|
| FileDiffViewer: hunk header + add/del highlighting | `src/components/diff-viewer.tsx` — same hunk headers + green/red coloring | OpenHands green (#014b01AA) / red (#750000AA) → same hex values in dark mode |
| ChangesTab: file icon + path + ± counts | `src/components/changes-panel.tsx` — same file icon + path + additions/deletions | OpenHands file-status icons (FilePlus, FileEdit, FileMinus) preserved |
| EmptyChangesMessage | `src/components/changes-panel.tsx` empty state | Same "No changes yet" centered pattern |

### 6. Permission Selector (OpenHands `custom-chat-input.tsx`)

| OpenHands 1.8.0 | reverse-agent Frontend V1 | Notes |
|---|---|---|
| Model selector dropdown in chat input | `src/components/permission-selector.tsx` — same dropdown pattern | Replaced model selection with permission profile selection (4 modes) |
| Dropdown: chevron + selected value | Same ChevronDown icon + selected profile label | Same `aria-haspopup="listbox"` + `aria-expanded` pattern |
| Plain-language summary below input | `src/components/authorization-summary.tsx` — same alert-banner pattern | Green "Authorized" or amber "Review required" status |

## Component structure comparison

```
OpenHands 1.8.0 (conceptual)
├── root-layout.tsx
│   ├── sidebar/sidebar.tsx (60/300 collapsed/expanded desktop sidebar)
│   ├── workspace outlet
│   └── chat-input-container.tsx (dock)
├── home.tsx
│   └── recent-conversations/recent-conversations.tsx
│       └── recent-conversation.tsx (conversation-card.tsx)
├── conversation.tsx
│   └── conversation-main/conversation-main.tsx
│       ├── conversation-name-with-status.tsx (header)
│       ├── conversation-tabs/conversation-tabs.tsx
│       ├── resizable panels (chat left, tabs right)
│       └── resize-handle
└── components/
    ├── conversation-panel/conversation-panel.tsx
    ├── diff-viewer/file-diff-viewer.tsx
    ├── changes-tab/changes-tab.tsx
    └── generic-event-message.tsx

reverse-agent Frontend V1
├── app-shell.tsx
│   ├── sidebar.tsx (60/300 collapsed/expanded desktop sidebar + mobile drawer)
│   ├── workspace outlet
│   └── new-task-composer.tsx (dock)
├── routes
│   ├── home.tsx → redirect to /tasks
│   ├── tasks.tsx → task-inbox.tsx
│   │   └── task-card.tsx
│   ├── task-detail.tsx
│   │   └── task-detail.tsx (inline)
│   └── (settings, approvals)
└── components/
    ├── conversation-panel.tsx
    ├── diff-viewer.tsx
    ├── changes-panel.tsx
    ├── activity-stream.tsx
    ├── timeline.tsx
    ├── evidence-panel.tsx
    ├── permission-selector.tsx
    ├── authorization-summary.tsx
    ├─ loading-state.tsx
    ├── empty-state.tsx
    ├── error-state.tsx
    ├── badge.tsx
    ├── collapsible-section.tsx
    └── editors/
        ├── custom-policy-editor.tsx
        ├── resource-access-editor.tsx
        ├── github-capabilities-editor.tsx
        ├── publication-editor.tsx
        └── autonomous-window-editor.tsx
```

## Visual style tokens (side-by-side)

| Design token | OpenHands 1.8.0 value | reverse-agent Frontend V1 value | Match? |
|---|---|---|---|
| Workspace background | `#0D0F11` (`--bg-dark`) | `--ra-base: #0d0f10` | Yes (1px offset, same perceptual dark) |
| Sidebar background | `#25272D` | `--ra-sidebar: #25272D` | Exact match |
| Content/workspace | `#1F2228` | `--ra-workspace: #1f2228` | Exact match |
| Panel background | `#171717` | `--ra-light: #171717` | Exact match |
| Input background | `#0C0C0C` | `--ra-input: #0d0f10` | Close match |
| Border | `#525252` | `--ra-border: #525252` | Exact match |
| Added line bg | `#014b01AA` | `bg-[#014b01AA]/20` | Same hex, 20% opacity for subtlety |
| Removed line bg | `#750000AA` | `bg-[#750000AA]/20` | Same hex, 20% opacity |
| Hunk header bg | `#3B82F6` (blue) | `#525252/30` (dark grey) | Adapted — grey is less prominent in dark theme |
| Primary accent | `#00BCD4` (cyan) | `--ra-accent: #3b82f6` (blue) | Adapted for consistency with dark palette |
| Error color | `#FF684E` (orange-red) | `--ra-status-error: #ef4444` (red) | Adapted — OpenHands uses orange-red, we use standard red |
| Skeleton animation | `pulse` keyframes | Same `skeleton` animation | Identical |
| Custom scrollbar | `::-webkit-scrollbar` | Same `customScrollbar` mixin | Identical |
| Font family | `Outfit` / `IBM Plex Mono` | Same imports | Identical |
| Font sizes | `text-xs` (12px) | Same | Identical |

## Target screenshot evidence (committed at HEAD 267d78f8)

Actual reverse-agent screenshots at the verification HEAD:

| Path | Viewport | Content |
|---|---|---|
| `frontend/artifacts/screenshots/task-inbox-desktop.png` | 1440×900 | Task inbox with Needs Owner Attention / Running / Recent sections |
| `frontend/artifacts/screenshots/task-inbox-mobile.png` | 390×844 | Mobile task inbox with hamburger drawer |
| `frontend/artifacts/screenshots/task-detail-desktop.png` | 1440×900 | Task detail with Activity + Changes/Evidence/Authority split |
| `frontend/artifacts/screenshots/task-detail-mobile.png` | 390×844 | Mobile single-pane task detail with Activity + tab nav |
| `frontend/artifacts/screenshots/custom-permission-editor.png` | 1440×900 | CUSTOM permission editor with all policy controls |
| `frontend/artifacts/screenshots/overnight-authorization-summary.png` | 1440×900 | Authorization summary from CUSTOM policy |

All screenshots use deterministic fixtures. No credentials, absolute paths,
private data, or production logs appear in any screenshot.

## OpenHands reference screenshot evidence

No OpenHands reference screenshots exist in the committed artifacts.
See the Methodology section above for the reason.

## Limitations

1. Side-by-side comparison tables are structural analysis, not pixel-comparison
   screenshots. They map each OpenHands 1.8.0 source path to its
   reverse-agent target path and note the adaptation.
2. OpenHands reference screenshots cannot be captured without running the
   OpenHands backend/runtime, which is outside this Work Item's scope.
3. Target screenshots were captured at a HEAD one commit before the
   fix-forward commits; the fix-forward changes did not affect visual rendering.
4. Screenshot capture was not re-executed at the exact final HEAD because the
   CLI verification environment does not include a headless browser and cannot
   install one without modifying `package.json`.

## Governance boundary

No real privileged operation, model invocation, OpenHands runtime,
credential access, merge, release, or deployment was performed.
PR #119 remains Draft.
