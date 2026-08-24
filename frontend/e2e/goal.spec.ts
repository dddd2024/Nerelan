import { test, expect, open, settle } from "./fixtures";

test("runs a provider-free goal with a deterministic fixture and bounded window", async ({ appPage }) => {
  await open(appPage, "/");
  await settle(appPage);
  await appPage.getByLabel("描述最终目标").fill("Playwright provider-free acceptance goal");
  await appPage.getByLabel("执行模式").selectOption("deterministic_fixture");
  await appPage.getByLabel("启用 2 小时自治窗口").check();
  await appPage.getByRole("button", { name: "规划并运行" }).click();
  await expect(appPage.getByTestId("goal-progress-bar")).toBeVisible();
  await expect(appPage.getByRole("heading", { name: "Playwright provider-free acceptance goal" })).toBeVisible();
});
