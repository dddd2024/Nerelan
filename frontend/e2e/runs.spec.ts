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
