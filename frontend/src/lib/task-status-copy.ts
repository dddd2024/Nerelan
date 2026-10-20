import { taskCopy, type UiLocale } from "@/lib/ui-locale";

/** Short user-facing copy over machine status; original identifiers remain in diagnostics. */
export function taskActionCopy(value: string | undefined, locale?: UiLocale): string {
  const copy = taskCopy(locale);
  if (!value?.trim()) return copy.noNextAction;
  if (/^Investigate failure classification$/i.test(value.trim())) {
    return copy.investigateFailure;
  }
  return value;
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
  return value;
}

export function taskReviewNotice(locale?: UiLocale): string {
  return taskCopy(locale).reviewNotice;
}
