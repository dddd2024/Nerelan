import { test, expect, open, settle } from "./fixtures";

const routes = [
  ["/", "platform-home"],
  ["/tasks", "tasks-page"],
  ["/goals", "goals-page"],
  ["/approvals", "approvals-page"],
  ["/runs", "runs-page"],
  ["/accounts", "accounts-page"],
  ["/settings", "settings-hub"],
] as const;

function routeLabel(path: string) {
  return path === "/tasks"
    ? "任务"
    : path === "/goals"
      ? "目标"
      : path === "/approvals"
        ? "审批"
        : path === "/runs"
          ? "运行记录"
          : path === "/accounts"
            ? "账户"
            : "设置";
}

test("keeps every product route reachable through task-first desktop IA", async ({ appPage }) => {
  await open(appPage, "/");
  await settle(appPage);
  if (await appPage.evaluate(() => window.innerWidth <= 500)) {
    for (const [path, testId] of routes.slice(1)) {
      await appPage.getByTestId("mobile-menu-button").click();
      const link = appPage.getByTestId("mobile-nav-" + routeLabel(path));
      await expect(link).toBeVisible();
      await link.focus();
      await expect(link).toBeFocused();
      await link.click();
      await settle(appPage);
      await expect(appPage.getByTestId(testId)).toBeVisible();
      await expect(appPage.getByTestId("mobile-drawer")).toBeHidden();
    }
  } else {
    // 目标 is a top route; every other route sits in the bottom 更多 menu, which closes after a choice.
    const menu = appPage.getByTestId("sidebar-menu");
    const openMenu = async () => {
      if (!(await menu.evaluate((el) => (el as HTMLDetailsElement).open))) {
        await menu.locator("summary").click();
      }
    };
    for (const [path, testId] of routes.slice(1, -1)) {
      const label = routeLabel(path);
      if (label !== "目标") await openMenu();
      const link = appPage.getByTestId("sidebar-nav-" + label);
      await expect(link).toBeVisible();
      await link.focus();
      await expect(link).toBeFocused();
      await link.click();
      await settle(appPage);
      await expect(appPage.getByTestId(testId)).toBeVisible();
    }

    await openMenu();
    const settings = appPage.getByTestId("sidebar-nav-设置");
    await expect(settings).toBeVisible();
    await settings.click();
    await settle(appPage);
    await expect(appPage.getByTestId("settings-hub")).toBeVisible();
    await openMenu();
    await expect(settings).toHaveAttribute("aria-current", "page");
  }
});
