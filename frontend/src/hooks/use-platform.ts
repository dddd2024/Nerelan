import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchGoal,
  fetchGoals,
  fetchPlatformStatus,
  startGoal,
  type StartGoalInput,
} from "@/lib/platform-client";

function useReconnect(query: { refetch: () => Promise<unknown> }) {
  useEffect(() => {
    const refetch = () => void query.refetch();
    globalThis.addEventListener("visibilitychange", refetch);
    globalThis.addEventListener("online", refetch);
    return () => {
      globalThis.removeEventListener("visibilitychange", refetch);
      globalThis.removeEventListener("online", refetch);
    };
  }, [query]);
}

export function usePlatformStatus() {
  const query = useQuery({
    queryKey: ["platform", "status"],
    queryFn: fetchPlatformStatus,
    staleTime: 3_000,
    refetchInterval: 5_000,
  });
  useReconnect(query);
  return query;
}

export function useGoals() {
  const query = useQuery({
    queryKey: ["goals"],
    queryFn: fetchGoals,
    staleTime: 2_000,
    refetchInterval: 5_000,
  });
  useReconnect(query);
  return query;
}

export function useGoal(goalId: string | undefined, options: { enabled?: boolean } = {}) {
  const enabled = options.enabled ?? true;
  const query = useQuery({
    queryKey: ["goals", goalId],
    queryFn: () => fetchGoal(goalId ?? ""),
    enabled: Boolean(goalId) && enabled,
    staleTime: 1_500,
    refetchInterval: 3_000,
  });
  if (enabled) useReconnect(query);
  return query;
}

export function useStartGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: StartGoalInput) => startGoal(input),
    onSuccess: (goal) => {
      queryClient.setQueryData(["goals", goal.id], goal);
      void queryClient.invalidateQueries({ queryKey: ["goals"] });
      void queryClient.invalidateQueries({ queryKey: ["goals", goal.id] });
      void queryClient.invalidateQueries({ queryKey: ["platform", "status"] });
    },
  });
}
