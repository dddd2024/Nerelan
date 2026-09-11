import { test, expect, open, settle } from "./fixtures";

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
