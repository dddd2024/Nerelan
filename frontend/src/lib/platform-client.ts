export type GoalStatus =
  | "DRAFT"
  | "PLANNED"
  | "APPROVED"
  | "RUNNING"
  | "COMPLETED"
  | "BLOCKED"
  | "INVALIDATED";

export interface PlatformGoal {
  id: string;
  title: string;
  objective: string;
  repository: string;
  status: GoalStatus;
  revision: number;
  spec_markdown: string;
  plan_markdown: string;
  tasks: Array<{ id: string; title: string; dependencies: string[] }>;
  acceptance_criteria: string[];
  artifact_digest: string;
  executor_kind: "opencode" | "deterministic_fixture";
  orchestration_mode: "single" | "sequential_team";
  binding_ref: string;
  window_id: string;
  created_at: string;
  updated_at: string;
  task_links?: Array<{ task_id: string; plan_task_id: string; status: string; title: string }>;
}

export interface PlatformWindow {
  id: string;
  policy_id: string;
  status: string;
  expires_at: string;
  repositories: string[];
  capabilities: string[];
  max_tasks: number;
  tasks_started: number;
  tasks_completed: number;
}

export interface PlatformStatus {
  service: string;
  autonomy: {
    autonomy_enabled: boolean;
    active_window: PlatformWindow | null;
    mode: string;
  };
  coordinator: {
    enabled: boolean;
    executions?: number;
    last_error: string;
    active_window_id: string;
  };
  task_count: number;
  goal_count: number;
  capability_count: number;
  live_model_calls: boolean;
}

export interface StartGoalInput {
  objective: string;
  repository: string;
  executorKind: "opencode" | "deterministic_fixture";
  bindingRef: string;
  autonomyHours: number;
}

const API_BASE = import.meta.env.VITE_TASK_API_BASE ?? "http://127.0.0.1:8766";

function isMock() {
  if (import.meta.env.MODE === "mock") return true;
  return import.meta.env.MODE === "test" && !import.meta.env.VITE_TASK_CLIENT_USE_HTTP;
}

const now = new Date();
const mockGoal: PlatformGoal = {
  id: "goal-demo-platform",
  title: "完善无人值守多 Agent 平台",
  objective: "把目标拆解为可恢复任务，按策略协调多个 Agent，并交付可审查的结果。",
  repository: "dddd2024/reverse-agent",
  status: "RUNNING",
  revision: 2,
  spec_markdown: "# Specification\n\nBuild a durable multi-agent platform.",
  plan_markdown: "# Plan\n\nAnalyze, implement, verify.",
  tasks: [
    { id: "T001", title: "分析目标与代码库", dependencies: [] },
    { id: "T002", title: "实现协调与恢复链路", dependencies: ["T001"] },
    { id: "T003", title: "验证并准备证据", dependencies: ["T002"] },
  ],
  acceptance_criteria: ["任务可恢复", "策略在服务端执行", "结果可审查"],
  artifact_digest: "b4a91c0e",
  executor_kind: "opencode",
  orchestration_mode: "sequential_team",
  binding_ref: "coding-default",
  window_id: "window-demo",
  created_at: new Date(now.getTime() - 25 * 60_000).toISOString(),
  updated_at: new Date(now.getTime() - 2 * 60_000).toISOString(),
  task_links: [
    { task_id: "task-demo-1", plan_task_id: "T001", status: "READY_FOR_REVIEW", title: "分析目标与代码库" },
    { task_id: "task-demo-2", plan_task_id: "T002", status: "RUNNING", title: "实现协调与恢复链路" },
    { task_id: "task-demo-3", plan_task_id: "T003", status: "QUEUED", title: "验证并准备证据" },
  ],
};

let mockGoals = [mockGoal];

const mockWindow: PlatformWindow = {
  id: "window-demo",
  policy_id: "owner-ui-demo",
  status: "ACTIVE",
  expires_at: new Date(now.getTime() + 95 * 60_000).toISOString(),
  repositories: ["dddd2024/reverse-agent"],
  capabilities: ["execute_task", "validate_task", "open_draft_pr"],
  max_tasks: 12,
  tasks_started: 2,
  tasks_completed: 1,
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { Accept: "application/json", "Content-Type": "application/json", ...init?.headers },
  });
  const text = await response.text();
  const payload = text ? (JSON.parse(text) as T & { error?: string }) : ({} as T & { error?: string });
  if (!response.ok) throw new Error(payload.error || `平台请求失败 (${response.status})`);
  return payload;
}

export async function fetchPlatformStatus(): Promise<PlatformStatus> {
  if (isMock()) return {
    service: "reverse-agent-platform-v2",
    autonomy: { autonomy_enabled: true, active_window: mockWindow, mode: "owner_activated_bounded_window" },
    coordinator: { enabled: true, executions: 7, last_error: "", active_window_id: mockWindow.id },
    task_count: 18, goal_count: mockGoals.length, capability_count: 6, live_model_calls: false,
  };
  return request<PlatformStatus>("/api/platform/status");
}

export async function fetchGoals(): Promise<PlatformGoal[]> {
  if (isMock()) return mockGoals;
  const result = await request<{ goals: PlatformGoal[] }>("/api/goals");
  return result.goals;
}

export async function fetchGoal(goalId: string): Promise<PlatformGoal> {
  if (isMock()) return mockGoals.find((goal) => goal.id === goalId) ?? mockGoal;
  return request<PlatformGoal>(`/api/goals/${encodeURIComponent(goalId)}`);
}

export async function startGoal(input: StartGoalInput): Promise<PlatformGoal> {
  if (isMock()) {
    const timestamp = new Date().toISOString();
    const goal: PlatformGoal = {
      ...mockGoal,
      id: `goal-${Date.now()}`,
      title: input.objective.slice(0, 48),
      objective: input.objective,
      repository: input.repository,
      status: "RUNNING",
      revision: 1,
      executor_kind: input.executorKind,
      orchestration_mode: input.executorKind === "opencode" ? "sequential_team" : "single",
      binding_ref: input.bindingRef,
      created_at: timestamp,
      updated_at: timestamp,
      task_links: mockGoal.task_links?.map((item, index) => ({
        ...item,
        task_id: `mock-task-${Date.now()}-${index}`,
        status: index === 0 ? "RUNNING" : "QUEUED",
      })),
    };
    mockGoals = [goal, ...mockGoals];
    return goal;
  }

  const idempotencyKey = `ui-goal-${Date.now()}-${crypto.randomUUID()}`;
  const created = await request<PlatformGoal>("/api/goals", {
    method: "POST",
    body: JSON.stringify({
      objective: input.objective,
      repository: input.repository,
      idempotency_key: idempotencyKey,
      executor_kind: input.executorKind,
      orchestration_mode: input.executorKind === "opencode" ? "sequential_team" : "single",
      binding_ref: input.executorKind === "opencode" ? input.bindingRef : "",
    }),
  });
  await request<PlatformGoal>(`/api/goals/${created.id}/plan`, {
    method: "POST", body: JSON.stringify({ expected_revision: created.revision }),
  });
  await request<PlatformGoal>(`/api/goals/${created.id}/approve`, {
    method: "POST", body: JSON.stringify({ expected_revision: created.revision }),
  });
  let status = await fetchPlatformStatus();
  let window = status.autonomy.active_window;
  if (!window || !window.repositories.includes(input.repository)) {
    const starts = new Date();
    const expires = new Date(starts.getTime() + input.autonomyHours * 60 * 60 * 1000);
    window = await request<PlatformWindow>("/api/windows/activate", {
      method: "POST",
      body: JSON.stringify({
        policy_id: `owner-ui-${Date.now()}`,
        policy_revision: 1,
        owner_identity: "local-owner",
        starts_at: starts.toISOString(),
        expires_at: expires.toISOString(),
        repositories: [input.repository],
        capabilities: ["execute_task", "resume_task", "reconcile_task", "validate_task", "open_draft_pr"],
        max_concurrent_tasks: 2,
        max_tasks: 20,
        max_retries: 1,
        confirmation: "ACTIVATE",
      }),
    });
  }
  await request<PlatformGoal>(`/api/goals/${created.id}/launch`, {
    method: "POST",
    body: JSON.stringify({ expected_revision: created.revision, window_id: window.id }),
  });
  return fetchGoal(created.id);
}
