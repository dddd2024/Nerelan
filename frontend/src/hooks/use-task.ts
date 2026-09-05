import { useQuery } from "@tanstack/react-query";
import { fetchTask } from "@/lib/task-client";
import type { ActivityEventType, ChangedFile, EvidenceItem, Task } from "@/types";

const EMPTY_TASK: Task = {
  id: "",
  title: "",
  issueNumber: null,
  state: "WAITING_FOR_OWNER",
  riskTier: "UNKNOWN",
  updatedAt: "",
  permissionProfile: "ASK_FOR_APPROVAL",
  branch: "",
  activity: [],
  changes: [],
  evidence: [],
  authorityStatus: "MISSING",
  testStatus: "PENDING",
  workflowStatus: "UNKNOWN",
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

function _issueNumber(v: unknown): Task["issueNumber"] {
  return typeof v === "number" && Number.isInteger(v) && v > 0 ? v : null;
}

function _riskTier(v: unknown): Task["riskTier"] {
  if (
    typeof v === "string" &&
    (v in { R0: 0, R1: 0, R2: 0, R3: 0, UNKNOWN: 0 })
  )
    return v as Task["riskTier"];
  return "UNKNOWN";
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
  return "MISSING";
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
  return "UNKNOWN";
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
    issueNumber: _issueNumber(source.issueNumber ?? source.issue_number ?? raw.issue_number),
    state: _state(source.state ?? raw.status, "WAITING_FOR_OWNER"),
    riskTier: _riskTier(source.riskTier ?? source.risk_tier ?? raw.risk_tier),
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
    branch: String(source.branch ?? raw.branch ?? (source.id ?? raw.id ?? "")),
    activity: activity.map((e) => {
      if (!e)
        return {
          id: "",
          type: "EXECUTOR_FINISHED",
          timestamp: "",
          title: "",
          description: "",
          expanded: false,
        };
      return {
        id: String(e.id ?? ""),
        type: _activityType(e.type, "EXECUTOR_FINISHED"),
        timestamp: String((e as { timestamp?: string }).timestamp ?? ""),
        title: String((e as { title?: string }).title ?? ""),
        description: String((e as { description?: string }).description ?? ""),
        rawLog: String(
          (e as { rawLog?: string; raw_log?: string }).rawLog ??
            (e as { rawLog?: string; raw_log?: string }).raw_log ??
            "",
        ),
        expanded: false,
      };
    }),
    changes: changes.map((f) => {
      if (!f)
        return { path: "", status: "modified", additions: 0, deletions: 0, diff: "" };
      const s = String((f as { status?: string }).status ?? "modified");
      const status =
        s === "added" || s === "modified" || s === "deleted" || s === "renamed"
          ? s
          : "modified";
      return {
        path: String((f as { path?: string }).path ?? ""),
        status: status as ChangedFile["status"],
        additions: Number((f as { additions?: number }).additions ?? 0),
        deletions: Number((f as { deletions?: number }).deletions ?? 0),
        diff: String((f as { diff?: string }).diff ?? ""),
      };
    }),
    evidence: evidence.map((ev) => {
      if (!ev)
        return {
          id: "",
          category: "Info",
          label: "",
          value: "",
          status: "info",
        };
      const s = String((ev as { status?: string }).status ?? "info");
      const status =
        s === "pass" || s === "fail" || s === "pending" ? s : "info";
      return {
        id: String((ev as { id?: string }).id ?? ""),
        category: String((ev as { category?: string }).category ?? "Info"),
        label: String((ev as { label?: string }).label ?? ""),
        value: String((ev as { value?: string }).value ?? ""),
        status: status as EvidenceItem["status"],
        detail: String((ev as { detail?: string }).detail ?? ""),
        rawJson: String(
          (ev as { rawJson?: string; raw_json_digest?: string }).rawJson ??
            (ev as { rawJson?: string; raw_json_digest?: string }).raw_json_digest ??
            "",
        ),
      };
    }),
    authorityStatus: _authority(
      source.authorityStatus ?? source.authority_status ?? raw.authority_status,
    ),
    testStatus: _testStatus(source.testStatus ?? "PENDING"),
    workflowStatus: _workflowStatus(
      source.workflowStatus ?? source.workflow_status ?? raw.workflow_status,
    ),
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

export function useTask(taskId: string | undefined) {
  return useQuery<Task>({
    queryKey: ["tasks", taskId],
    queryFn: async () => {
      if (!taskId) throw new Error("taskId is required");
      const raw = await fetchTask(taskId);
      return _toTask(raw);
    },
    enabled: Boolean(taskId),
    staleTime: 1000,
    retry: 1,
  });
}
