import { useEffect, useState, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router";
import {
  ChevronLeft,
  ChevronRight,
  Bot,
  Home,
  Inbox,
  ListChecks,
  Map,
  Menu,
  Plus,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/cn";
import { AgentCanvasSidebarFrame } from "@/vendor/agent-canvas-v1.6.1/agent-canvas-sidebar-frame";
import { SidebarCollapsedIconSlot } from "@/vendor/agent-canvas-v1.6.1/sidebar-collapsed-icon-slot";
import {
  SIDEBAR_ICON_SLOT_CLASS,
  SIDEBAR_ROW_INTERACTIVE_CLASS,
  sidebarNavLabelClassName,
  sidebarNavRowClassName,
} from "@/vendor/agent-canvas-v1.6.1/sidebar-layout";

export interface SidebarItem {
  to: string;
  label: string;
  icon: typeof Home;
}

const ITEMS: SidebarItem[] = [
  { to: "/", label: "首页", icon: Home },
  { to: "/tasks", label: "任务", icon: ListChecks },
  { to: "/inbox", label: "收件箱", icon: Inbox },
  { to: "/roadmap", label: "路线图", icon: Map },
  { to: "/runs", label: "Agent 运行", icon: Bot },
  { to: "/settings", label: "设置", icon: Settings },
];

interface SidebarProps {
  onNewTask: () => void;
  onOpenConversationPanel: () => void;
  onConversationPanelClose: () => void;
  conversationPanelOpen: boolean;
}

interface SidebarActionProps {
  collapsed: boolean;
  active?: boolean;
  label: string;
  testId: string;
  icon: ReactNode;
  onClick: () => void;
}

function SidebarAction({
  collapsed,
  active = false,
  label,
  testId,
  icon,
  onClick,
}: SidebarActionProps) {
  return (
    <button
      type="button"
      aria-label={label}
      data-testid={testId}
      onClick={onClick}
      className={cn(
        sidebarNavRowClassName({ collapsed }),
        active
          ? SIDEBAR_ROW_INTERACTIVE_CLASS.active
          : SIDEBAR_ROW_INTERACTIVE_CLASS.idle,
      )}
      title={label}
    >
      {collapsed ? (
        <SidebarCollapsedIconSlot active={active}>
          {icon}
        </SidebarCollapsedIconSlot>
      ) : (
        <>
          <span className={SIDEBAR_ICON_SLOT_CLASS}>{icon}</span>
          <span className={sidebarNavLabelClassName(false)}>{label}</span>
        </>
      )}
    </button>
  );
}

/** Thin reverse-agent adapter around the pinned Agent Canvas sidebar frame. */
export function Sidebar({
  onNewTask,
  onOpenConversationPanel,
  onConversationPanelClose,
  conversationPanelOpen,
}: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  useEffect(() => {
    onConversationPanelClose();
  }, [location.pathname, onConversationPanelClose]);

  const logo = (
    <button
      type="button"
      aria-label="reverse-agent"
      data-testid="sidebar-logo"
      onClick={() => {
        window.location.href = "/";
      }}
      className={cn(
        "flex h-9 w-full items-center text-sm font-semibold tracking-[-0.015em]",
        "text-ra-text hover:text-ra-text",
        collapsed ? "justify-center" : "justify-start px-2.5",
      )}
      title="Nerelan"
    >
      {collapsed ? (
        <span className="text-[15px] font-semibold">N</span>
      ) : (
        <span className="text-[15px] font-semibold">Nerelan</span>
      )}
    </button>
  );

  const collapseToggle = (
    <button
      type="button"
      aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"}
      aria-pressed={!collapsed}
      data-testid="sidebar-collapse-toggle"
      onClick={() => setCollapsed((value) => !value)}
      className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[var(--oh-muted)] hover:bg-[var(--oh-surface-raised)] hover:text-ra-text"
      title={collapsed ? "展开" : "收起"}
    >
      {collapsed ? (
        <ChevronRight className="h-[17px] w-[17px]" />
      ) : (
        <ChevronLeft className="h-[17px] w-[17px]" />
      )}
    </button>
  );

  const primaryActions = (
    <>
      <SidebarAction
        collapsed={collapsed}
        label="新建任务"
        testId="new-task-button"
        icon={<Plus className="h-[18px] w-[18px]" />}
        onClick={onNewTask}
      />
      <SidebarAction
        collapsed={collapsed}
        active={conversationPanelOpen}
        label={conversationPanelOpen ? "关闭任务列表" : "打开任务列表"}
        testId="toggle-conversation-panel"
        icon={<Menu className="h-[18px] w-[18px]" />}
        onClick={
          conversationPanelOpen
            ? onConversationPanelClose
            : onOpenConversationPanel
        }
      />
    </>
  );

  const navigation = ITEMS.map((item) => {
    const Icon = item.icon;
    return (
      <NavLink
        key={item.to}
        to={item.to}
        end={item.to === "/"}
        data-testid={`sidebar-nav-${item.label}`}
        className={({ isActive }) =>
          cn(
            sidebarNavRowClassName({ collapsed }),
            isActive
              ? SIDEBAR_ROW_INTERACTIVE_CLASS.active
              : SIDEBAR_ROW_INTERACTIVE_CLASS.idle,
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
          )
        }
        title={item.label}
      >
        {({ isActive }) =>
          collapsed ? (
            <SidebarCollapsedIconSlot active={isActive}>
              <Icon className="h-[18px] w-[18px]" />
            </SidebarCollapsedIconSlot>
          ) : (
            <>
              <span className={SIDEBAR_ICON_SLOT_CLASS}>
                <Icon className="h-[18px] w-[18px]" />
              </span>
              <span className={sidebarNavLabelClassName(false)}>
                {item.label}
              </span>
            </>
          )
        }
      </NavLink>
    );
  });

  return (
    <AgentCanvasSidebarFrame
      collapsed={collapsed}
      onExpand={() => setCollapsed(false)}
      logo={logo}
      collapseToggle={collapseToggle}
      primaryActions={primaryActions}
      navigation={navigation}
    />
  );
}
