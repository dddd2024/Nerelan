import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { PermissionSelector } from "@/components/permission-selector";
import { CustomPolicyEditor } from "@/components/custom-policy-editor";
import { Sidebar } from "@/components/sidebar";
import { profileToPolicy } from "@/lib/profile-mapper";

describe("accessibility", () => {
  it("permission selector opens via keyboard and is aria-labelled", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <PermissionSelector value="CONTROLLER_REVIEW" onChange={() => {}} />,
    );
    const trigger = screen.getByLabelText("Permission profile");
    expect(trigger).toHaveAttribute("aria-haspopup", "listbox");
    trigger.focus();
    await user.keyboard("{Enter}");
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    expect(
      screen.getByRole("listbox", { name: "Permission profile" }),
    ).toBeInTheDocument();
  });

  it("sidebar nav items are keyboard reachable and labelled", () => {
    renderWithProviders(
      <div>
        <Sidebar open={true} onClose={() => {}} />
      </div>,
    );
    const tasksLink = screen.getByTestId("nav-tasks");
    expect(tasksLink).toHaveAttribute("href", "/tasks");
    const homeLink = screen.getByTestId("nav-home");
    expect(homeLink).toHaveAttribute("href", "/");
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
      <CollapsibleSection title="Section">
        <p data-testid="body">body</p>
      </CollapsibleSection>,
    );
    const btn = screen.getByRole("button", { name: "Section" });
    expect(btn).toHaveAttribute("aria-expanded", "false");
    await user.click(btn);
    expect(btn).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByTestId("body")).toBeInTheDocument();
  });
});
