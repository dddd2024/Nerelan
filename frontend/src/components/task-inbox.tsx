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
        <LoadingState label="Loading tasks…" />
      </div>
    );
  }
  if (isError) {
    return (
      <div data-testid="task-inbox">
        <ErrorState title="Failed to load tasks" error={error} />
      </div>
    );
  }
  if (!tasks || tasks.length === 0) {
    return (
      <div data-testid="task-inbox">
        <EmptyState
          title="No tasks"
          description="Tasks created from approved work items will appear here."
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
        title="New Task"
        testId="section-new-task"
        description="Create a task from an approved work item."
      >
        <button
          type="button"
          className="rounded-md border border-dashed border-slate-300 px-4 py-3 text-sm text-slate-500 hover:border-slate-400 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
        >
          + New task
        </button>
      </Section>
      <Section
        title="Needs Owner Attention"
        testId="section-needs-attention"
        count={needsAttention.length}
      >
        <Cards tasks={needsAttention} />
      </Section>
      <Section title="Running" testId="section-running" count={running.length}>
        <Cards tasks={running} />
      </Section>
      <Section title="Recent Tasks" testId="section-recent" count={recent.length}>
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
    return <p className="text-xs text-slate-400">None.</p>;
  }
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      {tasks.map((t) => (
        <TaskCard key={t.id} task={t} />
      ))}
    </div>
  );
}
