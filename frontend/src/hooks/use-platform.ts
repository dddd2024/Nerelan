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

export function useGoal(
  goalId: string | undefined,
  options: { enabled?: boolean; staleTime?: number; refetchInterval?: number | false } = {},
) {
  const enabled = options.enabled ?? true;
  const goalStaleTime = (globalThis as unknown as { __testUseGoalStaleTime?: number }).__testUseGoalStaleTime ?? options.staleTime ?? 1_500;
  const goalRefetchInterval =
    options.refetchInterval ??
    ((query: { state: { data: unknown } }) => {
      const status = (query.state.data as { status?: string } | undefined)?.status;
      return status === "RUNNING" ? 2_500 : false;
    });
  const result = useQuery({
    queryKey: ["goals", goalId],
    queryFn: () => fetchGoal(goalId ?? ""),
    enabled: Boolean(goalId) && enabled,
    staleTime: goalStaleTime,
    refetchInterval: goalRefetchInterval,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });
  return result;
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
