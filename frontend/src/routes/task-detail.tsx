import { useParams } from "react-router";
import { useTask } from "@/hooks/use-task";
import { TaskDetail } from "@/components/task-detail";
import { cn } from "@/lib/cn";

/**
 * OpenHands ConversationMain / root-layout adaptation.
 * Source: frontend/src/routes/conversation.tsx (tag 1.8.0)
 * — `p-3 md:p-0 flex flex-col h-full gap-3`
 * License: MIT (inherited from OpenHands)
 */
export function TaskDetailPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const { data, isLoading, isError, error } = useTask(taskId);
  return (
    <div
      data-testid="task-detail-page"
      className={cn(
        "p-3 md:p-0 flex flex-col h-full gap-3",
        "bg-transparent rounded-xl",
      )}
    >
      <TaskDetail
        task={data}
        isLoading={isLoading}
        isError={isError}
        error={error}
      />
    </div>
  );
}
