import {
  PlatformClientError,
  createGoalDraftRecord,
  fetchGoal,
  fetchPlatformStatus,
  startGoal as legacyStartGoal,
  type PlatformGoal,
  type PlatformWindow,
  type StartGoalInput as PlatformStartGoalInput,
} from "@/lib/platform-client";

export interface StartGoalInput extends PlatformStartGoalInput {
  operationId: string;
}

type GoalStartStage = "CREATE" | "DRAFT" | "PLANNED" | "APPROVED";

interface GoalStartJournal {
  version: 1;
  operation_id: string;
  idempotency_key: string;
  input_fingerprint: string;
  goal_id: string;
  stage: GoalStartStage;
}

interface InFlightGoalStart {
  fingerprint: string;
  promise: Promise<PlatformGoal>;
}

const API_BASE = import.meta.env.VITE_TASK_API_BASE ?? "http://127.0.0.1:8766";
const JOURNAL_PREFIX = "nerelan.goal-start.operation.v1:";
const JOURNAL_FIELDS = new Set([
  "version",
  "operation_id",
  "idempotency_key",
  "input_fingerprint",
  "goal_id",
  "stage",
]);
const VALID_STAGES = new Set<GoalStartStage>([
  "CREATE",
  "DRAFT",
  "PLANNED",
  "APPROVED",
]);
const OPERATION_ID_PATTERN = /^[A-Za-z0-9._:-]{8,160}$/;
const GOAL_ID_PATTERN = /^[A-Za-z0-9._:-]{1,256}$/;
const inFlightGoalStarts = new Map<string, InFlightGoalStart>();

function isMock() {
  if (import.meta.env.MODE === "mock") return true;
  return import.meta.env.MODE === "test" && !import.meta.env.VITE_TASK_CLIENT_USE_HTTP;
}

function legacyInput(input: StartGoalInput): PlatformStartGoalInput {
  return {
    objective: input.objective,
    repository: input.repository,
    executorKind: input.executorKind,
    bindingRef: input.bindingRef,
    autonomyHours: input.autonomyHours,
  };
}

function journalKey(operationId: string) {
  return `${JOURNAL_PREFIX}${operationId}`;
}

function fingerprintInput(input: StartGoalInput): string {
  const canonical = JSON.stringify([
    input.objective,
    input.repository,
    input.executorKind,
    input.bindingRef,
    input.autonomyHours,
  ]);
  let hash = 0x811c9dc5;
  for (let index = 0; index < canonical.length; index += 1) {
    hash ^= canonical.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

export class GoalStartOperationError extends Error {
  readonly code: string;
  readonly goalId: string;

  constructor(code: string, goalId = "") {
    const message =
      code === "active_window_repository_conflict"
        ? "当前自治窗口属于其他仓库，请先完成或结束该窗口后再继续此目标。"
        : code === "goal_start_blocked"
          ? "该目标已进入阻塞状态；请处理现有目标，不要创建替代目标。"
          : code === "goal_start_invalidated"
            ? "该目标已失效；请先审查现有目标状态，再决定后续操作。"
            : code === "goal_start_operation_input_mismatch"
              ? "恢复中的目标与当前草稿不匹配；请保留当前草稿并重新提交。"
              : code === "goal_start_journal_invalid"
                ? "目标启动恢复信息无效；已停止自动恢复以避免创建重复目标。"
                : code === "goal_start_storage_unavailable"
                  ? "浏览器无法保存目标启动恢复信息；已停止启动以避免重复目标。"
                  : "目标启动状态无法安全恢复，请审查现有目标后重试。";
    super(message);
    this.name = "GoalStartOperationError";
    this.code = code;
    this.goalId = goalId;
  }
}

function storage(): Storage {
  if (typeof window === "undefined") {
    throw new GoalStartOperationError("goal_start_storage_unavailable");
  }
  try {
    return window.localStorage;
  } catch {
    throw new GoalStartOperationError("goal_start_storage_unavailable");
  }
}

function isValidJournal(value: unknown, operationId: string): value is GoalStartJournal {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  if (Object.keys(record).some((key) => !JOURNAL_FIELDS.has(key))) return false;
  return (
    record.version === 1 &&
    record.operation_id === operationId &&
    typeof record.idempotency_key === "string" &&
    record.idempotency_key === `ui-goal-${operationId}` &&
    typeof record.input_fingerprint === "string" &&
    /^[0-9a-f]{8}$/.test(record.input_fingerprint) &&
    typeof record.goal_id === "string" &&
    (record.goal_id === "" || GOAL_ID_PATTERN.test(record.goal_id)) &&
    typeof record.stage === "string" &&
    VALID_STAGES.has(record.stage as GoalStartStage)
  );
}

function readJournal(operationId: string): GoalStartJournal | null {
  let raw: string | null;
  try {
    raw = storage().getItem(journalKey(operationId));
  } catch (error) {
    if (error instanceof GoalStartOperationError) throw error;
    throw new GoalStartOperationError("goal_start_storage_unavailable");
  }
  if (raw === null) return null;
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new GoalStartOperationError("goal_start_journal_invalid");
  }
  if (!isValidJournal(parsed, operationId)) {
    throw new GoalStartOperationError("goal_start_journal_invalid");
  }
  return parsed;
}

function writeJournal(journal: GoalStartJournal): void {
  try {
    storage().setItem(journalKey(journal.operation_id), JSON.stringify(journal));
  } catch (error) {
    if (error instanceof GoalStartOperationError) throw error;
    throw new GoalStartOperationError("goal_start_storage_unavailable");
  }
}

function clearJournal(operationId: string): void {
  try {
    storage().removeItem(journalKey(operationId));
  } catch {
    // The server Goal is already authoritative; a stale journal can only
    // reconcile to that same Goal on the next attempt.
  }
}

function ensureJournal(input: StartGoalInput, fingerprint: string): GoalStartJournal {
  if (!OPERATION_ID_PATTERN.test(input.operationId)) {
    throw new GoalStartOperationError("goal_start_journal_invalid");
  }
  const existing = readJournal(input.operationId);
  if (existing) {
    if (existing.input_fingerprint !== fingerprint) {
      throw new GoalStartOperationError(
        "goal_start_operation_input_mismatch",
        existing.goal_id,
      );
    }
    return existing;
  }
  const created: GoalStartJournal = {
    version: 1,
    operation_id: input.operationId,
    idempotency_key: `ui-goal-${input.operationId}`,
    input_fingerprint: fingerprint,
    goal_id: "",
    stage: "CREATE",
  };
  writeJournal(created);
  return created;
}

function stageForGoal(goal: PlatformGoal): GoalStartStage {
  if (goal.status === "DRAFT") return "DRAFT";
  if (goal.status === "PLANNED") return "PLANNED";
  if (goal.status === "APPROVED") return "APPROVED";
  return "APPROVED";
}

function updateJournalGoal(
  journal: GoalStartJournal,
  goal: PlatformGoal,
): GoalStartJournal {
  const updated: GoalStartJournal = {
    ...journal,
    goal_id: goal.id,
    stage: stageForGoal(goal),
  };
  writeJournal(updated);
  return updated;
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

async function ensureWindow(input: StartGoalInput, goalId: string): Promise<PlatformWindow> {
  const platform = await fetchPlatformStatus();
  const active = platform.autonomy.active_window;
  if (active) {
    if (!active.repositories.includes(input.repository)) {
      throw new GoalStartOperationError(
        "active_window_repository_conflict",
        goalId,
      );
    }
    return active;
  }

  const starts = new Date();
  const expires = new Date(
    starts.getTime() + input.autonomyHours * 60 * 60 * 1000,
  );
  return request<PlatformWindow>("/api/windows/activate", {
    method: "POST",
    body: JSON.stringify({
      policy_id: `owner-ui-${input.operationId}`,
      policy_revision: 1,
      owner_identity: "local-owner",
      starts_at: starts.toISOString(),
      expires_at: expires.toISOString(),
      repositories: [input.repository],
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
}

async function runGoalStart(
  input: StartGoalInput,
  fingerprint: string,
  draftOnly = false,
): Promise<PlatformGoal> {
  let journal = ensureJournal(input, fingerprint);
  let goal: PlatformGoal;

  if (journal.goal_id) {
    goal = await fetchGoal(journal.goal_id);
    if (goal.id !== journal.goal_id) throw new GoalStartOperationError("goal_start_unexpected_state", journal.goal_id);
  } else {
    if (!draftOnly) {
      const platform = await fetchPlatformStatus();
      const active = platform.autonomy.active_window;
      if (active && !active.repositories.includes(input.repository)) {
        throw new GoalStartOperationError("active_window_repository_conflict");
      }
    }
    goal = await request<PlatformGoal>("/api/goals", {
      method: "POST",
      body: JSON.stringify({
        objective: input.objective,
        repository: input.repository,
        idempotency_key: journal.idempotency_key,
        executor_kind: input.executorKind,
        orchestration_mode:
          input.executorKind === "opencode" ? "sequential_team" : "single",
        binding_ref: input.executorKind === "opencode" ? input.bindingRef : "",
      }),
    });
    journal = updateJournalGoal(journal, goal);
  }

  if (draftOnly) return goal;

  for (let step = 0; step < 8; step += 1) {
    if (goal.status === "RUNNING" || goal.status === "COMPLETED") {
      clearJournal(input.operationId);
      return goal;
    }
    if (goal.status === "BLOCKED") {
      throw new GoalStartOperationError("goal_start_blocked", goal.id);
    }
    if (goal.status === "INVALIDATED") {
      throw new GoalStartOperationError("goal_start_invalidated", goal.id);
    }
    if (goal.status === "DRAFT") {
      goal = await request<PlatformGoal>(
        `/api/goals/${encodeURIComponent(goal.id)}/plan`,
        {
          method: "POST",
          body: JSON.stringify({ expected_revision: goal.revision }),
        },
      );
      journal = updateJournalGoal(journal, goal);
      continue;
    }
    if (goal.status === "PLANNED") {
      goal = await request<PlatformGoal>(
        `/api/goals/${encodeURIComponent(goal.id)}/approve`,
        {
          method: "POST",
          body: JSON.stringify({ expected_revision: goal.revision }),
        },
      );
      journal = updateJournalGoal(journal, goal);
      continue;
    }
    if (goal.status === "APPROVED") {
      const window = await ensureWindow(input, goal.id);
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
      goal = await fetchGoal(goal.id);
      continue;
    }
  }

  throw new GoalStartOperationError("goal_start_unexpected_state", goal.id);
}

export function startGoal(input: StartGoalInput): Promise<PlatformGoal> {
  return startOperation(input, false);
}

export function createGoalDraft(input: StartGoalInput): Promise<PlatformGoal> {
  return startOperation(input, true);
}

function startOperation(input: StartGoalInput, draftOnly: boolean): Promise<PlatformGoal> {
  if (isMock()) {
    return draftOnly
      ? createGoalDraftRecord(legacyInput(input), input.operationId)
      : legacyStartGoal(legacyInput(input));
  }

  const fingerprint = fingerprintInput(input);
  const flightKey = draftOnly ? `draft:${input.operationId}` : input.operationId;
  const existing = inFlightGoalStarts.get(flightKey);
  if (existing) {
    if (existing.fingerprint !== fingerprint) {
      return Promise.reject(
        new GoalStartOperationError("goal_start_operation_input_mismatch"),
      );
    }
    return existing.promise;
  }

  const promise = runGoalStart(input, fingerprint, draftOnly);
  inFlightGoalStarts.set(flightKey, { fingerprint, promise });
  const cleanup = () => {
    const current = inFlightGoalStarts.get(flightKey);
    if (current?.promise === promise) {
      inFlightGoalStarts.delete(flightKey);
    }
  };
  void promise.then(cleanup, cleanup);
  return promise;
}
