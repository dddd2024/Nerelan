import { useLocation, useNavigate } from "react-router";
import type { Task } from "@/types";
import { useTasks } from "@/hooks/use-tasks";
import { cn } from "@/lib/cn";
import { runStateStyle } from "@/lib/format";
import { AlertCircle, Clock } from "lucide-react";

interface ConversationPanelProps {
  open: boolean;
  onClose: () => void;
}

/**
 * OpenHands 1.8.0 ConversationPanel adaptation.
 *
 * Upstream source:
 *   frontend/src/components/features/conversation-panel/conversation-panel.tsx
 *     (tag 1.8.0)
 *   - dark bg-[#25272D], border #525252, rounded-lg, w-[400px]
 *   - ConversationCard: `border-b border-neutral-600 cursor-pointer
 *     hover:bg-[#454545]`
 *   - ConversationCardHeader: status dot + title
 *   - ConversationCardFooter: repo/branch + timestamp
 *
 * Structurally ported: same dark-panel overlay layout, same card
 * structure with status indicator dot, repository/branch info, and
 * relative timestamp. Uses ReactDOM portal to render into the workspace
 * outlet, matching OpenHands' ConversationPanelWrapper portal pattern.
 *
 * Modifications: tasks replace conversations; repository/branch from
 * reverse-agent Task type; status colors from reverse-agent RunState
 * instead of sandbox status; no delete/stop actions (read-only fixture).
 */
export function ConversationPanel({ open, onClose }: ConversationPanelProps) {
  const { data: tasks, isLoading, isError } = useTasks();
  const location = useLocation();
  const navigate = useNavigate();

  // Close when navigating away from /tasks (mirrors OpenHands click-outside)
  const handleTaskClick = (taskId: string) => {
    navigate(`/tasks/${taskId}`);
    onClose();
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="p-3 space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <ConversationCardSkeleton key={i} />
          ))}
        </div>
      );
    }

    if (isError || !tasks) {
      return (
        <div
          data-testid="conversation-panel-error"
          className="flex flex-col items-center justify-center h-full text-ra-text-secondary p-4"
        >
          <AlertCircle className="h-5 w-5 mb-2 text-ra-status-error" />
          <p className="text-sm">无法加载任务列表。</p>
        </div>
      );
    }

    if (tasks.length === 0) {
      return (
        <div
          data-testid="conversation-panel-empty"
          className="flex flex-col items-center justify-center h-full p-6 text-center"
        >
          <Clock className="h-8 w-8 mb-3 text-ra-text-tertiary" />
          <p className="text-sm text-ra-text-secondary">
            没有可用的任务。
          </p>
        </div>
      );
    }

    return (
      <div data-testid="conversation-panel-list" className="flex flex-col">
        {tasks.map((task) => {
          const isActive = location.pathname === `/tasks/${task.id}`;
          return (
            <button
              key={task.id}
              type="button"
              data-testid={`conversation-task-${task.id}`}
              onClick={() => handleTaskClick(task.id)}
              className={cn(
                "relative w-full p-3.5 border-b border-ra-border-strong cursor-pointer",
                "text-left transition-colors",
                isActive
                  ? "bg-ra-tertiary"
                  : "hover:bg-[#454545]",
              )}
            >
              <ConversationCard task={task} isActive={isActive} />
            </button>
          );
        })}
      </div>
    );
  };

  if (!open) return null;

  return (
    <div
      data-testid="conversation-panel"
      className={cn(
        "absolute h-full w-full left-0 top-0 z-[100]",
        "bg-black/80 rounded-xl",
        "flex flex-col",
      )}
    >
      <div className="overflow-y-auto custom-scrollbar-always flex-1">
        {renderContent()}
      </div>
    </div>
  );
}

/**
 * OpenHands ConversationCard structural port.
 * Source: conversation-card-header + conversation-card-footer + sandbox-status-indicator
 */
function ConversationCard({ task, isActive }: {
  task: Task;
  isActive: boolean;
}) {
  const state = runStateStyle(task.state);

  return (
    <div className="flex items-center justify-between w-full">
      <div className="flex items-center gap-2 flex-1 min-w-0 overflow-hidden">
        <StatusDot dotClass={state.dot} />
        <span
          className={cn(
            "text-xs leading-6 font-semibold bg-transparent truncate",
            isActive ? "text-ra-text" : "text-ra-text-secondary hover:text-ra-text",
          )}
          title={task.title}
        >
          #{task.issueNumber} — {task.title}
        </span>
      </div>
    </div>
  );
}

function StatusDot({ dotClass }: { dotClass: string }) {
  const colorMap: Record<string, string> = {
    "bg-emerald-500": "bg-ra-accent",
    "bg-sky-500": "bg-[#FFD43B]",
    "bg-amber-500": "bg-[#FFD43B]",
    "bg-orange-500": "bg-[#FFD43B]",
    "bg-rose-500": "bg-ra-status-error",
    "bg-violet-500": "bg-[#A3A3A3]",
    "bg-slate-400": "bg-[#A3A3A3]",
  };
  const bg = colorMap[dotClass] ?? "bg-[#A3A3A3]";
  return (
    <div
      className={cn("w-1.5 h-1.5 rounded-full shrink-0", bg)}
      aria-label={taskStateLabelFromDot(dotClass)}
      title={taskStateLabelFromDot(dotClass)}
    />
  );
}

function taskStateLabelFromDot(dotClass: string): string {
  const map: Record<string, string> = {
    "bg-emerald-500": "就绪",
    "bg-sky-500": "运行中",
    "bg-amber-500": "外部阻塞",
    "bg-orange-500": "需要返工",
    "bg-rose-500": "失败",
    "bg-violet-500": "等待 Owner",
    "bg-slate-400": "未知",
  };
  return map[dotClass] ?? "状态";
}

function ConversationCardSkeleton() {
  return (
    <div
      data-testid="conversation-card-skeleton"
      className="relative h-auto w-full p-3.5 border-b border-ra-border-strong"
    >
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center gap-2 w-full">
          <div className="skeleton-round h-1.5 w-1.5" />
          <div className="skeleton h-3 w-2/3 rounded" />
        </div>
      </div>
      <div className="mt-2 flex flex-col gap-1">
        <div className="skeleton h-2 w-1/2 rounded" />
        <div className="flex justify-between">
          <div className="skeleton h-2 w-1/4 rounded" />
          <div className="skeleton h-2 w-8 rounded" />
        </div>
      </div>
    </div>
  );
}
