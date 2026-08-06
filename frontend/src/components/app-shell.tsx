import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router";
import { Sidebar } from "@/components/sidebar";
import { ConversationPanel } from "@/components/conversation-panel";
import { NewTaskComposer } from "@/components/new-task-composer";
import { cn } from "@/lib/cn";

const DRAWER_ID = "mobile-nav-drawer";
const DRAWER_LABEL = "导航";

const SIDEBAR_ITEMS: { to: string; label: string }[] = [
  { to: "/", label: "首页" },
  { to: "/tasks", label: "任务" },
  { to: "/settings", label: "设置" },
];

function getNavLabel(to: string): string {
  const item = SIDEBAR_ITEMS.find((s) => s.to === to);
  return item?.label ?? to;
}

/**
 * OpenHands 1.8.0 root-layout adaptation with accessible mobile drawer.
 *
 * Upstream sources (tag 1.8.0, commit c7a765d900df294cbbf0f405ae26c9cbbd0fcc29):
 *   frontend/src/routes/root-layout.tsx
 *   — collapsible 60px / 300px desktop sidebar (`hidden md:flex`)
 *   — main workspace `flex flex-col w-full min-w-0 h-full gap-3`
 *
 *   frontend/src/components/features/sidebar/sidebar-mobile-menu-bar.tsx
 *   — `<button className="... md:hidden">` hamburger trigger
 *
 *   frontend/src/components/features/sidebar/sidebar.tsx
 *   — `<div className="md:hidden ...">` backdrop + fixed left drawer
 *   — `w-[min(300px,85vw)]` with translate-x transition
 *
 *   frontend/src/components/features/sidebar/sidebar-mobile-nav-context.tsx
 *   — SidebarMobileNavProvider state with open / close / routeClose
 *
 * Structurally ported (768px CSS shell boundary):
 *   - Desktop sidebar: always rendered, `hidden md:flex`
 *   - Mobile menu bar: always rendered, `md:hidden` with hamburger trigger
 *   - Mobile drawer: `fixed inset-y-0 left-0`, `w-[min(300px,85vw)]`, `md:hidden`
 *   - Backdrop: `fixed inset-0`, `md:hidden`, closes on click / Escape
 *   - Drawer: `role="dialog"`, `aria-modal`, focus trap, focus restore
 *   - Drawer close: Escape / backdrop / close button / route-change
 *   - Shell chrome visibility is controlled entirely by CSS; no React
 *     breakpoint state is used for the sidebar/drawer split.
 *
 * Modifications: OpenHands branding and agent runtime replaced with fixture-driven
 * reverse-agent domain. No server, websocket, or backend code.
 * License: MIT (inherited from OpenHands)
 */
export function AppShell({ children }: { children: ReactNode }) {
  const location = useLocation();
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

  const triggerRef = useRef<HTMLButtonElement>(null);
  const closeBtnRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<{ style: string } | null>(null);

  function restoreScroll() {
    if (scrollRef.current) {
      document.body.style.overflow = scrollRef.current.style;
    }
    scrollRef.current = null;
  }

  function closeDrawer() {
    setMobileNavOpen(false);
    restoreScroll();
    triggerRef.current?.focus();
  }

  // Escape closes drawer
  useEffect(() => {
    if (!mobileNavOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        closeDrawer();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mobileNavOpen]);

  // Route-change closes drawer
  useEffect(() => {
    if (mobileNavOpen) {
      setMobileNavOpen(false);
      restoreScroll();
      triggerRef.current?.focus();
    }
  }, [location.pathname, mobileNavOpen]);

  // Focus into drawer on open; Tab/Shift+Tab wraps inside drawer
  useEffect(() => {
    if (!mobileNavOpen) return;
    scrollRef.current = { style: document.body.style.overflow };
    document.body.style.overflow = "hidden";

    const el = drawerRef.current;
    if (!el) return;
    const focusable = Array.from(
      el.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      ),
    );
    if (closeBtnRef.current) {
      closeBtnRef.current.focus();
    } else if (focusable.length) {
      focusable[0].focus();
    }
    const handler = (e: KeyboardEvent) => {
      if (e.key !== "Tab" || !focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    el.addEventListener("keydown", handler);
    return () => {
      el.removeEventListener("keydown", handler);
    };
  }, [mobileNavOpen]);

  const handleMobileNavClose = closeDrawer;

  return (
    <div
      data-testid="app-shell"
      className={cn(
        "h-screen flex flex-col md:flex-row bg-ra-base overflow-hidden",
      )}
    >
      <Sidebar
        onNewTask={() => setNewTaskComposerOpen(true)}
        onOpenConversationPanel={handleConversationPanelOpen}
        onConversationPanelClose={handleConversationPanelClose}
        conversationPanelOpen={conversationPanelOpen}
      />

      <div
        className="md:hidden flex flex-row items-center gap-2 px-3 h-[54px] shrink-0 bg-ra-base border-b border-ra-border"
      >
        <button
          type="button"
          aria-label="打开菜单"
          aria-expanded={mobileNavOpen}
          aria-controls={DRAWER_ID}
          data-testid="mobile-menu-button"
          onClick={() => setMobileNavOpen(true)}
          ref={triggerRef}
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

      <div
        className="fixed inset-0 z-50 md:hidden bg-black/50"
        aria-hidden="true"
        data-testid="mobile-drawer-backdrop"
        onClick={handleMobileNavClose}
        style={{ display: mobileNavOpen ? "" : "none" }}
      />

      <div
        ref={drawerRef}
        role="dialog"
        id={DRAWER_ID}
        aria-label={DRAWER_LABEL}
        aria-modal="true"
        aria-hidden={mobileNavOpen}
        data-testid="mobile-drawer"
        className="fixed top-0 bottom-0 left-0 z-50 w-[min(300px,85vw)] md:hidden bg-ra-base flex flex-col shadow-lg"
        style={{ display: mobileNavOpen ? "" : "none" }}
      >
        <div className="flex items-center justify-between p-4 border-b border-ra-border">
          <span className="text-sm font-semibold text-ra-text">reverse-agent</span>
          <button
            type="button"
            aria-label="关闭菜单"
            data-testid="mobile-drawer-close"
            onClick={handleMobileNavClose}
            ref={closeBtnRef}
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
            <NavLink
              key={item.to}
              to={item.to}
              data-testid={`mobile-nav-${getNavLabel(item.to)}`}
              onClick={handleMobileNavClose}
              className="flex items-center gap-3 px-3 py-2 rounded-md text-ra-text-secondary hover:text-ra-text hover:bg-ra-tertiary"
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2 p-4 border-t border-ra-border">
          <button
            type="button"
            data-testid="mobile-new-task-button"
            onClick={() => {
              setMobileNavOpen(false);
              restoreScroll();
              setNewTaskComposerOpen(true);
              triggerRef.current?.focus();
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
              restoreScroll();
              setConversationPanelOpen(true);
              triggerRef.current?.focus();
            }}
            className="flex items-center gap-2 px-3 py-2 rounded-md text-ra-text-secondary hover:text-ra-text text-sm"
          >
            任务列表
          </button>
        </div>
      </div>

      <div
        className="flex flex-col w-full min-w-0 flex-1 gap-3 h-full"
        aria-hidden={mobileNavOpen ? "true" : undefined}
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
