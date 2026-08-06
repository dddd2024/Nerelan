import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { EvidencePanel } from "@/components/evidence-panel";
import type { EvidenceItem } from "@/types";

const evidence: EvidenceItem[] = [
  {
    id: "e1",
    category: "授权",
    label: "批准快照",
    value: "APPROVED",
    status: "pass",
    rawJson: JSON.stringify({ body_digest_sha256: "abc123" }, null, 2),
  },
  {
    id: "e2",
    category: "测试",
    label: "pytest",
    value: "12 项通过",
    status: "pass",
  },
  {
    id: "e3",
    category: "审计",
    label: "精确 Head 审计",
    value: "REJECTED",
    status: "fail",
    detail: "缺少来源信息",
  },
];

describe("evidence panel", () => {
  it("shows summary counts", () => {
    renderWithProviders(<EvidencePanel evidence={evidence} />);
    expect(screen.getByText("2 通过")).toBeInTheDocument();
    expect(screen.getByText("1 失败")).toBeInTheDocument();
  });

  it("collapses raw JSON by default and expands on click", async () => {
    const user = userEvent.setup();
    renderWithProviders(<EvidencePanel evidence={evidence} />);
    // The 授权 category section is collapsed by default; expand it.
    const sectionButtons = screen.getAllByRole("button", {
      name: /授权/,
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
