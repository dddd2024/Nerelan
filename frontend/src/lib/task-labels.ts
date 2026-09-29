/**
 * Product-language labels for runtime enums.
 *
 * The API speaks in machine states (`PENDING`, `EXECUTOR_RUNNING`, ...). Those
 * strings used to reach the screen verbatim, so the same product read as
 * Chinese in one panel and English in the next. This module is the single
 * mapping from runtime vocabulary to product vocabulary, matching the pattern
 * already used by `goal-status-label.ts`.
 */
import type {
  ActivityEventType,
  AuthorityStatus,
  TestStatus,
  WorkflowStatus,
} from "@/types";

const AUTHORITY_LABELS: Record<AuthorityStatus, string> = {
  APPROVED: "授权已批准",
  CANDIDATE: "待审候选",
  EXPIRED: "授权已过期",
  MISSING: "授权缺失",
  REVOKED: "授权已撤销",
};

const TEST_LABELS: Record<TestStatus, string> = {
  PASS: "检查通过",
  FAIL: "检查未通过",
  PENDING: "待验证",
  RUNNING: "验证中",
};

const WORKFLOW_LABELS: Record<WorkflowStatus, string> = {
  SUCCESS: "流水线通过",
  FAILURE: "流水线失败",
  PENDING: "流水线排队中",
  RUNNING: "流水线运行中",
  NEUTRALIZED: "流水线已中和",
  UNKNOWN: "流水线未知",
};

const EVENT_LABELS: Record<ActivityEventType, string> = {
  DISCOVERED: "已识别任务",
  VALIDATED: "校验通过",
  WORKSPACE_READY: "工作区已就绪",
  EXECUTOR_RUNNING: "Agent 正在执行",
  EXECUTOR_FINISHED: "Agent 执行结束",
  LOCAL_VALIDATED: "本地校验通过",
  COMMITTED: "已提交改动",
  PUSHED: "已推送分支",
  DRAFT_PR_OPEN: "草稿 PR 已创建",
  WORKFLOWS_OBSERVED: "已核对流水线",
  READY_FOR_HUMAN: "等待人工处理",
};

/** Localized label for an authority state, or the raw value as a fallback. */
export function authorityStatusLabel(status: string | undefined): string {
  if (!status) return "—";
  return AUTHORITY_LABELS[status as AuthorityStatus] ?? status;
}

/** Localized label for a test/verification state, or the raw value. */
export function testStatusLabel(status: string | undefined): string {
  if (!status) return "—";
  return TEST_LABELS[status as TestStatus] ?? status;
}

/** Localized label for a workflow state, or the raw value. */
export function workflowStatusLabel(status: string | undefined): string {
  if (!status) return "—";
  return WORKFLOW_LABELS[status as WorkflowStatus] ?? status;
}

/** Localized label for an activity event type, or the raw value. */
export function activityEventLabel(type: string): string {
  return EVENT_LABELS[type as ActivityEventType] ?? type;
}

/**
 * Localized label for a validation command outcome.
 *
 * `undefined` means "no deterministic check was recorded", which is a
 * materially different statement from "the check failed".
 */
export function validationStatusLabel(exitCode: number | undefined): string {
  if (exitCode === undefined) return "未记录检查结果";
  return exitCode === 0 ? `检查通过（exit ${exitCode}）` : `检查未通过（exit ${exitCode}）`;
}
