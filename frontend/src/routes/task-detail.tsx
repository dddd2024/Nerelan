import { useParams } from "react-router";
import { useTask } from "@/hooks/use-task";
import { TaskDetail } from "@/components/task-detail";

export function TaskDetailPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const { data, isLoading, isError, error } = useTask(taskId);
  return (
    <div className="mx-auto max-w-5xl">
      <TaskDetail
        task={data}
        isLoading={isLoading}
        isError={isError}
        error={error}
      />
    </div>
  );
}
