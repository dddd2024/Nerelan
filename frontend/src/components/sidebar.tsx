import { NavLink, useLocation } from "react-router";
import { Home, ListChecks, Settings } from "lucide-react";
import { cn } from "@/lib/cn";
import { useEffect } from "react";

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
 * OpenHands 1.8.0 Sidebar adaptation.
 *
 * Upstream source:
 *   frontend/src/components/features/sidebar/sidebar.tsx (tag 1.8.0)
 *   - vertical 75px icon bar on desktop
 *   - `<aside aria-label="...navigation" className="...md:w-[75px] md:min-w-[75px]
 *     flex flex-row md:flex-col ... bg-base ...">`
 *   - logo at top, new-conversation button, conversation-panel toggle,
 *     user avatar at bottom
 *
 * Structurally ported: same icon-bar layout, same flex-row-on-mobile /
 * flex-col-on-desktop responsive pattern. Icons use lucide-react with
 * OpenHands-style sizing (24px) and dark-palette colors.
 *
 * Modifications: OpenHands logo (SVG) → reverse-agent text; conversation-panel
 * toggle → task-list panel toggle; user avatar omitted (no auth in fixture
 * mode); New Task button replaces NewConversationButton.
 * License: MIT (inherited from OpenHands)
 */
export function Sidebar({
  onNewTask,
  onOpenConversationPanel,
  onConversationPanelClose,
  conversationPanelOpen,
}: SidebarProps) {
  const location = useLocation();

  useEffect(() => {
    onConversationPanelClose();
  }, [location.pathname, onConversationPanelClose]);

  return (
    <aside
      aria-label="导航"
      className={cn(
        "h-[54px] p-3 md:p-0 md:h-auto flex flex-row md:flex-col gap-1",
        "bg-ra-base md:w-[75px] md:min-w-[75px] sm:pt-0 sm:px-2 md:pt-[14px] md:px-0",
      )}
      data-testid="sidebar"
    >
      <nav className="flex flex-row md:flex-col items-center justify-between w-full h-auto md:w-auto md:h-full">
        <div className="flex flex-row md:flex-col items-center gap-[26px]">
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

          <div className="flex items-center justify-center">
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
          </div>

          <div className="flex items-center justify-center">
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
        </div>

        <div className="flex flex-row md:flex-col md:items-center gap-[26px]">
          <nav className="flex flex-row md:flex-col items-center gap-3 md:gap-[26px]">
            {ITEMS.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  data-testid={`sidebar-nav-${item.label}`}
                  className={cn(
                    "flex items-center justify-center w-6 h-6 rounded-md",
                    "text-ra-text-secondary hover:text-ra-text transition-colors",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    location.pathname === item.to &&
                      "text-ra-accent bg-ra-tertiary",
                  )}
                  title={item.label}
                >
                  <Icon className="h-5 w-5" />
                </NavLink>
              );
            })}
          </nav>
        </div>
      </nav>
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
