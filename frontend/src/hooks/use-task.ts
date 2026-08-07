import { useQuery } from "@tanstack/react-query";
import { findFixtureTask } from "@/fixtures/tasks";
import type { Task } from "@/types";

/**
 * Return a single fixture task by id via react-query.
 */
export function useTask(taskId: string | undefined) {
  return useQuery<Task>({
    queryKey: ["tasks", taskId],
    queryFn: async () => {
      if (!taskId) throw new Error("taskId is required");
      const found = findFixtureTask(taskId);
      if (!found) throw new Error(`Task not found: ${taskId}`);
      return Promise.resolve(structuredClone(found) as Task);
    },
    enabled: Boolean(taskId),
    staleTime: Infinity,
    retry: false,
  });
}
