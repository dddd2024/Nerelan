import { readFileSync } from "node:fs";
import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { PermissionSelector } from "@/components/permission-selector";
import { CustomPolicyEditor } from "@/components/custom-policy-editor";
import { Sidebar } from "@/components/sidebar";
import { profileToPolicy } from "@/lib/profile-mapper";

function read(relative: string) {
  return readFileSync(relative, "utf8");
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

/**
 * Every hex declared by an `--ra-accent-tone-*` rule, across all three theme
 * scopes, lowercased and without the leading `#`.
 *
 * Asserting on declarations rather than on the raw file text matters because
 * the tone lists carry comments that intentionally quote the previous hexes to
 * record why they were replaced.
 */
function declaredAccentTones(css: string): string[] {
  return [...css.matchAll(/--ra-accent-tone-[a-z]+(?:-hover)?\s*:\s*#([0-9a-f]{6})\s*;/gi)]
    .map((match) => match[1].toLowerCase());
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

  const LIGHT_SURFACES = ["#f3f4f6", "#ffffff", "#eff0f3", "#e8eaee", "#f8f9fa"];
  const DARK_SURFACES = ["#0f1012", "#1e2024", "#17181b", "#131417", "#25272c"];

  it("keeps tertiary text at WCAG AA contrast on every surface it renders on", () => {
    const css = read("src/index.css");

    expect(css).toContain("--ra-text-tertiary: #5c6069;");
    expect(css).toContain("--ra-text-tertiary: #9599a1;");
    for (const surface of LIGHT_SURFACES) {
      expect(contrastRatio("#5c6069", surface)).toBeGreaterThanOrEqual(4.5);
    }
    for (const surface of DARK_SURFACES) {
      expect(contrastRatio("#9599a1", surface)).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("keeps the light accent and status hues at WCAG AA contrast on every light surface", () => {
    const css = read("src/index.css");

    // The light accent lives in the theme's tone list; `html[data-accent="…"]`
    // only points at it, so the literal must be asserted there.
    expect(css).toContain("--ra-accent-tone-cyan: #0d6a76;");

    for (const value of ["#0d6a76", "#1f7346", "#855a0e", "#b03a33", "#5e6169"]) {
      expect(css).toContain(value);
      for (const surface of LIGHT_SURFACES) {
        expect(contrastRatio(value, surface)).toBeGreaterThanOrEqual(4.5);
      }
    }
  });

  it("keeps every dark accent tone at WCAG AA contrast on every dark surface", () => {
    const css = read("src/index.css");

    // `text-ra-accent` is used for run state, activity verbs and inline links,
    // so each accent has to hold up as *text* on every dark surface, not just
    // as a fill on the workspace.
    for (const stale of ["438cf4", "8a6cf1", "e45b72"]) {
      expect(declaredAccentTones(css), `${stale} must not survive as a dark accent`).not.toContain(stale);
    }

    for (const value of ["#5ab4c0", "#6ba6f7", "#a892f5", "#e0992f", "#ee8598"]) {
      expect(css, `${value} must be declared as a dark accent tone`).toContain(value);
      for (const surface of DARK_SURFACES) {
        expect(
          contrastRatio(value, surface),
          `${value} on ${surface}`,
        ).toBeGreaterThanOrEqual(4.6);
      }
    }
  });

  it("does not ship an unlayered global reset that would defeat padding utilities", () => {
    const css = read("src/index.css");

    // An unlayered `* { margin: 0; padding: 0 }` outranks @layer utilities and
    // silently zeroed every px-*/py-* in the product. Tailwind's preflight
    // already provides the same reset inside @layer base.
    const normalized = css.replace(/\s+/g, " ");
    expect(normalized).not.toContain(
      "*::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }",
    );
    expect(css).toContain('@import "tailwindcss"');
  });
});
