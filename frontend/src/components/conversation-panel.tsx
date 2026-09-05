import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { AlertCircle, Search, X } from "lucide-react";
import type { Task } from "@/types";
import { useTasks } from "@/hooks/use-tasks";
import { cn } from "@/lib/cn";
import { runStateStyle } from "@/lib/format";

interface ConversationPanelProps {
  open: boolean;
  onClose: () => void;
}

function searchableTaskText(task: Task) {
  return [task.title, task.issueNumber ? `#${task.issueNumber}` : "", task.repository ?? "", task.branch]
    .join(" ")
    .toLocaleLowerCase();
}

function taskMeta(task: Task) {
  return [task.repository, task.branch].filter(Boolean).join(" · ");
}

/** Compact task-search palette backed only by authoritative task read-model data. */
export function ConversationPanel({ open, onClose }: ConversationPanelProps) {
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
    queueMicrotask(() => inputRef.current?.focus());
  }, [open]);

  const filteredTasks = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    const source = tasks ?? [];
    if (!normalized) return source.slice(0, 12);
    return source
      .filter((task) => searchableTaskText(task).includes(normalized))
      .slice(0, 12);
  }, [query, tasks]);

  const handleTaskClick = (taskId: string) => {
    navigate(`/tasks/${taskId}`);
    onClose();
  };

  if (!open) return null;

  return (
    <div
      data-testid="conversation-panel"
      className="fixed inset-0 z-[100] flex items-start justify-center bg-ra-base/55 px-4 pt-[11vh]"
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
        aria-label="搜索任务"
        className="flex max-h-[68vh] w-full max-w-[620px] flex-col overflow-hidden rounded-[14px] border border-ra-border/70 bg-ra-workspace shadow-[0_24px_70px_rgba(0,0,0,.16)]"
      >
        <div className="flex h-12 shrink-0 items-center gap-2 border-b border-ra-border/60 px-3">
          <Search className="h-4 w-4 shrink-0 text-ra-text-tertiary" aria-hidden="true" />
          <label htmlFor="task-search" className="sr-only">搜索任务</label>
          <input
            ref={inputRef}
            id="task-search"
            data-testid="task-search-input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="搜索任务、项目或分支…"
            className="min-w-0 flex-1 bg-transparent text-sm text-ra-text placeholder:text-ra-text-tertiary focus:outline-none"
          />
          <button
            type="button"
            aria-label="关闭任务搜索"
            onClick={onClose}
            className="inline-flex h-7 w-7 items-center justify-center rounded-md text-ra-text-tertiary hover:bg-[var(--oh-surface-raised)] hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        <div className="min-h-[90px] overflow-y-auto py-1.5 custom-scrollbar">
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
            <div data-testid="conversation-panel-list" className="flex flex-col px-1.5">
              {filteredTasks.map((task) => {
                const isActive = location.pathname === `/tasks/${task.id}`;
                return (
                  <button
                    key={task.id}
                    type="button"
                    data-testid={`conversation-task-${task.id}`}
                    onClick={() => handleTaskClick(task.id)}
                    className={cn(
                      "flex min-h-[42px] w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-left",
                      "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                      isActive
                        ? "bg-ra-tertiary text-ra-text"
                        : "text-ra-text-secondary hover:bg-[var(--oh-surface-raised)] hover:text-ra-text",
                    )}
                  >
                    <StatusDot task={task} />
                    <span className="min-w-0 flex-1">
                      <span className="flex min-w-0 items-baseline gap-2">
                        <span className="min-w-0 flex-1 truncate text-[13px] font-medium leading-5">
                          {task.title}
                        </span>
                        {task.issueNumber ? (
                          <span className="shrink-0 text-[10px] tabular-nums text-ra-text-tertiary">
                            #{task.issueNumber}
                          </span>
                        ) : null}
                      </span>
                      {taskMeta(task) ? (
                        <span className="block truncate text-[10px] leading-4 text-ra-text-tertiary">
                          {taskMeta(task)}
                        </span>
                      ) : null}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="border-t border-ra-border/50 px-3 py-1.5 text-[10px] text-ra-text-tertiary">
          {query.trim() ? `${filteredTasks.length} 个匹配结果` : "最近任务"}
        </div>
      </section>
    </div>
  );
}

function StatusDot({ task }: { task: Task }) {
  const state = runStateStyle(task.state);
  const colorMap: Record<string, string> = {
    "bg-emerald-500": "bg-ra-accent",
    "bg-sky-500": "bg-ra-accent",
    "bg-amber-500": "bg-ra-status-starting",
    "bg-orange-500": "bg-ra-status-starting",
    "bg-rose-500": "bg-ra-status-error",
    "bg-violet-500": "bg-ra-text-tertiary",
    "bg-slate-400": "bg-ra-text-tertiary",
  };
  return (
    <span
      className={cn("h-1.5 w-1.5 shrink-0 rounded-full", colorMap[state.dot] ?? "bg-ra-text-tertiary")}
      aria-hidden="true"
    />
  );
}
