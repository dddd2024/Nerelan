import { Link } from "react-router";
import { useTasks } from "@/hooks/use-tasks";
import { TaskCard } from "@/components/task-card";
import { LoadingState } from "@/components/loading-state";
import { EmptyState } from "@/components/empty-state";
import { ShieldCheck } from "lucide-react";

export function ApprovalsPage() {
  const { data, isLoading } = useTasks();
  const tasks = data?.filter(
    (t) => t.state === "WAITING_FOR_OWNER" || t.state === "READY_FOR_HUMAN",
  );

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-4">
        <h1 className="text-lg font-semibold text-slate-900">审批</h1>
        <p className="text-sm text-slate-500">
          等待 Owner 审查的任务。合并仍由人工控制。
        </p>
      </div>
      {isLoading ? (
        <LoadingState />
      ) : tasks && tasks.length > 0 ? (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {tasks.map((t) => (
            <TaskCard key={t.id} task={t} />
          ))}
        </div>
      ) : (
        <EmptyState
          title="暂无待审批项"
          description="当前没有需要 Owner 关注的任务。"
          icon={<ShieldCheck className="h-6 w-6" />}
          action={
            <Link
              to="/tasks"
              className="text-sm text-slate-500 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
            >
              前往任务
            </Link>
          }
        />
      )}
    </div>
  );
}
