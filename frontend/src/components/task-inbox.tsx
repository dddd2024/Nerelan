import type { Task } from "@/types";
import { TaskCard } from "@/components/task-card";
import { LoadingState } from "@/components/loading-state";
import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";
import { cn } from "@/lib/cn";
import { Clock, PlayCircle, Flag } from "lucide-react";

interface TaskInboxProps {
  tasks: Task[] | undefined;
  isLoading: boolean;
  isError: boolean;
  error?: unknown;
}

/**
 * OpenHands HomeScreen / RecentConversations adaptation.
 *
 * Upstream sources:
 *   frontend/src/routes/home.tsx (tag 1.8.0)
 *   — `px-0 pt-4 bg-transparent h-full flex flex-col
 *      rounded-xl lg:px-[42px] lg:pt-[42px]`
 *   frontend/src/components/features/home/recent-conversations/
 *     recent-conversations.tsx
 *   — section with h3 header, conversation list, skeleton
 *   frontend/src/components/features/conversation-panel/
 *     conversation-panel.tsx
 *   — conversation cards with border-b, hover:bg-[#454545]
 *
 * Structurally ported: section-based list with category headers
 * ("需要 Owner 关注", "运行中", "最近任务"), each containing compact
 * conversation-card-style items. Loading shows skeleton cards.
 * Empty state uses icon + text pattern from RecentConversations.
 * Error state uses AlertCircle with danger color (#FF684E).
 *
 * Modifications: reverse-agent task states replace sandbox statuses;
 * categories map to reverse-agent RunState groups.
 * License: MIT (inherited from OpenHands)
 */
export function TaskInbox({ tasks, isLoading, isError, error }: TaskInboxProps) {
  if (isLoading) {
    return (
      <div data-testid="task-inbox">
        <LoadingState label="加载任务中…" />
      </div>
    );
  }

  if (isError) {
    return (
      <div data-testid="task-inbox">
        <ErrorState title="任务加载失败" error={error} />
      </div>
    );
  }

  if (!tasks || tasks.length === 0) {
    return (
      <div data-testid="task-inbox">
        <EmptyState
          title="未找到任务"
          description="从已批准工作项创建的任务将显示在此处。"
          icon={<Clock className="h-6 w-6" />}
        />
      </div>
    );
  }

  const needsAttention = tasks.filter(
    (t) => t.state === "WAITING_FOR_OWNER" || t.state === "READY_FOR_HUMAN",
  );
  const running = tasks.filter((t) => t.state === "RUNNING");
  const recent = tasks.filter(
    (t) =>
      t.state !== "WAITING_FOR_OWNER" &&
      t.state !== "READY_FOR_HUMAN" &&
      t.state !== "RUNNING",
  );

  return (
    <div data-testid="task-inbox" className="space-y-6">
      <Section
        title="需要 Owner 关注"
        testId="section-needs-attention"
        icon={<Flag className="h-4 w-4 text-ra-accent" />}
        count={needsAttention.length}
      >
        <Cards tasks={needsAttention} />
      </Section>
      <Section
        title="运行中"
        testId="section-running"
        icon={<PlayCircle className="h-4 w-4 text-[#FFD43B]" />}
        count={running.length}
      >
        <Cards tasks={running} />
      </Section>
      <Section
        title="最近任务"
        testId="section-recent"
        icon={<Clock className="h-4 w-4 text-ra-text-tertiary" />}
        count={recent.length}
      >
        <Cards tasks={recent} />
      </Section>
    </div>
  );
}

function Section({
  title,
  count,
  icon,
  testId,
  children,
}: {
  title: string;
  count?: number;
  icon?: React.ReactNode;
  testId: string;
  children: React.ReactNode;
}) {
  return (
    <section data-testid={testId} aria-label={title} className="flex flex-col">
      <div className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-ra-text-secondary">
        {icon}
        <h2>{title}</h2>
        {typeof count === "number" ? (
          <span className="text-ra-text-tertiary">({count})</span>
        ) : null}
      </div>
      <div
        className={cn(
          "rounded-xl border border-ra-border bg-ra-sidebar overflow-hidden",
        )}
      >
        {children}
      </div>
    </section>
  );
}

function Cards({ tasks }: { tasks: Task[] }) {
  if (tasks.length === 0) {
    return (
      <p className="px-4 py-3 text-xs text-ra-text-tertiary" data-testid="no-tasks">
        无。
      </p>
    );
  }
  return tasks.map((t) => (
    <TaskCard key={t.id} task={t} />
  ));
}
