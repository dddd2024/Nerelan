import { test, expect, open, settle } from "./fixtures";

// Mock UI boundary only. Real producer-consumer execution has separate HTTP/Git/SQLite tests.
test("does not infer an artifact input for a task with no dependencies", async ({ appPage }) => {
  await open(appPage, "/");
  await settle(appPage);
  await appPage.getByLabel("描述最终目标").fill("Review explicit accepted artifact input");
  await appPage.getByLabel("执行模式").selectOption("deterministic_fixture");
  await appPage.getByRole("button", { name: "创建并审阅目标" }).click();
  await appPage.getByTestId("approval-plan-button").click();
  await appPage.getByRole("button", { name: "编辑当前计划" }).click();
  const input = appPage.getByLabel("任务 T001 输入产物");
  await expect(input).toHaveValue("");
  await expect(input.locator("option")).toHaveCount(1);
  await appPage.getByRole("button", { name: "添加任务 T001 功能检查" }).click();
  await appPage.getByRole("button", { name: "保存计划修改" }).click();
  await expect(appPage.getByTestId("approval-plan")).not.toContainText("输入产物：");
  await expect(appPage.getByTestId("approval-launch-button")).toHaveCount(0);
});
