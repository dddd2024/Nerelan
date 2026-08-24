import { test, expect, open, settle } from "./fixtures";

const routes = [
  ["/", "platform-home"],
  ["/tasks", "tasks-page"],
  ["/inbox", "inbox-page"],
  ["/roadmap", "roadmap-page"],
  ["/runs", "runs-page"],
  ["/settings", "settings-page"],
] as const;

test("navigates across the six accessible product routes", async ({ appPage }) => {
  await open(appPage, "/");
  await settle(appPage);
  if (await appPage.evaluate(() => window.innerWidth <= 500)) {
    for (const [path, testId] of routes.slice(1)) {
      await appPage.getByTestId("mobile-menu-button").click();
      const label = path === "/tasks" ? "任务" : path === "/inbox" ? "收件箱" : path === "/roadmap" ? "路线图" : path === "/runs" ? "Agent 运行" : "设置";
      const link = appPage.getByTestId("mobile-nav-" + label);
      await expect(link).toBeVisible();
      await link.focus();
      await expect(link).toBeFocused();
      await link.click();
      await settle(appPage);
      await expect(appPage.getByTestId(testId)).toBeVisible();
      await expect(link).toHaveClass(/bg-ra-tertiary/);
      await expect(appPage.getByTestId("mobile-drawer")).toBeHidden();
    }
  } else {
    for (const [path, testId] of routes.slice(1)) {
      const label = path === "/tasks" ? "任务" : path === "/inbox" ? "收件箱" : path === "/roadmap" ? "路线图" : path === "/runs" ? "Agent 运行" : "设置";
      await appPage.getByTestId("sidebar-nav-" + label).click();
      await settle(appPage);
      await expect(appPage.getByTestId(testId)).toBeVisible();
      await expect(appPage.getByTestId("sidebar-nav-" + label)).toHaveClass(/bg-ra-tertiary/);
    }
  }
});
