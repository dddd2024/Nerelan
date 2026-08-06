import { useTasks } from "@/hooks/use-tasks";
import { TaskInbox } from "@/components/task-inbox";
import { cn } from "@/lib/cn";

/**
 * OpenHands HomeScreen adaptation.
 * Source: frontend/src/routes/home.tsx (tag 1.8.0)
 * — `px-0 pt-4 bg-transparent h-full flex flex-col
 *    rounded-xl lg:px-[42px] lg:pt-[42px]`
 * License: MIT (inherited from OpenHands)
 */
export function TasksPage() {
  const { data, isLoading, isError, error } = useTasks();
  return (
    <div
      data-testid="tasks-page"
      className={cn(
        "px-0 pt-4 bg-transparent h-full flex flex-col",
        "rounded-xl lg:px-[42px] lg:pt-[42px] custom-scrollbar-always",
      )}
    >
      <div className="flex flex-col flex-1 min-h-0">
        <TaskInbox
          tasks={data}
          isLoading={isLoading}
          isError={isError}
          error={error}
        />
      </div>
    </div>
  );
}
