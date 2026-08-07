export interface BackendTaskCreatePayload {
  title: string;
  repository?: string;
  executor_kind?: "deterministic_fixture";
  model_profile_ref?: string;
  permission_profile?: string;
  policy_ref?: string;
  workspace?: string;
  branch?: string;
  idempotency_key?: string;
}

export interface BackendTaskCreateResponse extends Record<string, unknown> {
  id: string;
  title: string;
  repository: string;
  status: string;
  state: string;
  executor_kind: string;
  execution_id: string;
  created_at: string;
  updated_at: string;
  failure_classification?: string;
  failure_detail?: string;
  changed_files?: Array<Record<string, unknown>>;
  evidence?: Array<Record<string, unknown>>;
  events?: Array<Record<string, unknown>>;
  frontend_task?: Record<string, unknown>;
}

export interface BackendTaskListResponse extends Record<string, unknown> {
  tasks: Array<Record<string, unknown>>;
  total: number;
}

export type BackendTaskDetailResponse = BackendTaskCreateResponse;

export interface BackendTaskEventsResponse extends Record<string, unknown> {
  task_id: string;
  events: Array<Record<string, unknown>>;
}

const API_BASE =
  import.meta.env.VITE_TASK_API_BASE ?? "http://127.0.0.1:8766";

function _isMock() {
  const mode = import.meta.env.MODE;
  if (mode === "mock") return true;
  if (mode === "test") {
    return !import.meta.env.VITE_TASK_CLIENT_USE_HTTP;
  }
  return false;
}

async function _json<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text) return {} as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error("invalid api response");
  }
}

function _array<T>(value: unknown): Array<T> {
  return Array.isArray(value) ? value : [];
}

function _statusOf(event: Record<string, unknown> | undefined) {
  if (!event) return "";
  return String((event as { type?: string }).type ?? "");
}

function _normalizeTask(raw: Record<string, unknown>) {
  const ft = raw.frontend_task as Record<string, unknown> | undefined;
  const source = ft ?? raw;
  const state =
    source.state ?? raw.status ?? "WAITING_FOR_OWNER";
  const title = String(source.title ?? raw.title ?? "");
  const id = String(source.id ?? raw.id ?? "");

  const permissionProfile =
    source.permissionProfile ??
    (raw as { permission_profile?: string }).permission_profile ??
    "ASK_FOR_APPROVAL";

  const evidence: Array<Record<string, unknown>> = _array(
    source.evidence ?? (raw.evidence as Array<Record<string, unknown>> | undefined),
  );
  const activity: Array<Record<string, unknown>> = _array(
    source.activity ?? (raw.events as Array<Record<string, unknown>> | undefined),
  );
  const changes: Array<Record<string, unknown>> = _array(
    source.changes ??
      (raw.changed_files as Array<Record<string, unknown>> | undefined),
  );

  return {
    id,
    title,
    issueNumber: Number(source.issueNumber ?? 0),
    state,
    riskTier: (source.riskTier as string) ?? "R1",
    updatedAt: String(source.updatedAt ?? raw.updated_at ?? ""),
    blocker: (source.blocker as string | undefined) ?? "",
    nextAction: (source.nextAction as string | undefined) ?? "",
    permissionProfile: permissionProfile as
      | "ASK_FOR_APPROVAL"
      | "CONTROLLER_REVIEW"
      | "OWNER_CONTROL"
      | "CUSTOM",
    modelProfileId:
      (source.modelProfileId as string | undefined) ??
      (raw.model_profile_ref as string | undefined) ??
      undefined,
    branch: String(source.branch ?? raw.branch ?? id),
    activity: activity.map((e: Record<string, unknown>, i: number) => ({
      id: String(e.id ?? `a-${i}`),
      type: _statusOf(e as Record<string, unknown>) || "EXECUTOR_FINISHED",
      timestamp: String(e.timestamp ?? ""),
      title: String(e.title ?? ""),
      description: String(e.description ?? ""),
      rawLog: String((e as { raw_log?: string }).raw_log ?? ""),
      expanded: false,
    })),
    changes: changes.map((c: Record<string, unknown>) => ({
      path: String(c.path ?? ""),
      status: (c.status as string) ?? "modified",
      additions: Number(c.additions ?? 0),
      deletions: Number(c.deletions ?? 0),
      diff: String(c.diff ?? ""),
    })),
    evidence: evidence.map((ev: Record<string, unknown>) => ({
      id: String(ev.id ?? ""),
      category: String(ev.category ?? "Info"),
      label: String(ev.label ?? ""),
      value: String(ev.value ?? ""),
      status: (ev.status as string) ?? "info",
      detail: String(ev.detail ?? ""),
      rawJson: String((ev as { raw_json_digest?: string }).raw_json_digest ?? ""),
    })),
    authorityStatus: (source.authorityStatus as string) ?? "APPROVED",
    testStatus: (source.testStatus as string) ?? "PENDING",
    workflowStatus: (source.workflowStatus as string) ?? "PENDING",
    executor:
      (source.executor as string | undefined) ??
      (raw.executor_kind as string | undefined) ??
      "",
    repository: String(raw.repository ?? ""),
    executionId: String(source.execution_id ?? raw.execution_id ?? ""),
    failureClassification:
      (raw as { failure_classification?: string }).failure_classification ??
      (raw as { failure_classification?: string }).failure_classification ??
      "",
    validationCommandId:
      (raw as { validation_command_id?: string }).validation_command_id ??
      "",
    validationExitCode: (raw as { validation_exit_code?: number })
      .validation_exit_code,
  } as Record<string, unknown>;
}

export async function fetchTasks(): Promise<Record<string, unknown>[]> {
  if (_isMock()) {
    const { FIXTURE_TASKS } = await import("@/fixtures/tasks");
    return (FIXTURE_TASKS as unknown as Array<Record<string, unknown>>) ?? [];
  }
  const response = await fetch(`${API_BASE}/api/tasks`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`fetch tasks failed: ${response.status}`);
  }
  const payload = (await _json<BackendTaskListResponse>(response)) as Record<
    string,
    unknown
  >;
  return _array<Record<string, unknown>>(payload.tasks).map(_normalizeTask);
}

export async function fetchTask(taskId: string) {
  if (!taskId) throw new Error("taskId is required");
  if (_isMock()) {
    const { findFixtureTask } = await import("@/fixtures/tasks");
    const found = findFixtureTask(taskId);
    if (!found) throw new Error(`Task not found: ${taskId}`);
    return found as unknown as Record<string, unknown>;
  }
  const response = await fetch(`${API_BASE}/api/tasks/${taskId}`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`fetch task failed: ${response.status}`);
  }
  const payload = (await _json<BackendTaskDetailResponse>(response)) as Record<
    string,
    unknown
  >;
  return _normalizeTask(payload);
}

export async function fetchTaskEvents(
  taskId: string,
): Promise<Array<Record<string, unknown>>> {
  if (!taskId) return [];
  if (_isMock()) return [];
  const response = await fetch(
    `${API_BASE}/api/tasks/${taskId}/events`,
    {
      headers: { Accept: "application/json" },
    },
  );
  if (!response.ok) {
    throw new Error(`fetch task events failed: ${response.status}`);
  }
  const payload = (await _json<BackendTaskEventsResponse>(response)) as Record<
    string,
    unknown
  >;
  return _array(payload.events);
}

export async function executeTask(taskId: string): Promise<Record<string, unknown>> {
  if (!taskId) throw new Error("taskId is required");
  if (_isMock()) {
    return {
      id: taskId,
      title: "mock task",
      issueNumber: 0,
      state: "READY_FOR_HUMAN",
      riskTier: "R1",
      updatedAt: new Date().toISOString(),
      nextAction: "mock fixture execution",
      permissionProfile: "ASK_FOR_APPROVAL",
      branch: taskId,
      activity: [
        { id: "e-1", type: "DISCOVERED", timestamp: "", title: "Task queued", description: "", expanded: false },
        { id: "e-2", type: "WORKSPACE_READY", timestamp: "", title: "Workspace ready", description: "", expanded: false },
        { id: "e-3", type: "EXECUTOR_RUNNING", timestamp: "", title: "Executor running", description: "", expanded: false },
        { id: "e-4", type: "VALIDATED", timestamp: "", title: "Validation passed", description: "", expanded: false },
      ],
      changes: [
        { path: "fixture.txt", status: "modified", additions: 1, deletions: 0, diff: "" },
      ],
      evidence: [
        { id: "ev-1", category: "Validation", label: "git_diff_check", value: "0", status: "pass", detail: "", rawJson: "" },
        { id: "ev-2", category: "Executor", label: "executor_kind", value: "deterministic_fixture", status: "pass", detail: "", rawJson: "" },
      ],
      authorityStatus: "APPROVED",
      testStatus: "PASS",
      workflowStatus: "PENDING",
      executor: "fixture/provider-free",
    };
  }
  const response = await fetch(`${API_BASE}/api/tasks/${taskId}/execute`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    const payload = await _json<Record<string, unknown>>(response).catch(
      () => ({}),
    );
    throw new Error(
      `execute task failed: ${response.status} ${(payload as {
        error?: string;
      }).error ?? ""}`,
    );
  }
  const payload = (await _json<BackendTaskCreateResponse>(response)) as Record<
    string,
    unknown
  >;
  return _normalizeTask(payload);
}
export async function createTask(
  input: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  if (_isMock()) {
    const timestamp = Date.now();
    const title = String((input as { title?: string }).title ?? "mock task");
    return {
      id: `mock-${timestamp}`,
      title,
      issueNumber: 0,
      state: "WAITING_FOR_OWNER",
      riskTier: "R1",
      updatedAt: new Date().toISOString(),
      nextAction: "mock backend task plane",
      permissionProfile: "ASK_FOR_APPROVAL",
      branch: "",
      activity: [],
      changes: [],
      evidence: [],
      authorityStatus: "APPROVED",
      testStatus: "PENDING",
      workflowStatus: "PENDING",
      executor: "fixture/provider-free",
    };
  }
  const body: Record<string, unknown> = {
    title: (input as { title?: string }).title ?? "untitled",
    repository: (input as { repository?: string }).repository ?? "dddd2024/reverse-agent",
    executor_kind: "deterministic_fixture",
    model_profile_ref: (input as { model_profile_ref?: string }).model_profile_ref ?? "",
    permission_profile: (input as { permission_profile?: string }).permission_profile ?? "ASK_FOR_APPROVAL",
    policy_ref: (input as { policy_ref?: string }).policy_ref ?? "",
    workspace: (input as { workspace?: string }).workspace ?? "",
    branch: (input as { branch?: string }).branch ?? "",
  };
  if ((input as { idempotency_key?: string }).idempotency_key) {
    body.idempotency_key = (input as { idempotency_key?: string }).idempotency_key;
  }
  const response = await fetch(`${API_BASE}/api/tasks`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const payload = await _json<Record<string, unknown>>(response).catch(
      () => ({}),
    );
    throw new Error(
      `create task failed: ${response.status} ${(payload as {
        error?: string;
      }).error ?? ""}`,
    );
  }
  const payload = (await _json<BackendTaskCreateResponse>(response)) as Record<
    string,
    unknown
  >;
  return _normalizeTask(payload);
}
