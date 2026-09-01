import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router";
import {
  Bot,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Folder,
  Inbox,
  ListChecks,
  Map,
  MoreHorizontal,
  Plus,
  Search,
  Settings,
} from "lucide-react";
import { useTasks } from "@/hooks/use-tasks";
import { cn } from "@/lib/cn";
import { AgentCanvasSidebarFrame } from "@/vendor/agent-canvas-v1.6.1/agent-canvas-sidebar-frame";
import { SidebarCollapsedIconSlot } from "@/vendor/agent-canvas-v1.6.1/sidebar-collapsed-icon-slot";
import {
  SIDEBAR_ICON_SLOT_CLASS,
  SIDEBAR_ROW_INTERACTIVE_CLASS,
  sidebarNavLabelClassName,
  sidebarNavRowClassName,
} from "@/vendor/agent-canvas-v1.6.1/sidebar-layout";
import type { Task } from "@/types";

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
  text?: string;
  testId: string;
  icon: ReactNode;
  onClick: () => void;
}

const SECONDARY_ROUTES = [
  { to: "/tasks", label: "任务", icon: ListChecks },
  { to: "/inbox", label: "收件箱", icon: Inbox },
  { to: "/roadmap", label: "路线图", icon: Map },
  { to: "/runs", label: "Agent 运行", icon: Bot },
] as const;

function timestamp(value: string) {
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function projectLabel(repository: string) {
  const pieces = repository.split("/").filter(Boolean);
  return pieces.at(-1) ?? repository;
}

function stateDot(task: Task) {
  if (task.state === "RUNNING") return "bg-ra-accent";
  if (task.state === "BLOCKED_EXTERNAL" || task.state === "REWORK_REQUIRED") {
    return "bg-ra-status-starting";
  }
  if (task.state === "FAILED_TERMINAL") return "bg-ra-status-error";
  return "bg-ra-text-tertiary/55";
}

function SidebarAction({
  collapsed,
  active = false,
  label,
  text = label,
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
      title={text}
    >
      {collapsed ? (
        <SidebarCollapsedIconSlot active={active}>{icon}</SidebarCollapsedIconSlot>
      ) : (
        <>
          <span className={SIDEBAR_ICON_SLOT_CLASS}>{icon}</span>
          <span className={sidebarNavLabelClassName(false)}>{text}</span>
        </>
      )}
    </button>
  );
}

function SectionLabel({ children, testId }: { children: ReactNode; testId: string }) {
  return (
    <div
      data-testid={testId}
      className="px-2.5 pb-1 pt-2 text-[10px] font-medium uppercase tracking-[0.13em] text-ra-text-tertiary"
    >
      {children}
    </div>
  );
}

/** Task-first Nerelan navigation built from authoritative task read-model data. */
export function Sidebar({
  onNewTask,
  onOpenConversationPanel,
  onConversationPanelClose,
  conversationPanelOpen,
}: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { data: tasks = [] } = useTasks();

  useEffect(() => {
    onConversationPanelClose();
    setMoreOpen(false);
  }, [location.pathname, onConversationPanelClose]);

  const recentTasks = useMemo(
    () =>
      [...tasks]
        .sort((left, right) => timestamp(right.updatedAt) - timestamp(left.updatedAt))
        .slice(0, 4),
    [tasks],
  );

  const projects = useMemo(
    () =>
      Array.from(
        new Set(
          tasks
            .map((task) => task.repository?.trim() ?? "")
            .filter((repository) => repository.length > 0),
        ),
      ).slice(0, 5),
    [tasks],
  );

  const selectedRepository = new URLSearchParams(location.search).get("repository");

  const logo = (
    <button
      type="button"
      aria-label="Nerelan"
      data-testid="sidebar-logo"
      onClick={() => navigate("/")}
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
        text="新建任务"
        testId="new-task-button"
        icon={<Plus className="h-4 w-4" />}
        onClick={onNewTask}
      />
      <SidebarAction
        collapsed={collapsed}
        active={conversationPanelOpen}
        label={conversationPanelOpen ? "关闭任务列表" : "打开任务列表"}
        text="搜索"
        testId="toggle-conversation-panel"
        icon={<Search className="h-4 w-4" />}
        onClick={
          conversationPanelOpen
            ? onConversationPanelClose
            : onOpenConversationPanel
        }
      />
    </>
  );

  const navigation = collapsed ? null : (
    <>
      <Link to="/" data-testid="sidebar-nav-首页" className="sr-only">
        首页
      </Link>

      <section aria-label="最近任务">
        <SectionLabel testId="sidebar-section-recent">Recent</SectionLabel>
        <div className="flex flex-col gap-0.5">
          {recentTasks.length > 0 ? (
            recentTasks.map((task) => {
              const selected = location.pathname === `/tasks/${task.id}`;
              return (
                <Link
                  key={task.id}
                  to={`/tasks/${task.id}`}
                  data-testid={`sidebar-recent-task-${task.id}`}
                  data-selected={String(selected)}
                  className={cn(
                    "flex h-[30px] min-h-[30px] min-w-0 items-center gap-2 rounded-md px-2.5 text-[13px] leading-4",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    selected
                      ? "bg-ra-tertiary text-ra-text"
                      : "text-ra-text-secondary hover:bg-[var(--oh-surface-raised)] hover:text-ra-text",
                  )}
                  title={task.title}
                >
                  <span
                    className={cn("h-1.5 w-1.5 shrink-0 rounded-full", stateDot(task))}
                    aria-hidden="true"
                  />
                  <span className="min-w-0 flex-1 truncate">{task.title}</span>
                </Link>
              );
            })
          ) : (
            <p className="px-2.5 py-1 text-[11px] text-ra-text-tertiary">暂无最近任务</p>
          )}
        </div>
      </section>

      <section aria-label="项目" className="mt-2">
        <SectionLabel testId="sidebar-section-projects">Projects</SectionLabel>
        <div className="flex flex-col gap-0.5">
          {projects.length > 0 ? (
            projects.map((repository) => {
              const selected =
                location.pathname === "/tasks" && selectedRepository === repository;
              return (
                <Link
                  key={repository}
                  to={`/tasks?repository=${encodeURIComponent(repository)}`}
                  data-testid={`sidebar-project-${repository}`}
                  data-selected={String(selected)}
                  className={cn(
                    "flex h-[30px] min-h-[30px] min-w-0 items-center gap-2 rounded-md px-2.5 text-[12px] leading-4",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    selected
                      ? "font-medium text-ra-text"
                      : "text-ra-text-tertiary hover:bg-[var(--oh-surface-raised)] hover:text-ra-text-secondary",
                  )}
                  title={repository}
                >
                  <Folder className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                  <span className="min-w-0 flex-1 truncate">{projectLabel(repository)}</span>
                </Link>
              );
            })
          ) : (
            <p className="px-2.5 py-1 text-[11px] text-ra-text-tertiary">暂无项目</p>
          )}
        </div>
      </section>
    </>
  );

  const footer = (
    <>
      <div className="relative">
        <button
          type="button"
          aria-label="更多导航"
          aria-expanded={moreOpen}
          data-testid="sidebar-more-toggle"
          onClick={() => setMoreOpen((value) => !value)}
          className={cn(
            sidebarNavRowClassName({ collapsed }),
            moreOpen
              ? SIDEBAR_ROW_INTERACTIVE_CLASS.active
              : SIDEBAR_ROW_INTERACTIVE_CLASS.idle,
          )}
        >
          {collapsed ? (
            <SidebarCollapsedIconSlot active={moreOpen}>
              <MoreHorizontal className="h-4 w-4" />
            </SidebarCollapsedIconSlot>
          ) : (
            <>
              <span className={SIDEBAR_ICON_SLOT_CLASS}>
                <MoreHorizontal className="h-4 w-4" />
              </span>
              <span className="min-w-0 flex-1 truncate text-left">更多</span>
              <ChevronDown
                className={cn("h-3.5 w-3.5 transition-transform", moreOpen && "rotate-180")}
                aria-hidden="true"
              />
            </>
          )}
        </button>

        <div
          data-testid="sidebar-more-menu"
          hidden={!moreOpen}
          aria-hidden={!moreOpen}
          className="absolute bottom-[34px] left-0 z-30 w-[205px] rounded-lg border border-ra-border/70 bg-ra-workspace p-1 shadow-[0_10px_30px_rgba(0,0,0,.12)]"
        >
          {SECONDARY_ROUTES.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                data-testid={`sidebar-nav-${item.label}`}
                onClick={() => setMoreOpen(false)}
                className={({ isActive }) =>
                  cn(
                    "flex h-8 items-center gap-2 rounded-md px-2 text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    isActive
                      ? "bg-ra-tertiary text-ra-text"
                      : "text-ra-text-secondary hover:bg-[var(--oh-surface-raised)] hover:text-ra-text",
                  )
                }
              >
                <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                {item.label}
              </NavLink>
            );
          })}
        </div>
      </div>

      <NavLink
        to="/settings"
        data-testid="sidebar-nav-设置"
        className={({ isActive }) =>
          cn(
            sidebarNavRowClassName({ collapsed }),
            isActive
              ? SIDEBAR_ROW_INTERACTIVE_CLASS.active
              : SIDEBAR_ROW_INTERACTIVE_CLASS.idle,
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
          )
        }
        title="设置"
      >
        {({ isActive }) =>
          collapsed ? (
            <SidebarCollapsedIconSlot active={isActive}>
              <Settings className="h-4 w-4" />
            </SidebarCollapsedIconSlot>
          ) : (
            <>
              <span className={SIDEBAR_ICON_SLOT_CLASS}>
                <Settings className="h-4 w-4" />
              </span>
              <span className={sidebarNavLabelClassName(false)}>设置</span>
            </>
          )
        }
      </NavLink>
    </>
  );

  return (
    <AgentCanvasSidebarFrame
      collapsed={collapsed}
      onExpand={() => setCollapsed(false)}
      logo={logo}
      collapseToggle={collapseToggle}
      primaryActions={primaryActions}
      navigation={navigation}
      footer={footer}
    />
  );
}
