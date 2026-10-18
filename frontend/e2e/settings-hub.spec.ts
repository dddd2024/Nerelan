import { test, expect, open, settle } from "./fixtures";

test("settings hub opens independent sections without mixing their controls", async ({ appPage }) => {
  await open(appPage, "/settings");
  await settle(appPage);
  await expect(appPage.getByTestId("settings-hub")).toBeVisible();
  await expect(appPage.getByTestId("settings-model-access-layout")).toHaveCount(0);
  await expect(appPage.getByTestId("theme-selector")).toHaveCount(0);

  for (const [name, route] of [
    ["AI 资源与账号", "/settings/resources"],
    ["用量与额度", "/settings/usage"],
    ["Agent 与执行", "/settings/agents"],
    ["外观", "/settings/appearance"],
  ] as const) {
    await appPage.getByRole("link", { name: new RegExp(name) }).click();
    await expect(appPage).toHaveURL(new RegExp(route.replaceAll("/", "\\/") + "$"));
    await expect(appPage.getByTestId("settings-subpage").or(appPage.getByTestId("settings-page"))).toBeVisible();
    await appPage.getByRole("link", { name: /返回设置/ }).click();
    await expect(appPage.getByTestId("settings-hub")).toBeVisible();
  }

  await appPage.getByRole("link", { name: /AI 资源与账号/ }).click();
  await expect(appPage.getByTestId("settings-model-access-layout")).toBeVisible();
  await expect(appPage.getByTestId("theme-selector")).toHaveCount(0);
  await appPage.getByRole("link", { name: /返回设置/ }).click();
  await appPage.getByRole("link", { name: /外观/ }).click();
  await expect(appPage.getByTestId("theme-selector")).toBeVisible();
  await expect(appPage.getByTestId("settings-model-access-layout")).toHaveCount(0);
});
