import { taskCopy, uiLocale, type UiLocale } from "@/lib/ui-locale";
import { runtimeExplanation } from "@/lib/runtime-labels";

/** Short user-facing copy over machine status; original identifiers remain in diagnostics. */
// The host's next-action sentences (task_service._map_task_to_frontend), in the Owner's words.
const HOST_ACTIONS: Record<string, string> = {
  "Waiting for executor dispatch": "排队中：等待执行窗口派发",
  "Executor running": "正在执行",
  "Owner review of functionally validated result": "功能检查已通过，等你审查",
  "Owner review; functional acceptance evidence still required": "等你审查（还缺功能验收证据）",
};

export function taskActionCopy(value: string | undefined, locale: UiLocale = uiLocale()): string {
  const copy = taskCopy(locale);
  if (!value?.trim()) return copy.noNextAction;
  // Callers usually omit the locale; resolve the Owner's preference so English stays English.
  if (locale !== "en" && HOST_ACTIONS[value.trim()]) return HOST_ACTIONS[value.trim()];
  if (/^Investigate failure classification$/i.test(value.trim())) {
    return copy.investigateFailure;
  }
  return runtimeExplanation(value);
}

export function taskBlockerCopy(value: string | undefined, locale?: UiLocale): string {
  const copy = taskCopy(locale);
  if (!value?.trim()) return copy.noBlocker;
  if (/planner_failed:opencode_timeout:\d+/i.test(value)) {
    return copy.plannerTimeout;
  }
  if (/^(?:codex|claude_code)_no_product_changes$/.test(value.trim())) {
    return copy.noProductChanges;
  }
  return runtimeExplanation(value);
}

export function taskReviewNotice(locale?: UiLocale): string {
  return taskCopy(locale).reviewNotice;
}
