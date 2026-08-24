import { test, expect, open, settle } from "./fixtures";

test("renders only reachable seeded states", async ({ appPage }) => {
  await open(appPage, "/");
  await settle(appPage);
  await expect(appPage.getByTestId("goal-state-label")).toContainText("正在执行");
  await open(appPage, "/runs");
  await settle(appPage);
  await expect(appPage.getByTestId("run-state-task-demo-1")).toContainText("等待人工审查");
  await expect(appPage.getByTestId("run-state-task-demo-2")).toContainText("运行中");
  await expect(appPage.getByTestId("run-state-task-demo-queued")).toContainText("QUEUED");
});
