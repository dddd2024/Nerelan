import { useQuery } from "@tanstack/react-query";
import { FIXTURE_TASKS } from "@/fixtures/tasks";
import type { Task } from "@/types";

/**
 * Return all fixture tasks via react-query.
 * No real API is called — fixtures only.
 */
export function useTasks() {
  return useQuery<Task[]>({
    queryKey: ["tasks"],
    queryFn: async () => {
      // Simulate async fixture resolution. No network.
      return Promise.resolve(structuredClone(FIXTURE_TASKS) as Task[]);
    },
    staleTime: Infinity,
  });
}
