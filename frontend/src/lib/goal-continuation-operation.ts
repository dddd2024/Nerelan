import {
  PlatformClientError,
  __setMockGoalStatus,
  fetchGoal,
  fetchPlatformStatus,
  type PlatformGoal,
  type PlatformWindow,
} from "@/lib/platform-client";

const API_BASE = import.meta.env.VITE_TASK_API_BASE ?? "http://127.0.0.1:8766";

export type GoalContinuationErrorCode =
  | "goal_revision_conflict"
  | "active_window_repository_conflict"
  | "invalid_autonomy_duration"
  | "goal_continuation_failed";

export class GoalContinuationError extends Error {
  readonly code: GoalContinuationErrorCode;
  readonly goalId: string;

  constructor(code: GoalContinuationErrorCode, goalId: string) {
    const message =
      code === "goal_revision_conflict"
        ? "目标已被其他操作更新。已重新读取最新状态，请确认后再继续。"
        : code === "active_window_repository_conflict"
          ? "当前自治窗口属于其他仓库；请先处理该窗口，再继续此目标。"
          : code === "invalid_autonomy_duration"
            ? "自治窗口时长无效。"
            : "目标继续操作未完成，请根据最新服务端状态重试。";
    super(message);
    this.name = "GoalContinuationError";
    this.code = code;
    this.goalId = goalId;
  }
}

function isMock() {
  if (import.meta.env.MODE === "mock") return true;
  return import.meta.env.MODE === "test" && !import.meta.env.VITE_TASK_CLIENT_USE_HTTP;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  const text = await response.text();
  const payload = text
    ? (JSON.parse(text) as T & { error?: string })
    : ({} as T & { error?: string });
  if (!response.ok) {
    const code =
      typeof payload.error === "string" ? payload.error : "platform_request_failed";
    throw new PlatformClientError(response.status, code);
  }
  return payload;
}

function mapStageError(error: unknown, goalId: string): never {
  if (
    error instanceof PlatformClientError &&
    (error.status === 409 ||
      error.code.includes("revision") ||
      error.code.includes("stale"))
  ) {
    throw new GoalContinuationError("goal_revision_conflict", goalId);
  }
  throw error;
}

async function mutateStage(
  goal: PlatformGoal,
  stage: "plan" | "approve",
): Promise<PlatformGoal> {
  try {
    return await request<PlatformGoal>(
      `/api/goals/${encodeURIComponent(goal.id)}/${stage}`,
      {
        method: "POST",
        body: JSON.stringify({ expected_revision: goal.revision }),
      },
    );
  } catch (error) {
    mapStageError(error, goal.id);
  }
}

async function ensureWindow(
  goal: PlatformGoal,
  autonomyHours: number,
): Promise<PlatformWindow> {
  if (!Number.isFinite(autonomyHours) || autonomyHours < 1 || autonomyHours > 24) {
    throw new GoalContinuationError("invalid_autonomy_duration", goal.id);
  }

  const platform = await fetchPlatformStatus();
  const active = platform.autonomy.active_window;
  if (active) {
    if (!active.repositories.includes(goal.repository)) {
      throw new GoalContinuationError(
        "active_window_repository_conflict",
        goal.id,
      );
    }
    return active;
  }

  const starts = new Date();
  const expires = new Date(
    starts.getTime() + autonomyHours * 60 * 60 * 1000,
  );
  try {
    return await request<PlatformWindow>("/api/windows/activate", {
      method: "POST",
      body: JSON.stringify({
        policy_id: `owner-approval-${goal.id}-${goal.revision}`,
        policy_revision: 1,
        owner_identity: "local-owner",
        starts_at: starts.toISOString(),
        expires_at: expires.toISOString(),
        repositories: [goal.repository],
        capabilities: [
          "execute_task",
          "resume_task",
          "reconcile_task",
          "validate_task",
          "open_draft_pr",
        ],
        max_concurrent_tasks: 2,
        max_tasks: 20,
        max_retries: 1,
        confirmation: "ACTIVATE",
      }),
    });
  } catch (error) {
    if (
      error instanceof PlatformClientError &&
      (error.status === 409 || error.code.includes("active_window"))
    ) {
      const refreshed = await fetchPlatformStatus();
      const refreshedWindow = refreshed.autonomy.active_window;
      if (
        refreshedWindow &&
        refreshedWindow.repositories.includes(goal.repository)
      ) {
        return refreshedWindow;
      }
      throw new GoalContinuationError(
        "active_window_repository_conflict",
        goal.id,
      );
    }
    throw error;
  }
}

export async function planExistingGoal(goal: PlatformGoal): Promise<PlatformGoal> {
  if (isMock()) {
    __setMockGoalStatus(goal.id, {
      status: "PLANNED",
      plan_markdown:
        goal.plan_markdown || "# Plan\n\nReview the generated plan before approval.",
    });
    return fetchGoal(goal.id);
  }
  return mutateStage(goal, "plan");
}

export async function approveExistingGoal(
  goal: PlatformGoal,
): Promise<PlatformGoal> {
  if (isMock()) {
    __setMockGoalStatus(goal.id, { status: "APPROVED" });
    return fetchGoal(goal.id);
  }
  return mutateStage(goal, "approve");
}

export async function launchExistingGoal(
  goal: PlatformGoal,
  autonomyHours: number,
): Promise<PlatformGoal> {
  if (isMock()) {
    __setMockGoalStatus(goal.id, {
      status: "RUNNING",
      window_id: "window-demo",
    });
    return fetchGoal(goal.id);
  }

  const window = await ensureWindow(goal, autonomyHours);
  try {
    await request<PlatformGoal>(
      `/api/goals/${encodeURIComponent(goal.id)}/launch`,
      {
        method: "POST",
        body: JSON.stringify({
          expected_revision: goal.revision,
          window_id: window.id,
        }),
      },
    );
    return fetchGoal(goal.id);
  } catch (error) {
    mapStageError(error, goal.id);
  }
}
