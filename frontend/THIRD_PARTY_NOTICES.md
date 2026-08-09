# Third-Party Notices

reverse-agent Frontend V1 incorporates structural adaptations of OpenHands 1.8.0
(commit `c7a765d900df294cbbf0f405ae26c9cbbd0fcc29`), licensed under the MIT License.

It also incorporates a bounded pinned direct source fork of selected
presentation/layout files from Agent Canvas v1.6.1, licensed under the MIT
License. The MIT terms reproduced below apply to both attributions.

## Agent Canvas v1.6.1

**Repository:** https://github.com/OpenHands/agent-canvas
**Tag:** v1.6.1
**Commit:** `43f091baf135142ed6c146f888f44a957141193f`
**License:** MIT
**Copyright:** Copyright © OpenHands contributors

Vendored or directly derived presentation files are recorded in
`frontend/OPENHANDS_REUSE_MAP.md`. OpenHands backend, Agent Server,
conversation API/store, credentials, and model/runtime code are not included.

## OpenHands 1.8.0

**Repository:** https://github.com/OpenHands/OpenHands
**Tag:** 1.8.0
**Commit:** `c7a765d900df294cbbf0f405ae26c9cbbd0fcc29`
**License:** MIT
**Copyright:** Copyright © 2025 OpenHands contributors

### MIT License

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### What was adapted (non-enterprise source only)

The following OpenHands 1.8.0 files were structurally ported (not copied
verbatim) into the reverse-agent frontend under `frontend/src/`:

| Upstream source | License | Adaptation type |
|---|---|---|
| `src/index.css` | MIT | Design tokens and CSS utilities ported to `frontend/src/index.css` |
| `tailwind.config.js` | MIT | Color palette ported to Tailwind `@theme` |
| `src/themes/color-themes.ts` | MIT | Color token definitions ported to `@theme` |
| `src/routes/root-layout.tsx` | MIT | Application shell ported to `app-shell.tsx` |
| `src/routes/home.tsx` | MIT | Home screen ported to `routes/home.tsx` + `task-inbox.tsx` |
| `src/routes/conversation.tsx` | MIT | Conversation route ported to `task-detail.tsx` |
| `src/components/features/sidebar/sidebar.tsx` | MIT | Sidebar port to `sidebar.tsx` |
| `src/components/features/sidebar/sidebar-rail-body.tsx` | MIT | Sidebar rail pattern ported to `sidebar.tsx` |
| `src/components/features/sidebar/sidebar-layout.ts` | MIT | Layout class constants ported to CSS `@theme` |
| `src/components/features/sidebar/sidebar-mobile-menu-bar.tsx` | MIT | Mobile bar pattern ported to `sidebar.tsx` |
| `src/components/features/sidebar/sidebar-nav-link.tsx` | MIT | Nav link pattern ported to `sidebar.tsx` |
| `src/components/features/sidebar/openhands-logo-button.tsx` | MIT | Logo button pattern ported to `sidebar.tsx` |
| `src/components/features/conversation-panel/conversation-panel.tsx` | MIT | Task list panel ported to `conversation-panel.tsx` |
| `src/components/features/conversation-panel/conversation-panel-wrapper.tsx` | MIT | Panel overlay pattern ported to `conversation-panel.tsx` |
| `src/components/features/conversation-panel/conversation-card/conversation-card.tsx` | MIT | Task card ported to `task-card.tsx` |
| `src/components/features/conversation-panel/conversation-card/conversation-card-header.tsx` | MIT | Card header ported to `task-card.tsx` |
| `src/components/features/conversation-panel/conversation-card/conversation-card-footer.tsx` | MIT | Card footer ported to `task-card.tsx` |
| `src/components/features/conversation-panel/conversation-card/conversation-card-skeleton.tsx` | MIT | Loading skeleton ported to `conversation-panel.tsx` |
| `src/components/features/conversation-panel/conversation-card/conversation-status-dot.tsx` | MIT | Status dot ported to `task-card.tsx` |
| `src/components/features/conversation-panel/compact-conversation-row.tsx` | MIT | Compact row ported to `task-card.tsx` |
| `src/components/features/conversation-panel/new-conversation-button.tsx` | MIT | New task button ported to `sidebar.tsx` |
| `src/components/features/conversation-panel/start-task-card/start-task-card.tsx` | MIT | Composer card ported to `new-task-composer.tsx` |
| `src/components/features/home/home-header/home-header.tsx` | MIT | Header pattern ported to `task-inbox.tsx` |
| `src/components/features/home/home-header/guide-message.tsx` | MIT | Guide message ported to `task-inbox.tsx` |
| `src/components/features/home/new-conversation/new-conversation.tsx` | MIT | New conversation card ported to `new-task-composer.tsx` |
| `src/components/features/conversation/conversation-main/conversation-main.tsx` | MIT | Workspace split ported to `task-detail.tsx` |
| `src/components/features/conversation/conversation-name-with-status.tsx` | MIT | Header ported to `task-detail.tsx` |
| `src/components/features/conversation/conversation-tabs/conversation-tabs.tsx` | MIT | Tab nav ported to `task-detail.tsx` |
| `src/components/features/chat/chat-input-container.tsx` | MIT | Composer container ported to `new-task-composer.tsx` |
| `src/components/features/chat/interactive-chat-box.tsx` | MIT | Chat input ported to `new-task-composer.tsx` |
| `src/components/features/chat/custom-chat-input.tsx` | MIT | Dropdown pattern ported to `permission-selector.tsx` |
| `src/components/features/chat/chat-input-model.tsx` | MIT | Model selector ported to `permission-selector.tsx` |
| `src/components/features/chat/chat-send-button.tsx` | MIT | Send button ported to `new-task-composer.tsx` |
| `src/components/features/chat/generic-event-message.tsx` | MIT | Event message ported to `activity-stream.tsx` |
| `src/components/features/chat/model-messages.tsx` | MIT | Message rendering ported to `activity-stream.tsx` |
| `src/components/features/diff-viewer/file-diff-viewer.tsx` | MIT | Diff viewer ported to `diff-viewer.tsx` |
| `src/components/features/diff-viewer/changes-tab.tsx` | MIT | Changes panel ported to `changes-panel.tsx` |
| `src/components/features/diff-viewer/empty-changes-message.tsx` | MIT | Empty state ported to `empty-state.tsx` |
| `src/components/features/diff-viewer/loading-spinner.tsx` | MIT | Loading spinner ported to `loading-state.tsx` |
| `src/components/features/conversation-panel/hooks-empty-state.tsx` | MIT | Empty state ported to `empty-state.tsx` |
| `src/components/shared/buttons/styled-tooltip.tsx` | MIT | Tooltip pattern ported to `sidebar.tsx` |
| `src/components/shared/navigation-link.tsx` | MIT | Nav link ported to `sidebar.tsx` |

### What was NOT reused

- OpenHands Agent Loop / runtime executor
- OpenHands sandbox / runtime / database
- OpenHands backend API code (`src/api/**`)
- OpenHands enterprise source (`enterprise/**`)
- Any credentials, model APIs, or production mutation APIs

### Disclaimer

The reverse-agent frontend is a derivative work that structurally adapts
OpenHands UI patterns for a fixture-driven, offline prototype. It does not
include, execute, or redistribute OpenHands backend, runtime, sandbox, or
enterprise code. All OpenHands runtime/backend dependencies are stubbed or
replaced with deterministic fixtures.
