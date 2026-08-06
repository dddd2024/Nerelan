# Visual Acceptance Evidence — Frontend V1 OpenHands Adaptation

This document records side-by-side visual comparison evidence between
OpenHands 1.8.0 UI concepts and the reverse-agent Frontend V1 adaptation.

## Methodology

Source screenshots were captured from OpenHands 1.8.0 deployed UI.
Target screenshots were captured from `npm run dev` loopback
(`http://localhost:5173`) with fixture data.

## Side-by-side comparisons

### 1. Root Layout — Sidebar + Workspace (OpenHands `root-layout.tsx`)

| OpenHands 1.8.0 | reverse-agent Frontend V1 | Notes |
|---|---|---|
| Fixed 75px dark icon sidebar on left | `src/components/app-shell.tsx` — same 75px `md:w-[75px]` icon bar | Sidebar is `flex-row` on mobile (bottom bar), `flex-col` on desktop |
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
| Resizable horizontal split (chat left, tab panel right) | `src/components/task-detail.tsx` — same resizable split with `leftWidth` state + resize handle | OpenHands `useResizablePanels` → manual mouse-drag implementation |
| ResizeHandle (draggable between panels) | `src/components/task-detail.tsx` — `<button>` with `cursor-ew-resize` | Same 1px transparent draggable strip |

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
│   ├── sidebar/sidebar.tsx (75px icon bar)
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
│   ├── sidebar.tsx (75px icon bar)
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

## Acceptance criteria

1. ✅ Layout structure matches OpenHands 1.8.0 (icon sidebar + workspace + dock)
2. ✅ Dark color palette matches (workspace, sidebar, borders)
3. ✅ Conversation cards match (status dot + title + secondary info)
4. ✅ Header bar matches (status dot + back link + branch + badges)
5. ✅ Tab navigation matches (horizontal icon tabs)
6. ✅ Diff viewer matches (hunk headers + add/del highlighting)
7. ✅ Permission selector matches (dropdown + plain-language summary)
8. ✅ Skeleton/empty/error states match OpenHands patterns
9. ✅ Responsive behavior matches (flex-row mobile, flex-col desktop)
10. ✅ Typography matches (Outfit headings, IBM Plex Mono code)
