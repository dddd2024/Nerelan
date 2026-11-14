import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router";
import {
  Bot,
  ChevronLeft,
  ChevronRight,
  ListChecks,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Target,
  Users,
} from "lucide-react";
import { useAccountPool, useGoals, usePlatformStatus } from "@/hooks/use-platform";
import type { PlatformGoal } from "@/lib/platform-client";
import { NerelanMark, NerelanWordmark } from "@/components/brand-logo";
import { cn } from "@/lib/cn";
import { isCredentialError } from "@/lib/http-errors";
import { GOAL_TONE_DOT, goalState, goalTitle } from "@/lib/goal-view";
import { isPrimaryShortcut, shortcutLabel } from "@/lib/shortcuts";
import { AgentCanvasSidebarFrame } from "@/vendor/agent-canvas-v1.6.1/agent-canvas-sidebar-frame";
import { SidebarCollapsedIconSlot } from "@/vendor/agent-canvas-v1.6.1/sidebar-collapsed-icon-slot";
import {
  SIDEBAR_ICON_SLOT_CLASS,
  SIDEBAR_ROW_INTERACTIVE_CLASS,
  sidebarNavLabelClassName,
  sidebarNavRowClassName,
} from "@/vendor/agent-canvas-v1.6.1/sidebar-layout";

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
  hint?: string;
  onClick: () => void;
}

const COLLAPSE_PREF_KEY = "nerelan.sidebar-collapsed.v1";
const RECENT_GOAL_LIMIT = 12;

/** The issue a goal resolves (its "#1234" title or issues/1234 link), so retries of it show once. */
export function goalIssueKey(goal: Pick<PlatformGoal, "id" | "title" | "objective" | "repository">): string {
  const fromTitle = /^#(\d+)\b/.exec(goal.title ?? "")?.[1];
  const fromLink = /\/issues\/(\d+)\b/.exec(goal.objective ?? "")?.[1];
  const issue = fromTitle ?? fromLink;
  return issue ? `${goal.repository ?? ""}#${issue}` : goal.id;
}

/** Newest goal per issue, newest first. Older goals of the same issue stay in 所有目标. */
export function recentGoals(goals: PlatformGoal[], limit = RECENT_GOAL_LIMIT): PlatformGoal[] {
  const newest: Record<string, PlatformGoal> = {};
  for (const goal of goals) {
    const key = goalIssueKey(goal);
    const kept = newest[key];
    if (!kept || timestamp(goal.updated_at) > timestamp(kept.updated_at)) newest[key] = goal;
  }
  return Object.values(newest).sort((a, b) => timestamp(b.updated_at) - timestamp(a.updated_at)).slice(0, limit);
}

function savedCollapsed(): boolean {
  try {
    return window.localStorage.getItem(COLLAPSE_PREF_KEY) === "1";
  } catch {
    return false;
  }
}

function persistCollapsed(collapsed: boolean) {
  try {
    window.localStorage.setItem(COLLAPSE_PREF_KEY, collapsed ? "1" : "0");
  } catch {
    // Storage may be unavailable; the preference then lasts for this page only.
  }
}

// Goal first, like an agent tool's session list: goals, what waits on the Owner,
// the agents' runs, then the raw tasks. Inbox and roadmap stay one search away.
const PRIMARY_ROUTES = [
  { to: "/goals", label: "目标", icon: Target },
] as const;

/** Everything else lives behind one menu, the way agent chats keep their sidebar to the conversations. */
const MENU_ROUTES = [
  { to: "/approvals", label: "审批", icon: ShieldCheck },
  { to: "/runs", label: "运行记录", icon: Bot },
  { to: "/tasks", label: "任务", icon: ListChecks },
  { to: "/accounts", label: "账户", icon: Users },
  { to: "/settings", label: "设置", icon: Settings },
] as const;

/** One label for the host state; an error never reads as a healthy green dot. */
function hostStatus(coordinator: { enabled: boolean; last_error: string } | undefined, failed: boolean, error?: unknown) {
  if (failed && isCredentialError((error as { status?: number } | null)?.status)) {
    return { tone: "error", label: "请在启动器窗口中使用" } as const;
  }
  if (failed) return { tone: "error", label: coordinator ? "状态待刷新" : "服务未连接" } as const;
  if (coordinator?.last_error) return { tone: "warning", label: "协调器需要处理" } as const;
  return coordinator?.enabled
    ? ({ tone: "ok", label: "协调器在线" } as const)
    : ({ tone: "warning", label: "协调器未运行" } as const);
}

function timestamp(value: string) {
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function SidebarAction({
  collapsed,
  active = false,
  label,
  text = label,
  testId,
  icon,
  hint,
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
          <span className={cn(sidebarNavLabelClassName(false), "flex-1 text-left")}>{text}</span>
          {hint ? (
            <kbd className="shrink-0 font-sans text-[10px] text-ra-text-tertiary">{hint}</kbd>
          ) : null}
        </>
      )}
    </button>
  );
}

function SectionLabel({ children, testId }: { children: ReactNode; testId: string }) {
  /*
   * Section labels are Chinese to match the product surface and their own
   * `aria-label`. They previously read `Recent` / `Projects` while the
   * surrounding section was already labelled 最近任务 / 项目, which broke
   * WCAG 2.5.3 (Label in Name) and mixed scripts in one sidebar.
   * 10px was also below the 11px metadata floor used everywhere else.
   */
  return (
    <div
      data-testid={testId}
      className="px-2.5 pb-1 pt-2 text-[11px] font-medium tracking-[0.04em] text-ra-text-tertiary"
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
  const [collapsed, setCollapsed] = useState(savedCollapsed);
  const location = useLocation();
  const navigate = useNavigate();
  const { data: goals = [], isLoading, isError } = useGoals();
  const platformQuery = usePlatformStatus();
  const activeAlerts = useAccountPool().data?.alerts.active ?? [];
  const urgentAlerts = activeAlerts.filter((alert) => alert.severity !== "info").length;
  const criticalAlert = activeAlerts.some((alert) => alert.severity === "critical");
  const host = hostStatus(platformQuery.data?.coordinator, platformQuery.isError, platformQuery.error);
  const instance = platformQuery.data?.instance;
  // Only an acceptance instance needs saying: its tasks are not the real ones.
  const instanceLabel = instance?.kind === "acceptance" ? `验收实例（独立任务数据） · ${instance.id}` : "";

  useEffect(() => {
    onConversationPanelClose();
  }, [location.pathname, onConversationPanelClose]);

  useEffect(() => {
    persistCollapsed(collapsed);
  }, [collapsed]);

  useEffect(() => {
    const toggle = (event: KeyboardEvent) => {
      if (isPrimaryShortcut(event, "b")) {
        event.preventDefault();
        setCollapsed((value) => !value);
      }
    };
    window.addEventListener("keydown", toggle);
    return () => window.removeEventListener("keydown", toggle);
  }, []);

  const recent = useMemo(() => recentGoals(goals), [goals]);
  const [menuOpen, setMenuOpen] = useState(false);

  const logo = (
    <button
      type="button"
      aria-label="Nerelan"
      data-testid="sidebar-logo"
      onClick={() => navigate("/")}
      className={cn(
        "flex h-9 w-full items-center text-ra-text",
        collapsed ? "justify-center" : "justify-start px-2.5",
      )}
      title="Nerelan"
    >
      {collapsed ? (
        <NerelanMark className="h-[22px] w-[21px]" />
      ) : (
        <NerelanWordmark className="h-[19px] w-[106px]" />
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
      className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-ra-text-secondary hover:bg-ra-tertiary hover:text-ra-text"
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
        label="新建目标"
        text="新建目标"
        testId="new-goal-button"
        icon={<Plus className="h-4 w-4" />}
        onClick={onNewTask}
      />
      <SidebarAction
        collapsed={collapsed}
        active={conversationPanelOpen}
        label={conversationPanelOpen ? "关闭搜索" : "打开搜索"}
        text="搜索"
        hint={shortcutLabel("K")}
        testId="toggle-conversation-panel"
        icon={<Search className="h-4 w-4" />}
        onClick={
          conversationPanelOpen
            ? onConversationPanelClose
            : onOpenConversationPanel
        }
      />
      <div className="mt-2 flex flex-col gap-0.5" role="group" aria-label="主导航">
        {PRIMARY_ROUTES.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              title={item.label}
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
            >
              {({ isActive }) =>
                collapsed ? (
                  <SidebarCollapsedIconSlot active={isActive}>
                    <Icon className="h-4 w-4" />
                  </SidebarCollapsedIconSlot>
                ) : (
                  <>
                    <span className={SIDEBAR_ICON_SLOT_CLASS}>
                      <Icon className="h-4 w-4" />
                    </span>
                    <span className={cn(sidebarNavLabelClassName(false), "flex-1")}>{item.label}</span>
                  </>
                )
              }
            </NavLink>
          );
        })}
      </div>
    </>
  );

  const navigation = collapsed ? null : (
    <>
      <Link to="/" data-testid="sidebar-nav-首页" className="sr-only">
        首页
      </Link>

      <section aria-label="最近目标">
        <SectionLabel testId="sidebar-section-recent">最近目标</SectionLabel>
        {isError && (
          <p role="alert" className="px-2.5 py-1 text-[11px] text-ra-text-secondary">
            最近目标读取失败，请检查服务连接
          </p>
        )}
        <div className="flex flex-col gap-0.5">
          {recent.length > 0 ? (
            recent.map((goal) => {
              const selected = location.pathname === "/" && new URLSearchParams(location.search).get("goal") === goal.id;
              return (
                <div key={goal.id} className="relative min-w-0">
                <Link
                  to={`/?goal=${encodeURIComponent(goal.id)}`}
                  data-testid={`sidebar-recent-goal-${goal.id}`}
                  data-selected={String(selected)}
                  className={cn(
                    "flex h-[30px] min-h-[30px] min-w-0 items-center gap-2 rounded-md px-2.5 text-[13px] leading-4",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    selected
                      ? "bg-ra-tertiary text-ra-text"
                      : "text-ra-text-secondary hover:bg-ra-tertiary hover:text-ra-text",
                  )}
                  title={`${goalTitle(goal, 300)} · ${goalState(goal).label}`}
                >
                  <span
                    className={cn(
                      "h-1.5 w-1.5 shrink-0 rounded-full",
                      GOAL_TONE_DOT[goalState(goal).tone],
                      goalState(goal).key === "running" && "ra-pulse",
                    )}
                    aria-hidden="true"
                  />
                  <span className="min-w-0 flex-1 truncate">{goalTitle(goal)}</span>
                </Link>
                </div>
              );
            })
          ) : !isError ? (
            <p role="status" className="px-2.5 py-1 text-[11px] text-ra-text-tertiary">
              {isLoading ? "正在加载最近目标…" : "暂无最近目标"}
            </p>
          ) : null}
        </div>
      </section>

    </>
  );

  const menuActive = MENU_ROUTES.some((item) => location.pathname.startsWith(item.to));
  const footer = (
    <>
      {!collapsed && (platformQuery.data || platformQuery.isError) && host.tone !== "ok" ? (
        <div
          data-testid="sidebar-host-status"
          data-tone={host.tone}
          className="flex min-h-[30px] items-center gap-2 px-2.5 text-[11px] text-ra-text-tertiary"
          title={platformQuery.data?.coordinator.last_error || undefined}
        >
          <span
            aria-hidden="true"
            className={cn(
              "h-1.5 w-1.5 shrink-0 rounded-full",
              host.tone === "error" && "bg-ra-status-error",
              host.tone === "warning" && "bg-ra-status-warning",
            )}
          />
          <span className="shrink-0">{host.label}</span>
          {instanceLabel && (
            <span data-testid="sidebar-instance" title={instanceLabel} className="min-w-0 flex-1 truncate text-right">
              {instanceLabel}
            </span>
          )}
        </div>
      ) : null}

      <details className="group relative" data-testid="sidebar-menu" open={menuOpen}
        onToggle={(event) => setMenuOpen((event.currentTarget as HTMLDetailsElement).open)}>
        <summary
          className={cn(
            sidebarNavRowClassName({ collapsed }),
            menuActive ? SIDEBAR_ROW_INTERACTIVE_CLASS.active : SIDEBAR_ROW_INTERACTIVE_CLASS.idle,
            "cursor-pointer list-none focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent [&::-webkit-details-marker]:hidden",
          )}
          title="更多"
          aria-label={urgentAlerts > 0 ? `更多（${urgentAlerts} 条账户告警）` : "更多"}
        >
          {collapsed ? (
            <SidebarCollapsedIconSlot active={menuActive}>
              <Settings className="h-4 w-4" />
            </SidebarCollapsedIconSlot>
          ) : (
            <>
              <span className={SIDEBAR_ICON_SLOT_CLASS}>
                <Settings className="h-4 w-4" />
              </span>
              <span className={cn(sidebarNavLabelClassName(false), "flex-1")}>更多</span>
            </>
          )}
          {urgentAlerts > 0 && (
            <span
              data-testid="sidebar-alert-count"
              aria-hidden="true"
              className={cn("h-1.5 w-1.5 shrink-0 rounded-full", criticalAlert ? "bg-ra-status-error" : "bg-ra-status-warning",
                collapsed && "absolute right-3 top-2")}
            />
          )}
        </summary>
        <nav aria-label="更多" className="absolute bottom-full left-0 z-20 mb-1 w-52 rounded-xl border border-ra-border bg-ra-base p-1 shadow-[var(--ra-shadow-2)]">
          {MENU_ROUTES.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                data-testid={`sidebar-nav-${item.label}`}
                onClick={() => setMenuOpen(false)}
                className={({ isActive }) => cn(
                  "flex h-8 items-center gap-2.5 rounded-lg px-2.5 text-[13px] focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                  isActive ? "bg-ra-tertiary text-ra-text" : "text-ra-text-secondary hover:bg-ra-tertiary hover:text-ra-text",
                )}
              >
                <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                <span className="flex-1">{item.label}</span>
                {item.to === "/accounts" && urgentAlerts > 0 && (
                  <span className={cn("text-[11px] tabular-nums", criticalAlert ? "text-ra-status-error" : "text-ra-status-warning")}
                    aria-label={`${urgentAlerts} 条账户告警`}>
                    {urgentAlerts}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>
      </details>
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
