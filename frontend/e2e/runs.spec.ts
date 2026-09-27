import { test, expect, open, settle } from "./fixtures";

test("expands a run into agents, activity, files and validation", async ({ appPage }) => {
  await open(appPage, "/runs");
  await settle(appPage);
  const first = appPage.getByTestId("run-task-demo-1");
  await first.getByTestId("run-toggle-task-demo-1").click();
  await expect(first.getByTestId("run-agents-task-demo-1")).toBeVisible();
  await expect(first.getByTestId("run-activity-section-task-demo-1")).toBeVisible();
  await expect(first.getByTestId("run-files-task-demo-1")).toBeVisible();
  await expect(first.getByTestId("run-validation-task-demo-1")).toBeVisible();
});

test("confirms a queued cancellation and exposes its terminal state", async ({ appPage }) => {
  await open(appPage, "/runs");
  await settle(appPage);
  const queued = appPage.getByTestId("run-task-demo-queued");
  await queued.getByTestId("run-toggle-task-demo-queued").click();
  await queued.getByTestId("run-cancel-task-demo-queued").click();
  await expect(queued.getByTestId("run-cancel-confirm-task-demo-queued")).toBeVisible();
  await queued.getByRole("button", { name: "确认取消" }).click();
  await expect(queued.getByTestId("run-state-task-demo-queued")).toContainText("CANCELLED");
});

test("identifies each run by task title in the collapsed row and toggle accessible name", async ({ appPage }) => {
  await open(appPage, "/runs");
  await settle(appPage);
  const first = appPage.getByTestId("run-task-demo-1");
  await expect(first.getByText(/T001 分析目标与代码库/)).toBeVisible();
  await expect(first.getByTestId("run-toggle-task-demo-1")).toHaveAttribute(
    "aria-label",
    /运行：.*T001 分析目标与代码库/,
  );
});

test("presents truthful usage for observed and all-unknown runs", async ({ appPage }) => {
  await open(appPage, "/runs");
  await settle(appPage);
  const observed = appPage.getByTestId("run-usage-task-demo-1");
  await expect(observed).toContainText("Tokens 68,420");
  await expect(observed).toContainText("Cost $0.8123");

  const unknown = appPage.getByTestId("run-usage-task-demo-2");
  await expect(unknown).toContainText("用量未知：1 条观测均未提供数值");
  await expect(unknown).not.toContainText("Tokens");
  await expect(unknown).toContainText("UNKNOWN 不是 0");
});

test("keeps unavailable controls compactly disclosed in an expanded run", async ({ appPage }) => {
  await open(appPage, "/runs");
  await settle(appPage);
  const run = appPage.getByTestId("run-task-demo-2");
  await run.getByTestId("run-toggle-task-demo-2").click();
  const cancelDetails = run.getByTestId("run-control-task-demo-2");
  await expect(cancelDetails).not.toHaveAttribute("open");
  await expect(cancelDetails).toContainText("取消排队任务 · 不可用");
  await expect(run.getByTestId("run-cancel-task-demo-2")).toBeDisabled();
});
