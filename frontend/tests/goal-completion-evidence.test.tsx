import { expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes, useLocation } from "react-router";
import { GoalProgress } from "@/components/goal-progress";
import type { PlatformGoal, PlatformGoalTaskLink } from "@/lib/platform-client";
import type { FunctionalValidation } from "@/types";
import { renderWithProviders } from "./test-utils";

const verified: FunctionalValidation = {
  status: "VERIFIED", verified: true, contract_digest: "a".repeat(64), result_digest: "b".repeat(64),
  base_commit: "c".repeat(40), head: "d".repeat(40), tree: "e".repeat(40), run_id: "run-bound", lease_epoch: 2,
  checks: [{ profile_id: "python_pytest", working_directory: ".", exit_code: 0, timed_out: false,
    test_report: { format: "junit", tests: 3, passed: 2, failed: 0, skipped: 1, accepted: true } }],
};

function goal(changes: Partial<PlatformGoalTaskLink> = {}): PlatformGoal {
  return {
    id: "goal-bound", title: "Current goal", objective: "A working implementation", repository: "owner/repo",
    status: "COMPLETED", revision: 1, spec_markdown: "", plan_markdown: "", artifact_digest: "f".repeat(64),
    tasks: [{ id: "T001", title: "Implementation", dependencies: [] }], acceptance_criteria: [],
    executor_kind: "opencode", orchestration_mode: "single", binding_ref: "binding", window_id: "window",
    created_at: "2026-09-12T00:00:00Z", updated_at: "2026-09-12T00:00:00Z",
    completion_scope: "EXECUTION_ONLY", remote_acceptance: "NOT_OBSERVED",
    task_links: [{ task_id: "task-bound", plan_task_id: "T001", title: "Implementation", status: "READY_FOR_REVIEW",
      executor_kind: "opencode", functional_validation: verified, publication: null, ...changes }],
  };
}

function status() { return screen.getByTestId("goal-functional-status-task-bound"); }

it("shows current functional acceptance, pending review and inspectable exact evidence separately", async () => {
  renderWithProviders(<GoalProgress goal={goal()} />);
  expect(status()).toHaveTextContent("功能已验证");
  expect(status()).toBeVisible();
  expect(screen.getByText("执行完成，待审查")).toBeVisible();
  expect(screen.getByTestId("goal-publication-task-bound")).toHaveTextContent("尚无发布记录");
  expect(screen.getByText(/远端审查、合并与交付尚未确认/)).toBeVisible();
  expect(screen.getByText(verified.tree!)).not.toBeVisible();
  await userEvent.click(screen.getByText("查看功能检查", { selector: "summary" }));
  expect(screen.getByText("共 3 项 · 通过 2 · 失败 0 · 跳过 1")).toBeVisible();
  // The component's nested evidence disclosure is explicit as well.
  await userEvent.click(screen.getByText("查看验证证据", { selector: "summary" }));
  expect(screen.getByText(verified.tree!)).toBeVisible();
  expect(screen.getByText(verified.result_digest!)).toBeVisible();
});

it.each([
  ["missing", undefined],
  ["stale", { ...verified, status: "UNVERIFIED", verified: false, reason: "execution_changed" }],
  ["no implementation", { status: "UNVERIFIED", verified: false, reason: "no_coder_product_diff" }],
  ["invalid identity", { ...verified, result_digest: "stale" }],
  ["missing report", { ...verified, checks: [{ ...verified.checks![0], test_report: undefined }] }],
  ["nonzero exit", { ...verified, checks: [{ ...verified.checks![0], exit_code: 1 }] }],
  ["zero executed tests", { ...verified, checks: [{ ...verified.checks![0], test_report: { format: "junit", tests: 0, passed: 0, failed: 0, skipped: 0, accepted: true } }] }],
])("does not infer verification from completed execution with %s proof", (_, evidence) => {
  renderWithProviders(<GoalProgress goal={goal({ functional_validation: evidence as FunctionalValidation | undefined })} />);
  expect(status()).toHaveTextContent("功能尚未验证");
  expect(screen.getByText("执行完成，待审查")).toBeVisible();
  expect(screen.queryByText("功能已验证")).not.toBeInTheDocument();
});

it("keeps a real failed check visible without converting failed execution to success", () => {
  renderWithProviders(<GoalProgress goal={{ ...goal({ status: "FAILED", functional_validation: {
    ...verified, status: "FAILED", verified: false, checks: [{ ...verified.checks![0], exit_code: 1,
      test_report: { format: "junit", tests: 3, passed: 1, failed: 1, skipped: 1, accepted: false } }],
  } }), status: "BLOCKED" }} />);
  expect(status()).toHaveTextContent("功能检查未通过");
  expect(screen.getByText("需要处理阻塞")).toBeVisible();
  expect(screen.getByTestId("goal-progress-summary")).toHaveTextContent("0/1");
  expect(screen.queryByText("功能已验证")).not.toBeInTheDocument();
});

it.each(["missing executor", "fixture executor", "fixture lifecycle"])("does not promote a %s using Goal-level provenance", (kind) => {
  const task = kind === "missing executor" ? { executor_kind: undefined }
    : kind === "fixture executor" ? { executor_kind: "deterministic_fixture" as const }
      : { status: "READY_FOR_REVIEW_FIXTURE" };
  renderWithProviders(<GoalProgress goal={goal(task)} />);
  expect(status()).toHaveTextContent("功能尚未验证");
  expect(screen.queryByText("功能已验证")).not.toBeInTheDocument();
});

it("shows actual fixture validation as fixture-only evidence", () => {
  renderWithProviders(<GoalProgress goal={goal({ status: "READY_FOR_REVIEW_FIXTURE", executor_kind: "deterministic_fixture",
    functional_validation: { ...verified, status: "FIXTURE_VERIFIED", verified: false } })} />);
  expect(status()).toHaveTextContent("仅测试夹具通过");
  expect(screen.getByText("Fixture 完成，待审查")).toBeVisible();
  expect(screen.queryByText("功能已验证")).not.toBeInTheDocument();
});

it.each([
  ["PENDING", "等待发布"], ["COMMIT_CREATED", "提交已生成，尚未发布"], ["PUSHED", "分支已推送，Draft 尚未确认"],
  ["COMPLETE", "已记录 Draft PR #42"], ["FAILED", "发布未完成"], ["MERGED", "发布记录不完整，Draft 尚未确认"],
])("keeps publication %s independent of functional proof and current remote acceptance", (publication, label) => {
  renderWithProviders(<GoalProgress goal={goal({ publication: { status: publication, branch: "codex/result", pr_number: 42,
    pr_url: "https://github.com/owner/repo/pull/42", commit_sha: "1".repeat(40) } })} />);
  expect(status()).toHaveTextContent("功能已验证");
  expect(screen.getByTestId("goal-publication-task-bound")).toHaveTextContent(label);
  expect(screen.getByText(/远端审查、合并与交付尚未确认/)).toBeVisible();
  expect(screen.queryByText("已交付")).not.toBeInTheDocument();
});

it("downgrades a newer unverified response even when a Draft publication record is present", () => {
  const view = renderWithProviders(<GoalProgress goal={goal()} />);
  expect(status()).toHaveTextContent("功能已验证");
  view.rerender(<GoalProgress goal={goal({ functional_validation: { status: "UNVERIFIED", verified: false },
    publication: { status: "COMPLETE", branch: "codex/result", pr_number: 42, pr_url: "https://github.com/owner/repo/pull/42", commit_sha: "1".repeat(40) } })} />);
  expect(status()).toHaveTextContent("功能尚未验证");
  expect(screen.getByTestId("goal-publication-task-bound")).toHaveTextContent("已记录 Draft PR #42");
  expect(screen.queryByText("功能已验证")).not.toBeInTheDocument();
});

it.each(["missing", "empty"])("shows an unlaunched plan without synthetic runtime links when task_links is %s", (kind) => {
  renderWithProviders(<GoalProgress goal={{ ...goal(), status: "PLANNED", task_links: kind === "empty" ? [] : undefined }} />);
  expect(screen.getByText("Implementation")).toBeVisible();
  expect(screen.getByText("尚未启动")).toBeVisible();
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
  expect(screen.queryByTestId("goal-functional-status-T001")).not.toBeInTheDocument();
});

function SelectedRun() {
  const location = useLocation();
  return <output data-testid="selected-task">{new URLSearchParams(location.search).get("task")}</output>;
}

it("navigates using the exact materialized task identity, including encoded characters", async () => {
  const taskId = "task /?&目标";
  renderWithProviders(<Routes>
    <Route path="/" element={<GoalProgress goal={goal({ task_id: taskId })} />} />
    <Route path="/runs" element={<SelectedRun />} />
  </Routes>);
  await userEvent.click(screen.getByRole("link", { name: "查看 Implementation 的运行" }));
  expect(screen.getByTestId("selected-task")).toHaveTextContent(taskId);
});
