import type { Task } from "@/types";
import { TaskCard } from "@/components/task-card";
import { LoadingState } from "@/components/loading-state";
import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";
import { Inbox } from "lucide-react";

interface TaskInboxProps {
  tasks: Task[] | undefined;
  isLoading: boolean;
  isError: boolean;
  error?: unknown;
}

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
          icon={<Inbox className="h-6 w-6" />}
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
        title="新建任务"
        testId="section-new-task"
        description="从已批准工作项创建任务。"
      >
        <button
          type="button"
          className="rounded-md border border-dashed border-slate-300 px-4 py-3 text-sm text-slate-500 hover:border-slate-400 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
        >
          + 新建任务
        </button>
      </Section>
      <Section
        title="需要 Owner 关注"
        testId="section-needs-attention"
        count={needsAttention.length}
      >
        <Cards tasks={needsAttention} />
      </Section>
      <Section title="运行中" testId="section-running" count={running.length}>
        <Cards tasks={running} />
      </Section>
      <Section title="最近任务" testId="section-recent" count={recent.length}>
        <Cards tasks={recent} />
      </Section>
    </div>
  );
}

function Section({
  title,
  count,
  description,
  testId,
  children,
}: {
  title: string;
  count?: number;
  description?: string;
  testId: string;
  children: React.ReactNode;
}) {
  return (
    <section data-testid={testId} aria-label={title}>
      <div className="mb-2 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold text-slate-700">{title}</h2>
        {typeof count === "number" ? (
          <span className="text-xs text-slate-400">{count}</span>
        ) : null}
      </div>
      {description ? <p className="mb-2 text-xs text-slate-500">{description}</p> : null}
      {children}
    </section>
  );
}

function Cards({ tasks }: { tasks: Task[] }) {
  if (tasks.length === 0) {
    return <p className="text-xs text-slate-400">无。</p>;
  }
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      {tasks.map((t) => (
        <TaskCard key={t.id} task={t} />
      ))}
    </div>
  );
}
