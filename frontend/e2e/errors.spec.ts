import { test, expect, open, settle } from "./fixtures";

test("unknown task identifiers remain recoverable without inventing a state", async ({ appPage }) => {
  await open(appPage, "/runs");
  await settle(appPage);
  await expect(appPage.getByTestId("runs-page")).toBeVisible();
  await expect(appPage.getByTestId("runs-list")).toBeVisible();
  await appPage.goto("/runs?task=unknown-task-for-recovery");
  await settle(appPage);
  await expect(appPage.getByTestId("runs-page")).toBeVisible();
  await expect(appPage.getByTestId("runs-list")).toBeVisible();
  await expect(appPage.getByText("未知任务状态")).toHaveCount(0);
});
