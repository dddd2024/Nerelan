import { useEffect, useMemo, useRef, useState, type ComponentType, type SVGProps } from "react";
import { useLocation, useNavigate } from "react-router";
import { Command } from "cmdk";
import {
  AlertCircle,
  Bot,
  Flag,
  Gauge,
  Home,
  Inbox,
  ListChecks,
  Map,
  Moon,
  Plus,
  Search,
  Settings,
  Sun,
  Users,
  X,
} from "lucide-react";
import type { Task } from "@/types";
import { useTasks } from "@/hooks/use-tasks";
import { cn } from "@/lib/cn";
import { displayTitle } from "@/lib/display-title";
import { runStateStyle } from "@/lib/format";
import { readAppearance, setAppearance } from "@/lib/theme";

interface ConversationPanelProps {
  open: boolean;
  onClose: () => void;
  /** Absent where no composer is mounted, in which case the command is hidden. */
  onNewTask?: () => void;
}

interface PaletteCommand {
  id: string;
  label: string;
  keywords: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  run: () => void;
}

const ROUTES = [
  { to: "/", label: "首页", keywords: "home new goal 目标", icon: Home },
  { to: "/tasks", label: "任务", keywords: "tasks", icon: ListChecks },
  { to: "/goals", label: "目标", keywords: "goals", icon: Flag },
  { to: "/inbox", label: "收件箱", keywords: "inbox review 审查", icon: Inbox },
  { to: "/roadmap", label: "路线图", keywords: "roadmap", icon: Map },
  { to: "/runs", label: "Agent 运行", keywords: "runs agent", icon: Bot },
  { to: "/accounts", label: "账户", keywords: "accounts pool quota alerts 告警 额度", icon: Users },
  { to: "/settings/usage", label: "用量与额度", keywords: "usage quota", icon: Gauge },
  { to: "/settings", label: "设置", keywords: "settings", icon: Settings },
] as const;

function searchableTaskText(task: Task) {
  return [task.title, task.issueNumber ? `#${task.issueNumber}` : "", task.repository ?? "", task.branch]
    .join(" ")
    .toLocaleLowerCase();
}

function taskMeta(task: Task) {
  return [task.repository, task.branch].filter(Boolean).join(" · ");
}

function resolvedDark() {
  const { mode } = readAppearance();
  if (mode !== "system") return mode === "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

/**
 * Global command palette (Ctrl/Cmd+K), built on cmdk for list semantics and
 * keyboard navigation. Filtering stays here on purpose: task search must be an
 * exact substring match over authoritative task data, and the fuzzy scorer in
 * cmdk would match `#0` against unrelated tasks. It holds no state of its own.
 */
export function ConversationPanel({ open, onClose, onNewTask }: ConversationPanelProps) {
  const { data: tasks, isLoading, isError } = useTasks();
  const location = useLocation();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!open) {
      setQuery("");
      return;
    }
    // Hand focus back on close: the palette can open in the middle of typing.
    const previous = document.activeElement;
    queueMicrotask(() => inputRef.current?.focus());
    return () => {
      if (previous instanceof HTMLElement && previous.isConnected) previous.focus();
    };
  }, [open]);

  const normalized = query.trim().toLocaleLowerCase();

  const filteredTasks = useMemo(() => {
    const source = tasks ?? [];
    if (!normalized) return source.slice(0, 8);
    return source
      .filter((task) => searchableTaskText(task).includes(normalized))
      .slice(0, 12);
  }, [normalized, tasks]);

  const commands = useMemo<PaletteCommand[]>(() => {
    const dark = open && resolvedDark();
    const all: PaletteCommand[] = [
      ...(onNewTask
        ? [{ id: "new-task", label: "新建任务", keywords: "new task create", icon: Plus, run: onNewTask }]
        : []),
      ...ROUTES.map((route) => ({
        id: `go-${route.to}`,
        label: route.label,
        keywords: route.keywords,
        icon: route.icon,
        run: () => navigate(route.to),
      })),
      {
        id: "toggle-theme",
        label: dark ? "切换到浅色外观" : "切换到深色外观",
        keywords: "theme appearance dark light 主题",
        icon: dark ? Sun : Moon,
        run: () => {
          const current = readAppearance();
          setAppearance({ ...current, mode: dark ? "light" : "dark" });
        },
      },
    ];
    if (!normalized) return all;
    return all.filter((command) =>
      `${command.label} ${command.keywords}`.toLocaleLowerCase().includes(normalized),
    );
  }, [navigate, normalized, onNewTask, open]);

  const handleTaskClick = (taskId: string) => {
    navigate(`/tasks/${taskId}`);
    onClose();
  };

  if (!open) return null;

  return (
    <div
      data-testid="conversation-panel"
      className="fixed inset-0 z-[100] flex items-start justify-center bg-black/40 px-4 pt-[12vh]"
      onMouseDown={(event) => {
        if (event.currentTarget === event.target) onClose();
      }}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          onClose();
        }
      }}
      role="presentation"
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-label="命令面板"
        className="flex max-h-[64vh] w-full max-w-[640px] flex-col overflow-hidden rounded-xl border border-ra-border bg-ra-workspace shadow-[var(--ra-shadow-3)]"
      >
        <Command shouldFilter={false} loop label="搜索任务或命令" className="flex min-h-0 flex-1 flex-col">
          <div className="flex h-12 shrink-0 items-center gap-2 border-b border-ra-border px-3">
            <Search className="h-4 w-4 shrink-0 text-ra-text-tertiary" aria-hidden="true" />
            <Command.Input
              ref={inputRef}
              data-testid="task-search-input"
              value={query}
              onValueChange={setQuery}
              placeholder="搜索任务、项目、分支或命令…"
              className="min-w-0 flex-1 bg-transparent text-sm text-ra-text placeholder:text-ra-text-tertiary focus:outline-none"
            />
            <button
              type="button"
              aria-label="关闭任务搜索"
              onClick={onClose}
              className="inline-flex h-7 w-7 items-center justify-center rounded-md text-ra-text-tertiary hover:bg-ra-tertiary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>

          <Command.List label="命令与任务" className="min-h-[90px] overflow-y-auto px-1.5 py-1.5 custom-scrollbar">
            {commands.length > 0 ? (
              <Command.Group heading="命令">
                {commands.map((command) => {
                  const Icon = command.icon;
                  return (
                    <Command.Item
                      key={command.id}
                      value={command.id}
                      data-testid={`palette-command-${command.id}`}
                      onSelect={() => {
                        onClose();
                        command.run();
                      }}
                      className="flex h-9 cursor-pointer items-center gap-2.5 rounded-md px-2.5 text-[13px] text-ra-text-secondary"
                    >
                      <Icon className="h-4 w-4 shrink-0 text-ra-text-tertiary" aria-hidden="true" />
                      {command.label}
                    </Command.Item>
                  );
                })}
              </Command.Group>
            ) : null}

            {isLoading ? (
              <div className="px-4 py-8 text-center text-xs text-ra-text-tertiary">正在加载任务…</div>
            ) : isError || !tasks ? (
              <div
                data-testid="conversation-panel-error"
                className="flex items-center justify-center gap-2 px-4 py-8 text-xs text-ra-status-error"
              >
                <AlertCircle className="h-4 w-4" aria-hidden="true" />
                无法加载任务列表。
              </div>
            ) : filteredTasks.length === 0 ? (
              <div
                data-testid="conversation-panel-empty"
                className="px-4 py-8 text-center text-xs text-ra-text-tertiary"
              >
                没有匹配的任务。
              </div>
            ) : (
              <Command.Group heading="任务" data-testid="conversation-panel-list">
                {filteredTasks.map((task) => {
                  const isActive = location.pathname === `/tasks/${task.id}`;
                  return (
                    <Command.Item
                      key={task.id}
                      value={`task-${task.id}`}
                      data-testid={`conversation-task-${task.id}`}
                      onSelect={() => handleTaskClick(task.id)}
                      className={cn(
                        "flex min-h-[42px] w-full cursor-pointer items-center gap-2.5 rounded-md px-2.5 py-1.5 text-left",
                        isActive ? "text-ra-text" : "text-ra-text-secondary",
                      )}
                    >
                      <StatusDot task={task} />
                      <span className="min-w-0 flex-1">
                        <span className="flex min-w-0 items-baseline gap-2">
                          <span className="min-w-0 flex-1 truncate text-[13px] font-medium leading-5">
                            {displayTitle(task.title)}
                          </span>
                          {task.issueNumber ? (
                            <span className="shrink-0 text-[11px] tabular-nums text-ra-text-tertiary">
                              #{task.issueNumber}
                            </span>
                          ) : null}
                        </span>
                        {taskMeta(task) ? (
                          <span className="block truncate text-[11px] leading-4 text-ra-text-tertiary">
                            {taskMeta(task)}
                          </span>
                        ) : null}
                      </span>
                    </Command.Item>
                  );
                })}
              </Command.Group>
            )}
          </Command.List>

          <div className="flex items-center justify-between border-t border-ra-border px-3 py-1.5 text-[11px] text-ra-text-tertiary">
            <span>{normalized ? `${filteredTasks.length} 个匹配任务` : "最近任务"}</span>
            <span>↑↓ 选择 · Enter 打开 · Esc 关闭</span>
          </div>
        </Command>
      </section>
    </div>
  );
}

function StatusDot({ task }: { task: Task }) {
  const state = runStateStyle(task.state);
  /*
   * This used to translate the *old* palette dot classes (`bg-emerald-500`,
   * `bg-rose-500`, …) into tokens. `runStateStyle` no longer emits those, so
   * every lookup missed the map and fell through to the grey fallback — the
   * search panel rendered every task with the same dot colour.
   */
  return (
    <span
      className={cn("h-1.5 w-1.5 shrink-0 rounded-full", state.dot)}
      aria-hidden="true"
    />
  );
}
