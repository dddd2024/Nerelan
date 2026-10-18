/** Short user-facing copy over machine status; original identifiers remain in diagnostics. */
export function taskActionCopy(value: string | undefined): string {
  if (!value?.trim()) return "暂无下一步操作";
  if (/^Investigate failure classification$/i.test(value.trim())) {
    return "查看任务失败原因和执行记录";
  }
  return value;
}

export function taskBlockerCopy(value: string | undefined): string {
  if (!value?.trim()) return "无";
  if (/planner_failed:opencode_timeout:\d+/i.test(value)) {
    return "Agent 在规划阶段超时，执行记录中有详细原因";
  }
  if (/^(?:codex|claude_code)_no_product_changes$/.test(value.trim())) {
    return "任务没有产生预期的文件修改";
  }
  return value;
}

export function taskReviewNotice(): string {
  return "任务已进入待审查状态；可以查看变更和验证结果。";
}
