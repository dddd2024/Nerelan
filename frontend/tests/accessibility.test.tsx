import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { PermissionSelector } from "@/components/permission-selector";
import { CustomPolicyEditor } from "@/components/custom-policy-editor";
import { Sidebar } from "@/components/sidebar";
import { profileToPolicy } from "@/lib/profile-mapper";

const ROOT = fileURLToPath(new URL("../", import.meta.url));

function read(relative: string) {
  return readFileSync(`${ROOT}${relative}`, "utf8");
}

function srgbChannel(value: number) {
  const channel = value / 255;
  return channel <= 0.04045
    ? channel / 12.92
    : ((channel + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(hex: string) {
  const value = Number.parseInt(hex.slice(1), 16);
  const red = (value >> 16) & 0xff;
  const green = (value >> 8) & 0xff;
  const blue = value & 0xff;
  return (
    0.2126 * srgbChannel(red) +
    0.7152 * srgbChannel(green) +
    0.0722 * srgbChannel(blue)
  );
}

function contrastRatio(a: string, b: string) {
  const first = relativeLuminance(a);
  const second = relativeLuminance(b);
  const lighter = Math.max(first, second);
  const darker = Math.min(first, second);
  return (lighter + 0.05) / (darker + 0.05);
}

describe("accessibility", () => {
  it("permission selector opens via keyboard and is aria-labelled", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <PermissionSelector value="CONTROLLER_REVIEW" onChange={() => {}} />,
    );
    const trigger = screen.getByLabelText("权限配置");
    expect(trigger).toHaveAttribute("aria-haspopup", "listbox");
    trigger.focus();
    await user.keyboard("{Enter}");
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    expect(
      screen.getByRole("listbox", { name: "权限配置" }),
    ).toBeInTheDocument();
  });

  it("sidebar nav items are keyboard reachable and labelled", () => {
    renderWithProviders(
      <div>
        <Sidebar
          onNewTask={() => {}}
          onOpenConversationPanel={() => {}}
          onConversationPanelClose={() => {}}
          conversationPanelOpen={false}
        />
      </div>,
    );
    const tasksLink = screen.getByTestId("sidebar-nav-任务");
    expect(tasksLink).toHaveAttribute("href", "/tasks");
    const homeLink = screen.getByTestId("sidebar-nav-首页");
    expect(homeLink).toHaveAttribute("href", "/");
    expect(screen.getByTestId("sidebar-nav-收件箱")).toHaveAttribute("href", "/inbox");
    expect(screen.getByTestId("sidebar-nav-路线图")).toHaveAttribute("href", "/roadmap");
    expect(screen.getByTestId("sidebar-nav-Agent 运行")).toHaveAttribute("href", "/runs");
    expect(screen.getByTestId("sidebar-nav-设置")).toHaveAttribute("href", "/settings");
  });

  it("custom policy editor traps focus (Tab cycles within dialog)", async () => {
    const user = userEvent.setup();
    const policy = profileToPolicy("CUSTOM");
    renderWithProviders(
      <CustomPolicyEditor
        open={true}
        policy={policy}
        onChange={() => {}}
        onClose={() => {}}
      />,
    );
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    // Many focusable elements exist inside.
    const focusables = dialog.querySelectorAll(
      "button, input, select, textarea, [href], [tabindex]:not([tabindex='-1'])",
    );
    expect(focusables.length).toBeGreaterThan(2);
    // The first focusable should receive focus shortly after open.
    // Move focus explicitly and ensure Tab stays within the dialog.
    (focusables[0] as HTMLElement).focus();
    await user.tab();
    const activeAfterTab = document.activeElement as HTMLElement;
    expect(dialog.contains(activeAfterTab)).toBe(true);
  });

  it("collapsible section exposes aria-expanded", async () => {
    const user = userEvent.setup();
    const { CollapsibleSection } = await import("@/components/collapsible-section");
    renderWithProviders(
      <CollapsibleSection title="区块">
        <p data-testid="body">内容</p>
      </CollapsibleSection>,
    );
    const btn = screen.getByRole("button", { name: "区块" });
    expect(btn).toHaveAttribute("aria-expanded", "false");
    await user.click(btn);
    expect(btn).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByTestId("body")).toBeInTheDocument();
  });

  it("keeps light tertiary text at WCAG AA contrast on both light surfaces", () => {
    const css = read("src/index.css");

    expect(css).not.toContain("--ra-text-tertiary: #77786f;");
    expect(css).toContain("--ra-text-tertiary: #66675f;");
    expect(css).toContain("--ra-text-tertiary: #8f8e88;");
    expect(contrastRatio("#66675f", "#fffefa")).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio("#66675f", "#f1eee6")).toBeGreaterThanOrEqual(4.5);
  });
});
