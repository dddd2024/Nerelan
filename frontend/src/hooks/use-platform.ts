import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchGoal,
  fetchGoals,
  fetchPlatformStatus,
  startGoal,
  type StartGoalInput,
} from "@/lib/platform-client";

export function usePlatformStatus() {
  return useQuery({
    queryKey: ["platform", "status"],
    queryFn: fetchPlatformStatus,
    staleTime: 3_000,
    refetchInterval: 5_000,
  });
}

export function useGoals() {
  return useQuery({
    queryKey: ["goals"],
    queryFn: fetchGoals,
    staleTime: 2_000,
    refetchInterval: 5_000,
  });
}

export function useGoal(goalId: string | undefined) {
  return useQuery({
    queryKey: ["goals", goalId],
    queryFn: () => fetchGoal(goalId ?? ""),
    enabled: Boolean(goalId),
    staleTime: 2_000,
    refetchInterval: 4_000,
  });
}

export function useStartGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: StartGoalInput) => startGoal(input),
    onSuccess: (goal) => {
      queryClient.setQueryData(["goals", goal.id], goal);
      void queryClient.invalidateQueries({ queryKey: ["goals"] });
      void queryClient.invalidateQueries({ queryKey: ["platform", "status"] });
    },
  });
}
