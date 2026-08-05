import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { EvidencePanel } from "@/components/evidence-panel";
import type { EvidenceItem } from "@/types";

const evidence: EvidenceItem[] = [
  {
    id: "e1",
    category: "Authority",
    label: "Approval snapshot",
    value: "APPROVED",
    status: "pass",
    rawJson: JSON.stringify({ body_digest_sha256: "abc123" }, null, 2),
  },
  {
    id: "e2",
    category: "Tests",
    label: "pytest",
    value: "12 passed",
    status: "pass",
  },
  {
    id: "e3",
    category: "Audit",
    label: "Exact-head audit",
    value: "REJECTED",
    status: "fail",
    detail: "missing provenance",
  },
];

describe("evidence panel", () => {
  it("shows summary counts", () => {
    renderWithProviders(<EvidencePanel evidence={evidence} />);
    expect(screen.getByText("2 pass")).toBeInTheDocument();
    expect(screen.getByText("1 fail")).toBeInTheDocument();
  });

  it("collapses raw JSON by default and expands on click", async () => {
    const user = userEvent.setup();
    renderWithProviders(<EvidencePanel evidence={evidence} />);
    // The Authority category section is collapsed by default; expand it.
    const sectionButtons = screen.getAllByRole("button", {
      name: /Authority/i,
    });
    // open the category
    await user.click(sectionButtons[0]);
    const toggle = await screen.findByTestId("evidence-raw-toggle-e1");
    expect(screen.queryByTestId("evidence-raw-e1")).not.toBeInTheDocument();
    await user.click(toggle);
    expect(screen.getByTestId("evidence-raw-e1")).toBeInTheDocument();
    expect(screen.getByTestId("evidence-raw-e1").textContent).toContain(
      "body_digest_sha256",
    );
  });

  it("shows empty state with no evidence", () => {
    renderWithProviders(<EvidencePanel evidence={[]} />);
    expect(screen.getByTestId("evidence-empty")).toBeInTheDocument();
  });
});
