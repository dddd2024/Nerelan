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
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });
}

export function useGoals() {
  return useQuery({
    queryKey: ["goals"],
    queryFn: fetchGoals,
    staleTime: 2_000,
    refetchInterval: 5_000,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });
}

export function useGoal(goalId: string | undefined) {
  return useQuery({
    queryKey: ["goals", goalId],
    queryFn: () => fetchGoal(goalId ?? ""),
    enabled: Boolean(goalId),
    staleTime: 1_500,
    refetchInterval: (query) => {
      const status = (query.state.data as { status?: string } | undefined)?.status;
      return status === "RUNNING" ? 2_500 : false;
    },
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });
}

export function useStartGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: StartGoalInput) => startGoal(input),
    onSuccess: (goal) => {
      queryClient.setQueryData(["goals", goal.id], goal);
      void queryClient.setQueryData(["goals"], (previous: unknown) => {
        const list = Array.isArray(previous) ? previous : [];
        const existing = list.findIndex((entry) => entry && entry.id === goal.id);
        if (existing >= 0) {
          return list.map((entry, index) => (index === existing ? goal : entry));
        }
        return [goal, ...list];
      });
      void queryClient.invalidateQueries({ queryKey: ["goals"] });
      void queryClient.invalidateQueries({ queryKey: ["goals", goal.id] });
      void queryClient.invalidateQueries({ queryKey: ["platform", "status"] });
    },
  });
}
