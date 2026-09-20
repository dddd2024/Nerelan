import { test, expect, open, settle } from "./fixtures";

test("keeps mock Goal completion unverified and opens its exact Run evidence", async ({ appPage }) => {
  await open(appPage, "/");
  await settle(appPage);
  const task = appPage.getByTestId("goal-task-task-demo-1");
  await expect(task.getByText("执行完成，待审查")).toBeVisible();
  await expect(task.getByTestId("goal-functional-status-task-demo-1")).toHaveText("功能尚未验证");
  await expect(task.getByTestId("goal-publication-task-demo-1")).toHaveText("尚无发布记录");
  await task.getByRole("link", { name: "查看 分析目标与代码库 的运行" }).click();
  await expect(appPage).toHaveURL(/\/runs\?task=task-demo-1$/);
  const selected = appPage.getByRole("region", { name: "选中运行" });
  await expect(selected.getByTestId("run-overview-task-demo-1")).toBeVisible();
  await expect(selected.getByTestId("run-validation-task-demo-1")).toBeVisible();
  await expect(selected.getByText("功能已验证")).toHaveCount(0);
});

// This exercises the visible mock review flow. Real test execution is covered
// separately by the Task API / SQLite / Git acceptance probe, not this fixture.
test("reviews selected functional checks before explicit approval in the mock UI", async ({ appPage }) => {
  await open(appPage, "/");
  await settle(appPage);
  await appPage.getByLabel("描述最终目标").fill("Review functional checks before execution");
  await appPage.getByLabel("执行模式").selectOption("deterministic_fixture");
  await appPage.getByRole("button", { name: "创建并审阅目标" }).click();
  await expect(appPage.getByTestId("approval-goal-detail")).toBeVisible();
  const goalId = new URL(appPage.url()).searchParams.get("goal");
  await appPage.getByTestId("approval-plan-button").click();
  await appPage.getByRole("button", { name: "编辑当前计划" }).click();
  await appPage.getByRole("button", { name: "添加任务 T001 功能检查" }).click();
  const directory = appPage.getByLabel("任务 T001 检查 1 目录");
  await directory.fill("../outside");
  await expect(appPage.getByRole("button", { name: "保存计划修改" })).toBeDisabled();
  await directory.fill(".");
  await appPage.getByRole("button", { name: "保存计划修改" }).click();
  await expect(appPage.getByTestId("approval-plan")).toContainText("功能检查：python_pytest · .");
  await expect(appPage.getByTestId("approval-launch-button")).toHaveCount(0);
  await appPage.getByRole("button", { name: "编辑当前计划" }).click();
  await expect(directory).toHaveValue(".");
  await appPage.getByRole("button", { name: "移除任务 T001 检查 1" }).click();
  await appPage.getByRole("button", { name: "保存计划修改" }).click();
  await expect(appPage.getByTestId("approval-plan")).not.toContainText("功能检查：");
  await appPage.getByTestId("approval-approve-button").click();
  await expect(appPage.getByTestId("approval-launch-button")).toBeDisabled();
  await expect(appPage.getByRole("button", { name: "编辑当前计划" })).toHaveCount(0);
  expect(new URL(appPage.url()).searchParams.get("goal")).toBe(goalId);
});
