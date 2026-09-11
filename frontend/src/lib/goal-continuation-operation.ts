import {
  PlatformClientError,
  __setMockGoalStatus,
  __launchMockGoal,
  fetchGoal,
  fetchPlatformStatus,
  type PlatformGoal,
  type PlatformWindow,
} from "@/lib/platform-client";

export interface GoalConfigurationInput {
  objective: string;
  repository: string;
  executor_kind: PlatformGoal["executor_kind"];
  orchestration_mode: PlatformGoal["orchestration_mode"];
  binding_ref: string;
}

export interface GoalPlanInput {
  tasks: PlatformGoal["tasks"];
  acceptance_criteria: string[];
}

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
  return saveGoalPlan(goal, { tasks: goal.tasks, acceptance_criteria: goal.acceptance_criteria });
}

async function saveRevision(goal: PlatformGoal, action: "amend" | "plan", input: object) {
  try {
    const saved = await request<PlatformGoal>(`/api/goals/${encodeURIComponent(goal.id)}/${action}`, {
      method: "POST", body: JSON.stringify({ ...input, expected_revision: goal.revision }),
    });
    if (saved.id !== goal.id) throw new GoalContinuationError("goal_continuation_failed", goal.id);
    return saved;
  } catch (error) { mapStageError(error, goal.id); }
}

async function mockCurrent(goal: PlatformGoal, statuses: PlatformGoal["status"][]) {
  const current = await fetchGoal(goal.id);
  if (current.id !== goal.id || current.revision !== goal.revision || !statuses.includes(current.status)) {
    throw new GoalContinuationError("goal_revision_conflict", goal.id);
  }
  return current;
}

export async function saveGoalConfiguration(goal: PlatformGoal, input: GoalConfigurationInput): Promise<PlatformGoal> {
  if (!isMock()) return saveRevision(goal, "amend", input);
  const current = await mockCurrent(goal, ["DRAFT", "PLANNED", "APPROVED"]);
  if (current.task_links?.length) throw new GoalContinuationError("goal_revision_conflict", goal.id);
  const unchanged = Object.entries(input).every(([key, value]) => current[key as keyof PlatformGoal] === value);
  if (!unchanged) __setMockGoalStatus(goal.id, {
    ...input, status: "DRAFT", revision: current.revision + 1, spec_markdown: "", plan_markdown: "",
    tasks: [], acceptance_criteria: [], artifact_digest: "", window_id: "", updated_at: new Date().toISOString(),
  });
  return { ...await fetchGoal(goal.id) };
}

export async function saveGoalPlan(goal: PlatformGoal, input: GoalPlanInput): Promise<PlatformGoal> {
  if (!isMock()) return saveRevision(goal, "plan", input);
  const current = await mockCurrent(goal, ["DRAFT", "PLANNED"]);
  const tasks = input.tasks.length ? input.tasks : [{
    id: "T001", title: "实现并验证目标", instruction: current.objective,
    dependencies: [], capability: "execute_task",
  }];
  const criteria = input.acceptance_criteria.length ? input.acceptance_criteria : [`完成目标：${current.objective}`];
  const unchanged = JSON.stringify(current.tasks) === JSON.stringify(tasks)
    && JSON.stringify(current.acceptance_criteria) === JSON.stringify(criteria);
  if (current.status === "PLANNED" && unchanged) return { ...current };
  const revision = current.revision + (current.status === "PLANNED" ? 1 : 0);
  __setMockGoalStatus(goal.id, {
    status: "PLANNED", revision, tasks, acceptance_criteria: criteria,
    spec_markdown: current.objective,
    plan_markdown: tasks.map((task) => `${task.id}: ${task.title}\n${task.instruction ?? task.title}${(task.validation_checks ?? []).map((check) => `\n功能检查：${check.profile_id} · ${check.working_directory}`).join("")}`).join("\n\n"),
    artifact_digest: `mock-plan:${current.id}:${revision}`, updated_at: new Date().toISOString(),
  });
  return { ...await fetchGoal(goal.id) };
}

export async function approveExistingGoal(
  goal: PlatformGoal,
): Promise<PlatformGoal> {
  if (isMock()) {
    await mockCurrent(goal, ["PLANNED"]);
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
    await mockCurrent(goal, ["APPROVED"]);
    __launchMockGoal(goal.id);
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
