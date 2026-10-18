import { describe, expect, it } from "vitest";
import { taskActionCopy, taskBlockerCopy, taskReviewNotice } from "@/lib/task-status-copy";

describe("task details use actionable locale copy without discarding machine evidence", () => {
  it("turns internal retry guidance into plain language", () => {
    expect(taskActionCopy("Investigate failure classification"))
      .toBe("查看任务失败原因和执行记录");
    expect(taskActionCopy(undefined)).toBe("暂无下一步操作");
  });

  it("explains a planner timeout without claiming the task succeeded", () => {
    expect(taskBlockerCopy("planner_failed:opencode_timeout:840"))
      .toContain("规划阶段超时");
    expect(taskBlockerCopy("codex_no_product_changes"))
      .toContain("没有产生预期的文件修改");
  });

  it("preserves unknown messages instead of guessing causes", () => {
    expect(taskActionCopy("Ask Owner to confirm scope")).toBe("Ask Owner to confirm scope");
    expect(taskBlockerCopy("upstream_unknown_reason")).toBe("upstream_unknown_reason");
  });

  it("does not claim review approval or functional verification", () => {
    expect(taskReviewNotice()).toContain("待审查");
    expect(taskReviewNotice()).not.toMatch(/已验证|审查通过/);
  });
});
