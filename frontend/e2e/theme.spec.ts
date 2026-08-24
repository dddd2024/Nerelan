import { test, expect, open, settle } from "./fixtures";

test.describe("appearance preferences", () => {
  test("supports system, light, dark, accent, reload and media emulation", async ({ appPage }) => {
    await open(appPage, "/settings");
    await settle(appPage);
    await appPage.getByRole("radio", { name: /深色/ }).check({ force: true });
    await appPage.getByRole("radio", { name: /紫色/ }).check({ force: true });
    await expect(appPage.locator("html")).toHaveAttribute("data-theme", "dark");
    await expect(appPage.locator("html")).toHaveAttribute("data-accent", "violet");
    await appPage.reload();
    await expect(appPage.getByTestId("theme-option-dark")).toBeChecked();
    await expect(appPage.getByTestId("accent-option-violet")).toBeChecked();
    await appPage.getByRole("radio", { name: /跟随系统/ }).check({ force: true });
    await appPage.emulateMedia({ colorScheme: "dark" });
    await expect(appPage.locator("html")).toHaveAttribute("data-theme", "system");
    await appPage.getByRole("radio", { name: /浅色/ }).check({ force: true });
    await expect(appPage.locator("html")).toHaveAttribute("data-theme", "light");
  });
});
