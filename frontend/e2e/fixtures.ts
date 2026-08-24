import { test as base, expect, type Page } from "@playwright/test";

const FIXED_NOW = "2026-08-24T12:00:00.000Z";

export const test = base.extend<{ appPage: Page }>({
  appPage: async ({ page, context }, use) => {
    await context.addInitScript(({ fixedNow }) => {
      const RealDate = Date;
      const fixedTime = RealDate.parse(fixedNow);
      class FixedDate extends RealDate {
        constructor(...args: ConstructorParameters<typeof Date>) {
          if (args.length === 0) super(fixedTime);
          else super(...args);
        }
        static now() { return fixedTime; }
      }
      globalThis.Date = FixedDate;
    }, { fixedNow: FIXED_NOW });
    await page.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      if (url.origin === "http://127.0.0.1:4173" || url.protocol === "data:" || url.protocol === "blob:") {
        await route.continue();
      } else {
        await route.abort("blockedbyclient");
      }
    });
    await use(page);
  },
});

export { expect };

export async function open(page: Page, path: string) {
  await page.goto(path);
  await expect(page.locator("#root")).toBeVisible();
}

export async function settle(page: Page) {
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => document.fonts?.ready);
  await page.waitForTimeout(150);
}

export async function disableMotion(page: Page) {
  await page.addStyleTag({ content: "*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}" });
}
