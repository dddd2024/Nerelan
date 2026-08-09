import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { NavLink, useLocation } from "react-router";
import { Menu, Plus, X } from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { ConversationPanel } from "@/components/conversation-panel";
import { NewTaskComposer } from "@/components/new-task-composer";
import { useCreateTask } from "@/hooks/use-tasks";
import { cn } from "@/lib/cn";

const DRAWER_ID = "mobile-nav-drawer";
const DRAWER_LABEL = "导航";

const SIDEBAR_ITEMS: { to: string; label: string }[] = [
  { to: "/", label: "首页" },
  { to: "/tasks", label: "任务" },
  { to: "/settings", label: "设置" },
];

function getNavLabel(to: string): string {
  const item = SIDEBAR_ITEMS.find((candidate) => candidate.to === to);
  return item?.label ?? to;
}

/**
 * OpenHands 1.8.0 root-layout adaptation with an accessible mobile drawer.
 *
 * Upstream sources (tag 1.8.0, commit c7a765d900df294cbbf0f405ae26c9cbbd0fcc29):
 *   frontend/src/routes/root-layout.tsx
 *   frontend/src/components/features/sidebar/sidebar-mobile-menu-bar.tsx
 *   frontend/src/components/features/sidebar/sidebar.tsx
 *   frontend/src/components/features/sidebar/sidebar-mobile-nav-context.tsx
 *
 * The desktop rail is controlled at the 768px `md` boundary. The mobile
 * trigger, backdrop and fixed drawer are the complementary `md:hidden`
 * surface. OpenHands runtime, backend and credential behavior is not used.
 */
export function AppShell({ children }: { children: ReactNode }) {
  const location = useLocation();
  const createTaskMutation = useCreateTask();
  const previousPathnameRef = useRef(location.pathname);

  const [conversationPanelOpen, setConversationPanelOpen] = useState(false);
  const [newTaskComposerOpen, setNewTaskComposerOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const triggerRef = useRef<HTMLButtonElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<string | null>(null);

  const handleConversationPanelOpen = useCallback(() => {
    setConversationPanelOpen(true);
  }, []);

  const handleConversationPanelClose = useCallback(() => {
    setConversationPanelOpen(false);
  }, []);

  const restoreScroll = useCallback(() => {
    if (scrollRef.current !== null) {
      document.body.style.overflow = scrollRef.current;
      scrollRef.current = null;
    }
  }, []);

  const closeDrawer = useCallback(
    (restoreFocus = true) => {
      setMobileNavOpen(false);
      restoreScroll();
      if (restoreFocus) {
        queueMicrotask(() => triggerRef.current?.focus());
      }
    },
    [restoreScroll],
  );

  const openDrawer = useCallback(() => {
    setConversationPanelOpen(false);
    setMobileNavOpen(true);
  }, []);

  useEffect(() => {
    if (!mobileNavOpen) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeDrawer();
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [closeDrawer, mobileNavOpen]);

  useEffect(() => {
    const pathnameChanged = previousPathnameRef.current !== location.pathname;
    previousPathnameRef.current = location.pathname;

    if (pathnameChanged && mobileNavOpen) {
      closeDrawer();
    }
  }, [closeDrawer, location.pathname, mobileNavOpen]);

  useEffect(() => {
    if (!mobileNavOpen) return;

    if (scrollRef.current === null) {
      scrollRef.current = document.body.style.overflow;
    }
    document.body.style.overflow = "hidden";

    const drawer = drawerRef.current;
    if (!drawer) {
      return () => restoreScroll();
    }

    const getFocusableElements = () =>
      Array.from(
        drawer.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      );

    const focusable = getFocusableElements();
    (closeButtonRef.current ?? focusable[0])?.focus();

    const trapFocus = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;

      const currentFocusable = getFocusableElements();
      if (currentFocusable.length === 0) {
        event.preventDefault();
        drawer.focus();
        return;
      }

      const first = currentFocusable[0];
      const last = currentFocusable[currentFocusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    drawer.addEventListener("keydown", trapFocus);
    return () => {
      drawer.removeEventListener("keydown", trapFocus);
      restoreScroll();
    };
  }, [mobileNavOpen, restoreScroll]);

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
        data-testid="mobile-menu-bar"
        data-agent-canvas-source="v1.6.1"
        className="md:hidden flex flex-row items-center gap-2 px-3 h-[54px] shrink-0 bg-ra-base border-b border-ra-border"
        inert={mobileNavOpen ? true : undefined}
        aria-hidden={mobileNavOpen ? "true" : undefined}
      >
        <button
          type="button"
          aria-label="打开菜单"
          aria-expanded={mobileNavOpen}
          aria-controls={DRAWER_ID}
          data-testid="mobile-menu-button"
          onClick={openDrawer}
          ref={triggerRef}
          className="flex items-center gap-2 text-ra-text-secondary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
          <span className="font-semibold text-ra-text">reverse-agent</span>
        </button>
      </div>

      <div
        className="fixed inset-0 z-40 md:hidden bg-black/50"
        aria-hidden="true"
        data-testid="mobile-drawer-backdrop"
        onClick={() => closeDrawer()}
        style={{ display: mobileNavOpen ? "" : "none" }}
      />

      <div
        ref={drawerRef}
        role="dialog"
        id={DRAWER_ID}
        aria-label={DRAWER_LABEL}
        aria-modal="true"
        aria-hidden={!mobileNavOpen}
        tabIndex={-1}
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
            onClick={() => closeDrawer()}
            ref={closeButtonRef}
            className="text-ra-text-tertiary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <nav aria-label="主导航" className="flex flex-col gap-1 p-2">
          {SIDEBAR_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              data-testid={`mobile-nav-${getNavLabel(item.to)}`}
              onClick={() => closeDrawer()}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm",
                  "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                  isActive
                    ? "bg-ra-tertiary text-ra-text"
                    : "text-ra-text-secondary hover:text-ra-text hover:bg-ra-tertiary",
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto flex flex-col gap-2 p-4 border-t border-ra-border">
          <button
            type="button"
            data-testid="mobile-new-task-button"
            onClick={() => {
              closeDrawer();
              setNewTaskComposerOpen(true);
            }}
            className="flex items-center justify-center gap-2 px-3 py-2 rounded-md bg-ra-accent text-ra-base text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            新建任务
          </button>
          <button
            type="button"
            data-testid="mobile-task-list-toggle"
            onClick={() => {
              closeDrawer();
              setConversationPanelOpen(true);
            }}
            className="flex items-center justify-center gap-2 px-3 py-2 rounded-md text-ra-text-secondary hover:text-ra-text hover:bg-ra-tertiary text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
          >
            任务列表
          </button>
        </div>
      </div>

      <div
        data-testid="app-shell-workspace"
        data-agent-canvas-source="v1.6.1"
        className="flex flex-col w-full min-w-0 flex-1 h-full bg-[var(--oh-surface)]"
        inert={mobileNavOpen ? true : undefined}
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
            onSubmit={(input) => createTaskMutation.mutate(input)}
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
