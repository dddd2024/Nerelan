import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createTask,
  executeTask,
  fetchTask,
  fetchTaskEvents,
  fetchTasks,
} from "@/lib/task-client";
import type { ActivityEvent, ActivityEventType, ChangedFile, EvidenceItem, PolicyContract, Task } from "@/types";

export interface CreateTaskInput {
  title: string;
  modelProfileId?: string;
  bindingRef?: string;
  executorKind?: "deterministic_fixture" | "opencode";
  permissionProfile?: string;
  policy?: PolicyContract;
  repository?: string;
  branch?: string;
  workspace?: string;
  idempotencyKey: string;
}

const EMPTY_TASK: Task = {
  id: "",
  title: "",
  issueNumber: 0,
  state: "WAITING_FOR_OWNER",
  riskTier: "R1",
  updatedAt: "",
  permissionProfile: "ASK_FOR_APPROVAL",
  branch: "",
  activity: [],
  changes: [],
  evidence: [],
  authorityStatus: "APPROVED",
  testStatus: "PENDING",
  workflowStatus: "PENDING",
};

type UnknownEvent = Record<string, unknown> | undefined;
type UnknownArray = Array<UnknownEvent>;

function _activityType(
  value: unknown,
  fallback: ActivityEventType,
): ActivityEventType {
  if (typeof value !== "string") return fallback;
  if (value in {
    DISCOVERED: 0,
    VALIDATED: 0,
    WORKSPACE_READY: 0,
    EXECUTOR_RUNNING: 0,
    EXECUTOR_FINISHED: 0,
    LOCAL_VALIDATED: 0,
    COMMITTED: 0,
    PUSHED: 0,
    DRAFT_PR_OPEN: 0,
    WORKFLOWS_OBSERVED: 0,
    READY_FOR_HUMAN: 0,
  }) return value as ActivityEventType;
  return fallback;
}

function _state(v: unknown, fallback: Task["state"]): Task["state"] {
  if (typeof v === "string" && (v in {
    READY_FOR_HUMAN: 0,
    RUNNING: 0,
    BLOCKED_EXTERNAL: 0,
    REWORK_REQUIRED: 0,
    FAILED_TERMINAL: 0,
    WAITING_FOR_OWNER: 0,
  })) return v as Task["state"];
  return fallback;
}

function _riskTier(v: unknown): Task["riskTier"] {
  if (typeof v === "string" && (v in { R0: 0, R1: 0, R2: 0, R3: 0 })) return v as Task["riskTier"];
  return "R1";
}

function _permission(v: unknown): Task["permissionProfile"] {
  if (typeof v === "string" && (v in {
    ASK_FOR_APPROVAL: 0,
    CONTROLLER_REVIEW: 0,
    OWNER_CONTROL: 0,
    CUSTOM: 0,
  })) return v as Task["permissionProfile"];
  return "ASK_FOR_APPROVAL";
}

function _authority(v: unknown): Task["authorityStatus"] {
  if (typeof v === "string" && (v in {
    APPROVED: 0,
    CANDIDATE: 0,
    EXPIRED: 0,
    MISSING: 0,
    REVOKED: 0,
  })) return v as Task["authorityStatus"];
  return "APPROVED";
}

function _testStatus(v: unknown): Task["testStatus"] {
  if (typeof v === "string" && (v in { PASS: 0, FAIL: 0, PENDING: 0, RUNNING: 0 }))
    return v as Task["testStatus"];
  return "PENDING";
}

function _workflowStatus(v: unknown): Task["workflowStatus"] {
  if (typeof v === "string" && (v in {
    SUCCESS: 0,
    FAILURE: 0,
    PENDING: 0,
    RUNNING: 0,
    NEUTRALIZED: 0,
    UNKNOWN: 0,
  })) return v as Task["workflowStatus"];
  return "PENDING";
}

function _toActivity(event: UnknownEvent, fallbackType: ActivityEventType): ActivityEvent {
  if (!event)
    return {
      id: "",
      type: fallbackType,
      timestamp: "",
      title: "",
      description: "",
      expanded: false,
    };
  return {
    id: String(event.id ?? ""),
    type: _activityType(event.type, fallbackType),
    timestamp: String((event as { timestamp?: string }).timestamp ?? ""),
    title: String((event as { title?: string }).title ?? ""),
    description: String((event as { description?: string }).description ?? ""),
    rawLog: String(
      (event as { rawLog?: string; raw_log?: string }).rawLog ??
        (event as { rawLog?: string; raw_log?: string }).raw_log ??
        "",
    ),
    expanded: false,
  };
}

function _toChangedFile(file: UnknownEvent): ChangedFile {
  if (!file)
    return { path: "", status: "modified", additions: 0, deletions: 0, diff: "" };
  const s = String((file as { status?: string }).status ?? "modified");
  const status =
    s === "added" || s === "modified" || s === "deleted" || s === "renamed"
      ? s
      : "modified";
  return {
    path: String((file as { path?: string }).path ?? ""),
    status: status as ChangedFile["status"],
    additions: Number((file as { additions?: number }).additions ?? 0),
    deletions: Number((file as { deletions?: number }).deletions ?? 0),
    diff: String((file as { diff?: string }).diff ?? ""),
  };
}

function _toEvidence(item: UnknownEvent): EvidenceItem {
  if (!item)
    return {
      id: "",
      category: "Info",
      label: "",
      value: "",
      status: "info",
    };
  const s = String((item as { status?: string }).status ?? "info");
  const status =
    s === "pass" || s === "fail" || s === "pending"
      ? s
      : "info";
  return {
    id: String((item as { id?: string }).id ?? ""),
    category: String((item as { category?: string }).category ?? "Info"),
    label: String((item as { label?: string }).label ?? ""),
    value: String((item as { value?: string }).value ?? ""),
    status: status as EvidenceItem["status"],
    detail: String((item as { detail?: string }).detail ?? ""),
    rawJson: String(
      (item as { rawJson?: string; raw_json_digest?: string }).rawJson ??
        (item as { rawJson?: string; raw_json_digest?: string }).raw_json_digest ??
        "",
    ),
  };
}

function _toTask(raw: Record<string, unknown> | undefined): Task {
  if (!raw) return EMPTY_TASK;
  const source =
    (raw as { frontend_task?: Record<string, unknown> }).frontend_task ?? raw;
  const activity = ((source.activity ?? raw.events ?? []) as UnknownArray) ?? [];
  const changes = ((source.changes ??
    raw.changed_files ??
    []) as UnknownArray) ?? [];
  const evidence = ((source.evidence ?? []) as UnknownArray) ?? [];
  return {
    id: String(source.id ?? raw.id ?? ""),
    title: String(source.title ?? raw.title ?? ""),
    issueNumber: Number(source.issueNumber ?? 0),
    state: _state(source.state ?? raw.status, "WAITING_FOR_OWNER"),
    riskTier: _riskTier(source.riskTier),
    updatedAt: String(source.updatedAt ?? raw.updated_at ?? ""),
    blocker: (String(source.blocker ?? raw.failure_detail ?? "") ||
      undefined) as Task["blocker"],
    nextAction: (String(source.nextAction ?? "") || undefined) as Task["nextAction"],
    permissionProfile: _permission(
      source.permissionProfile ?? raw.permission_profile ?? "ASK_FOR_APPROVAL",
    ),
    modelProfileId:
      (String(source.modelProfileId ?? raw.model_profile_ref ?? "") ||
        undefined) as Task["modelProfileId"],
    bindingRef:
      (String(source.bindingRef ?? raw.binding_ref ?? "") ||
        undefined) as Task["bindingRef"],
    branch: String(source.branch ?? raw.branch ?? (source.id ?? raw.id ?? "")),
    activity: activity.map((e, _i) => _toActivity(e, "EXECUTOR_FINISHED")),
    changes: changes.map(_toChangedFile),
    evidence: evidence.map(_toEvidence),
    authorityStatus: _authority(source.authorityStatus ?? "APPROVED"),
    testStatus: _testStatus(source.testStatus ?? "PENDING"),
    workflowStatus: _workflowStatus(source.workflowStatus ?? "PENDING"),
    executor:
      (String(source.executor ?? raw.executor_kind ?? "") ||
        undefined) as Task["executor"],
    repository: String(raw.repository ?? ""),
    executionId:
      (String(source.execution_id ?? raw.execution_id ?? "") ||
        undefined) as Task["executionId"],
    failureClassification:
      (String((raw as { failure_classification?: string }).failure_classification ?? "") ||
        undefined) as Task["failureClassification"],
    validationCommandId:
      (String((raw as { validation_command_id?: string }).validation_command_id ?? "") ||
        undefined) as Task["validationCommandId"],
    validationExitCode: (raw as { validation_exit_code?: number })
      .validation_exit_code,
  };
}

export function useTasks() {
  return useQuery<Task[]>({
    queryKey: ["tasks"],
    queryFn: async () => {
      const raw = await fetchTasks();
      return (raw as Array<Record<string, unknown>>).map(_toTask);
    },
    staleTime: 1000,
    retry: 1,
  });
}

export function useTaskEvents(taskId: string | undefined) {
  return useQuery<Array<Record<string, unknown>>>({
    queryKey: ["tasks", taskId, "events"],
    queryFn: async () => {
      if (!taskId) return [];
      return fetchTaskEvents(taskId);
    },
    enabled: Boolean(taskId),
    staleTime: 1000,
    retry: 1,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation<Task, Error, CreateTaskInput>({
    mutationFn: async (input) => {
      const isOpencode = input.executorKind === "opencode";
      const payload: Record<string, unknown> = {
        title: input.title,
        executor_kind: input.executorKind ?? "deterministic_fixture",
        model_profile_ref: isOpencode ? "" : (input.modelProfileId ?? ""),
        binding_ref: isOpencode ? (input.bindingRef ?? "") : "",
        permission_profile: input.permissionProfile ?? "ASK_FOR_APPROVAL",
        branch: input.branch ?? "",
        workspace: input.workspace ?? "",
        idempotency_key: input.idempotencyKey,
      };
      if (input.repository) {
        payload.repository = input.repository;
      }
      const createdRaw = await createTask(payload);
      const created = _toTask(createdRaw);
      const taskId = String(created.id ?? createdRaw.id ?? "");
      if (!taskId) return created;
      await executeTask(taskId);
      await queryClient.invalidateQueries({ queryKey: ["tasks"] });
      const readbackRaw = await fetchTask(taskId);
      return _toTask(readbackRaw);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}

export { fetchTaskEvents, fetchTasks } from "@/lib/task-client";
