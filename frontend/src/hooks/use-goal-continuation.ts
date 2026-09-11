import { useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query";
import {
  approveExistingGoal,
  launchExistingGoal,
  planExistingGoal,
} from "@/lib/goal-continuation-operation";
import type { PlatformGoal } from "@/lib/platform-client";

function writeGoalToCache(
  queryClient: QueryClient,
  goal: PlatformGoal,
) {
  queryClient.setQueryData(["goals", goal.id], goal);
  queryClient.setQueryData(["goals"], (previous: unknown) => {
    const list = Array.isArray(previous) ? (previous as PlatformGoal[]) : [];
    const found = list.some((entry) => entry.id === goal.id);
    if (!found) return [goal, ...list];
    return list.map((entry) => (entry.id === goal.id ? goal : entry));
  });
  void queryClient.invalidateQueries({ queryKey: ["platform", "status"] });
}

function invalidateGoal(
  queryClient: QueryClient,
  goalId: string,
) {
  void queryClient.invalidateQueries({ queryKey: ["goals"] });
  void queryClient.invalidateQueries({ queryKey: ["goals", goalId] });
  void queryClient.invalidateQueries({ queryKey: ["platform", "status"] });
}

export function usePlanExistingGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (goal: PlatformGoal) => planExistingGoal(goal),
    onSuccess: (goal) => writeGoalToCache(queryClient, goal),
    onError: (_error, goal) => invalidateGoal(queryClient, goal.id),
  });
}

export function useApproveExistingGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (goal: PlatformGoal) => approveExistingGoal(goal),
    onSuccess: (goal) => writeGoalToCache(queryClient, goal),
    onError: (_error, goal) => invalidateGoal(queryClient, goal.id),
  });
}

export function useLaunchExistingGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      goal,
      autonomyHours,
    }: {
      goal: PlatformGoal;
      autonomyHours: number;
    }) => launchExistingGoal(goal, autonomyHours),
    onSuccess: (goal) => writeGoalToCache(queryClient, goal),
    onError: (_error, variables) =>
      invalidateGoal(queryClient, variables.goal.id),
  });
}
