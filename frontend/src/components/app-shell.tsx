import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Sidebar } from "@/components/sidebar";
import { ConversationPanel } from "@/components/conversation-panel";
import { NewTaskComposer } from "@/components/new-task-composer";
import { useBreakpoint } from "@/hooks/use-breakpoint";
import { cn } from "@/lib/cn";

const SIDEBAR_ITEMS: { to: string; label: string }[] = [
  { to: "/", label: "首页" },
  { to: "/tasks", label: "任务" },
  { to: "/settings", label: "设置" },
];

/**
 * OpenHands 1.8.0 root-layout adaptation with mobile drawer.
 *
 * Upstream sources (tag 1.8.0):
 *   frontend/src/routes/root-layout.tsx
 *   — collapsible 60px/300px desktop sidebar
 *   — main workspace `flex flex-col w-full min-w-0 h-full gap-3`
 *   — dark bg-base (#0D0F11), overflow-hidden
 *
 *   frontend/src/components/features/sidebar/sidebar-mobile-menu-bar.tsx
 *   — `<button className="relative ... md:hidden">` hamburger trigger
 *
 *   frontend/src/components/features/sidebar/sidebar.tsx
 *   — `<div className="md:hidden ...">` backdrop + fixed left drawer
 *   — `w-[min(300px,85vw)]` with `translate-x` transition
 *
 *   frontend/src/components/features/sidebar/sidebar-mobile-nav-context.tsx
 *   — SidebarMobileNavProvider state with open/close/routeClose
 *
 * Structurally ported:
 *   - Desktop: hidden md:flex Sidebar with 60/300 collapsed/expanded
 *   - Mobile: max-md:flex hamburger bar + fixed left drawer with backdrop
 *   - Drawer: same nav items as desktop, close on route change / Escape / backdrop
 *   - Main workspace shell layout preserved
 *
 * Modifications: OpenHands branding, agent runtime, sandbox replaced with
 * fixture-driven reverse-agent domain. No server, websocket, or backend code.
 * License: MIT (inherited from OpenHands)
 */
export function AppShell({ children }: { children: ReactNode }) {
  const bp = useBreakpoint();
  const isDesktop = bp === "desktop";

  const [conversationPanelOpen, setConversationPanelOpen] = useState(false);
  const [newTaskComposerOpen, setNewTaskComposerOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const handleConversationPanelOpen = useCallback(
    () => setConversationPanelOpen(true),
    [],
  );
  const handleConversationPanelClose = useCallback(
    () => setConversationPanelOpen(false),
    [],
  );

  // Close mobile drawer on Escape
  useEffect(() => {
    if (!isDesktop && mobileNavOpen) {
      const onKey = (e: KeyboardEvent) => {
        if (e.key === "Escape") setMobileNavOpen(false);
      };
      window.addEventListener("keydown", onKey);
      return () => window.removeEventListener("keydown", onKey);
    }
  }, [isDesktop, mobileNavOpen]);

  return (
    <div
      data-testid="app-shell"
      className={cn(
        "h-screen flex flex-col md:flex-row bg-ra-base overflow-hidden",
      )}
    >
      {/* Desktop Sidebar — hidden on mobile/tablet */}
      {isDesktop && (
        <Sidebar
          onNewTask={() => setNewTaskComposerOpen(true)}
          onOpenConversationPanel={handleConversationPanelOpen}
          onConversationPanelClose={handleConversationPanelClose}
          conversationPanelOpen={conversationPanelOpen}
        />
      )}

      {/* Mobile hamburger menu bar */}
      {!isDesktop && (
        <div
          className="max-md:flex max-md:flex-row max-md:items-center max-md:gap-2 max-md:px-3 max-md:h-[54px] max-md:shrink-0 max-md:bg-ra-base max-md:border-b max-md:border-ra-border"
          data-testid="mobile-menu-bar"
        >
          <button
            type="button"
            aria-label="打开菜单"
            data-testid="mobile-menu-button"
            onClick={() => setMobileNavOpen(true)}
            className="flex items-center gap-2 text-ra-text-secondary hover:text-ra-text"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-5 w-5"
            >
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
        </div>
      )}

      {/* Mobile drawer backdrop */}
      {mobileNavOpen && (
        <div
          className="fixed inset-0 z-50 md:hidden bg-black/50"
          data-testid="mobile-drawer-backdrop"
          onClick={() => setMobileNavOpen(false)}
        />
      )}

      {/* Mobile drawer */}
      {mobileNavOpen && (
        <div
          className={cn(
            "fixed top-0 bottom-0 left-0 z-50 w-[min(300px,85vw)] md:hidden",
            "bg-ra-base flex flex-col shadow-lg",
          )}
          data-testid="mobile-drawer"
        >
          <div className="flex items-center justify-between p-4 border-b border-ra-border">
            <span className="text-sm font-semibold text-ra-text">reverse-agent</span>
            <button
              type="button"
              aria-label="关闭菜单"
              data-testid="mobile-drawer-close"
              onClick={() => setMobileNavOpen(false)}
              className="text-ra-text-tertiary hover:text-ra-text"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-5 w-5"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <nav className="flex flex-col gap-1 p-2">
            {SIDEBAR_ITEMS.map((item) => (
              <a
                key={item.to}
                href={item.to}
                onClick={() => setMobileNavOpen(false)}
                className="flex items-center gap-3 px-3 py-2 rounded-md text-ra-text-secondary hover:text-ra-text hover:bg-ra-tertiary"
                data-testid={`mobile-nav-${item.label}`}
              >
                {item.label}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-2 p-4 border-t border-ra-border">
            <button
              type="button"
              data-testid="mobile-new-task-button"
              onClick={() => {
                setMobileNavOpen(false);
                setNewTaskComposerOpen(true);
              }}
              className="flex items-center gap-2 px-3 py-2 rounded-md bg-ra-accent text-ra-base text-sm"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-4 w-4"
              >
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              新建任务
            </button>
            <button
              type="button"
              data-testid="mobile-task-list-toggle"
              onClick={() => {
                setMobileNavOpen(false);
                setConversationPanelOpen(true);
              }}
              className="flex items-center gap-2 px-3 py-2 rounded-md text-ra-text-secondary hover:text-ra-text text-sm"
            >
              任务列表
            </button>
          </div>
        </div>
      )}

      <div
        className={cn(
          "flex flex-col w-full min-w-0 flex-1 gap-3",
          isDesktop ? "h-full" : "h-[calc(100%-54px)]",
        )}
      >
        <div
          data-testid="workspace-outlet"
          className="flex-1 relative overflow-auto custom-scrollbar"
        >
          {children}
        </div>

        {newTaskComposerOpen && (
          <NewTaskComposer
            open={newTaskComposerOpen}
            onClose={() => setNewTaskComposerOpen(false)}
          />
        )}
      </div>

      <ConversationPanel
        open={conversationPanelOpen}
        onClose={handleConversationPanelClose}
      />
    </div>
  );
}
