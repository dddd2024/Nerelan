import { useTasks } from "@/hooks/use-tasks";
import { TaskInbox } from "@/components/task-inbox";

export function TasksPage() {
  const { data, isLoading, isError, error } = useTasks();
  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-4">
        <h1 className="text-lg font-semibold text-slate-900">Tasks</h1>
        <p className="text-sm text-slate-500">
          Fixture-driven task inbox. No live operations.
        </p>
      </div>
      <TaskInbox tasks={data} isLoading={isLoading} isError={isError} error={error} />
    </div>
  );
}
