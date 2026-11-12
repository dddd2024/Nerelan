import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import type { PlatformGoal } from "@/lib/platform-client";
import { PlatformClientError } from "@/lib/platform-client";
import { PlanSteps } from "@/components/plan-steps";
import { bindingLabel, executionModeLabel, quotaFitText } from "@/lib/goal-labels";
import { CLIENT_CREDENTIAL_MISSING, httpErrorMessage } from "@/lib/http-errors";

const GOAL = {
  id: "g1", title: "#9 修复登录", objective: "第一行\n第二行", repository: "o/r", status: "PLANNED", revision: 2,
  spec_markdown: "", plan_markdown: "# Plan: #9\n\n## Execution tasks", acceptance_criteria: ["能登录"],
  artifact_digest: "", executor_kind: "opencode", orchestration_mode: "sequential_team", binding_ref: "magpie-codex-gpt-6.1-sol",
  window_id: "", created_at: "", updated_at: "",
  tasks: [
    { id: "T001", title: "改登录接口", instruction: "修改 api/login.py\n保留旧参数", dependencies: [],
      validation_checks: [{ profile_id: "python_pytest", working_directory: ".", targets: ["tests/test_login.py"] }] },
    { id: "T002", title: "更新文档", instruction: "写明新参数", dependencies: ["T001"] },
  ],
} as unknown as PlatformGoal;

describe("plan steps", () => {
  it("numbers the steps in Chinese and keeps the raw plan folded", () => {
    render(<PlanSteps goal={{ ...GOAL, quota_fit: { status: "needs_a_reset", uncertain: true } }} />);
    expect(screen.getByTestId("plan-step-T001")).toHaveTextContent("第 1 步改登录接口");
    expect(screen.getByTestId("plan-step-T001")).toHaveTextContent("可以最先开始");
    expect(screen.getByTestId("plan-step-T001")).toHaveTextContent("python_pytest（在 .，针对 tests/test_login.py）");
    expect(screen.getByTestId("plan-step-T002")).toHaveTextContent("在第 1 步之后进行");
    expect(screen.getByTestId("plan-step-T002")).toHaveTextContent("没有选择功能检查：只检查补丁格式，不能证明功能正确。");
    expect(screen.getByTestId("approval-quota-fit")).toHaveTextContent("额度要等下一次刷新后才够。（数据不完整，仅供参考） 这只是预测，不会预留额度。");
    expect(screen.getByTestId("approval-plan-markdown").closest("details")).not.toHaveAttribute("open");
    expect(screen.getByTestId("approval-plan")).not.toHaveTextContent("```json");
  });
});

describe("labels", () => {
  it("names each execution mode for what it does", () => {
    expect(executionModeLabel(GOAL)).toBe("OpenCode：规划 → 编码 → 审查");
    expect(executionModeLabel({ executor_kind: "opencode", orchestration_mode: "agent_team" })).toBe("自动（按任务选择 Agent 和模型）");
    expect(executionModeLabel({ executor_kind: "deterministic_fixture", orchestration_mode: "single" })).toBe("无模型演练（只验证平台流程）");
  });

  it("shows the model, not the stored binding id", () => {
    expect(bindingLabel(GOAL)).toBe("codex-gpt-6.1-sol");
    expect(bindingLabel({ binding_ref: "", orchestration_mode: "agent_team", executor_kind: "opencode" })).toBe("自动选择");
    expect(bindingLabel({ binding_ref: "", orchestration_mode: "single", executor_kind: "opencode" })).toBe("未选择");
  });

  it("states the quota forecast as a sentence", () => {
    expect(quotaFitText({ status: "fits_now" })).toBe("按预测，现有额度够完成全部步骤。");
    expect(quotaFitText(null)).toBe("");
  });
});

describe("error messages", () => {
  it("names the real cause", () => {
    expect(httpErrorMessage(401)).toBe(CLIENT_CREDENTIAL_MISSING);
    expect(new PlatformClientError(409, "owner_selection_confirmation_unavailable").message).toContain("请在终端运行 owner_window");
    expect(httpErrorMessage(500, "repository_discovery_failed")).toContain("gh auth login");
    expect(httpErrorMessage(409, "something_new")).toBe("平台请求未完成（something_new）");
  });
});
