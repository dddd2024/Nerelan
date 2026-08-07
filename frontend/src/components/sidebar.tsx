import { NavLink, useLocation } from "react-router";
import { Home, ListChecks, Settings, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/cn";
import { useEffect, useState } from "react";

export interface SidebarItem {
  to: string;
  label: string;
  icon: typeof Home;
}

const ITEMS: SidebarItem[] = [
  { to: "/", label: "首页", icon: Home },
  { to: "/tasks", label: "任务", icon: ListChecks },
  { to: "/settings", label: "设置", icon: Settings },
];

interface SidebarProps {
  onNewTask: () => void;
  onOpenConversationPanel: () => void;
  onConversationPanelClose: () => void;
  conversationPanelOpen: boolean;
}

/**
 * OpenHands 1.8.0 Desktop Sidebar adaptation.
 *
 * Upstream sources (tag 1.8.0):
 *   frontend/src/components/features/sidebar/sidebar.tsx
 *   - `md:flex-col ... md:w-[60px] md:min-w-[60px]` collapsed state
 *   - `md:w-[300px] md:min-w-[300px]` expanded state
 *   - desktop-only: `hidden` on mobile (`max-md:hidden` in layout wrapper)
 *   - logo, collapse toggle, new-conversation button, conversation panel toggle,
 *     nav links, user avatar at bottom
 *
 * Structurally ported: same 60/300 collapsed/expanded desktop sidebar,
 * same nav icon layout with labels shown in expanded state.
 *
 * Modifications: OpenHands branding → reverse-agent; conversation panel
 * toggle → task list toggle; user avatar omitted (fixture-only mode);
 * nav items: home/tasks/settings.
 * License: MIT (inherited from OpenHands)
 */
export function Sidebar({
  onNewTask,
  onOpenConversationPanel,
  onConversationPanelClose,
  conversationPanelOpen,
}: SidebarProps) {
  const [collapsed, setCollapsed] = useState(true);
  const location = useLocation();

  useEffect(() => {
    if (onConversationPanelClose) onConversationPanelClose();
  }, [location.pathname, onConversationPanelClose]);

  return (
    <aside
      aria-label="导航"
      className={cn(
        "hidden md:flex flex-col h-screen bg-ra-base",
        "transition-all duration-200 ease-in-out border-r border-ra-border",
        collapsed ? "w-[60px] min-w-[60px] sidebar-collapsed" : "w-[300px] min-w-[300px] sidebar-expanded",
      )}
      data-testid="sidebar"
      data-collapsed={String(collapsed)}
    >
      <div className="flex flex-col items-center justify-between gap-1 flex-1 py-2">
        <div className="flex flex-col items-center gap-[26px]">
          <div className="flex items-center justify-center">
            <button
              type="button"
              aria-label="reverse-agent"
              data-testid="sidebar-logo"
              onClick={() => {
                window.location.href = "/";
              }}
              className="text-xs font-semibold text-ra-text-secondary hover:text-ra-text transition-colors"
            >
              RA
            </button>
          </div>

          <button
            type="button"
            aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"}
            aria-pressed={!collapsed}
            data-testid="sidebar-collapse-toggle"
            onClick={() => setCollapsed((c) => !c)}
            className="w-6 h-6 flex items-center justify-center text-ra-text-secondary hover:text-ra-text transition-colors"
            title={collapsed ? "展开" : "收起"}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </button>

          <button
            type="button"
            aria-label="新建任务"
            data-testid="new-task-button"
            onClick={onNewTask}
            className="w-6 h-6 rounded-full flex items-center justify-center text-ra-text-secondary hover:text-ra-accent transition-colors"
            title="新建任务"
          >
            <PlusIcon className="h-5 w-5" />
          </button>

          <button
            type="button"
            aria-label={conversationPanelOpen ? "关闭任务列表" : "打开任务列表"}
            data-testid="toggle-conversation-panel"
            onClick={conversationPanelOpen ? onConversationPanelClose : onOpenConversationPanel}
            className={cn(
              "w-6 h-6 flex items-center justify-center transition-colors",
              conversationPanelOpen
                ? "text-ra-accent"
                : "text-ra-text-secondary hover:text-ra-text",
            )}
            title={conversationPanelOpen ? "关闭任务列表" : "打开任务列表"}
          >
            <ListIcon className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex flex-col items-center gap-3 w-full">
          {ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                data-testid={`sidebar-nav-${item.label}`}
                className={cn(
                  "flex items-center justify-center rounded-md",
                  collapsed ? "w-6 h-6" : "w-full h-10 justify-start px-3 gap-2",
                  "text-ra-text-secondary hover:text-ra-text transition-colors",
                  "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                  location.pathname === item.to &&
                    "text-ra-accent bg-ra-tertiary",
                )}
                title={item.label}
              >
                <Icon className="h-5 w-5 shrink-0" />
                {!collapsed && <span className="text-sm whitespace-nowrap">{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}

function PlusIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  );
}

function ListIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}
