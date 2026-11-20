import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchGoal,
  PlatformClientError,
  fetchGoalTimeline,
  retryGoalStep,
  fetchGoals,
  fetchPlatformStatus,
  fetchAccountPool,
  fetchApprovedPolicyIfConfigured,
  draftQuickStart,
  preflightOwnerWindow,
  type QuickStartDraftInput,
  type OwnerWindowPreflightRequest,
  type PlatformGoalTimeline,
} from "@/lib/platform-client";
import {
  startGoal,
  createGoalDraft,
  type StartGoalInput,
} from "@/lib/goal-start-operation";

export function useApprovedPolicy() {
  return useQuery({
    queryKey: ["platform", "approved-policy"], queryFn: fetchApprovedPolicyIfConfigured,
    enabled: import.meta.env.MODE !== "mock" && (import.meta.env.MODE !== "test" || Boolean(import.meta.env.VITE_TASK_CLIENT_USE_HTTP)),
    staleTime: 3_000, retry: false, refetchOnWindowFocus: true,
  });
}

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

export function useAccountPool() {
  return useQuery({
    queryKey: ["platform", "accounts"],
    queryFn: fetchAccountPool,
    staleTime: 5_000,
    refetchInterval: 15_000,
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

const GOAL_FINISHED = new Set(["COMPLETED", "SUCCEEDED", "CANCELLED", "FAILED", "ARCHIVED"]);

/**
 * How often the goal detail refreshes. A stopped (BLOCKED) goal can be resumed
 * from elsewhere (a supervisor retry, another window or tab), so it keeps a
 * slower poll; without it the cached goal kept naming an old attempt while the
 * timeline moved on (2026-11-14, #1521). Only a finished goal stops polling.
 */
export function goalReadRetryDelay(attempt: number): number {
  return Math.min(30_000, Math.round(5_000 * 2 ** Math.min(attempt, 3) * (1 + Math.random() * 0.2)));
}

export function goalRefetchInterval(status: string | undefined, failures = 0): number | false {
  if (failures > 0) return goalReadRetryDelay(failures - 1);
  if (status === "RUNNING") return 2_500;
  return status && GOAL_FINISHED.has(status) ? false : 10_000;
}

export function useGoal(goalId: string | undefined) {
  return useQuery({
    queryKey: ["goals", goalId],
    queryFn: async ({ signal }) => {
      const goal = await fetchGoal(goalId ?? "", signal);
      if (goal.id !== goalId) throw new Error("未找到请求的目标。");
      return goal;
    },
    enabled: Boolean(goalId),
    staleTime: 1_500,
    retry: (failures, error) => failures < 2 && error instanceof PlatformClientError && error.retryable,
    retryDelay: goalReadRetryDelay,
    refetchInterval: (query) => {
      if (query.state.error instanceof PlatformClientError && !query.state.error.retryable) return false;
      return goalRefetchInterval((query.state.data as { status?: string } | undefined)?.status,
        query.state.error ? Math.max(1, query.state.fetchFailureCount) : 0);
    },
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });
}

const LIVE_ATTEMPT = new Set(["RUNNING", "RUNNING_FIXTURE", "VALIDATING", "PREPARING_WORKSPACE", "QUEUED"]);

/** Poll execution and landing independently, since landing can outlast the attempts. */
export function useGoalTimeline(goalId: string | undefined) {
  return useQuery({
    queryKey: ["goals", goalId, "timeline"],
    queryFn: () => fetchGoalTimeline(goalId ?? ""),
    enabled: Boolean(goalId),
    staleTime: 1_500,
    refetchInterval: (query) => {
      const data = query.state.data as PlatformGoalTimeline | undefined;
      const live = data?.steps.some((step) => step.attempts.some((attempt) => LIVE_ATTEMPT.has(attempt.status)));
      if (live || data?.goal.status === "RUNNING") return 3_000;
      const phase = data?.landing?.phase;
      return phase === "PENDING" || phase === "WAITING" || phase === "RECONCILING" ? 10_000 : false;
    },
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });
}

export function useRetryGoalStep(goalId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ planTaskId, revision, bindingRef }: { planTaskId: string; revision: number; bindingRef?: string }) =>
      retryGoalStep(goalId, planTaskId, revision, bindingRef),
    onSuccess: (goal) => {
      queryClient.setQueryData(["goals", goal.id], goal);
      void queryClient.invalidateQueries({ queryKey: ["goals", goal.id] });
      void queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}

export function useStartGoal() {
  return useGoalSubmission(startGoal);
}

export function useCreateGoalDraft() {
  return useGoalSubmission(createGoalDraft);
}

export function useDraftQuickStart() {
  return useMutation({
    mutationFn: (input: QuickStartDraftInput) => draftQuickStart(input),
  });
}

export function usePreflightOwnerWindow() {
  return useMutation({
    mutationFn: (request: OwnerWindowPreflightRequest) => preflightOwnerWindow(request),
  });
}

function useGoalSubmission(submit: typeof startGoal) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: StartGoalInput) => submit(input),
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
      // Starting a Goal can materialize new Tasks outside the current route.
      void queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}
