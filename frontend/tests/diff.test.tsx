import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { DiffViewer } from "@/components/diff-viewer";
import { ChangesPanel } from "@/components/changes-panel";
import type { ChangedFile } from "@/types";

const diff = `--- a/a.ts
+++ b/a.ts
@@ -1,3 +1,4 @@
 line
-removed
+added
+added2
`;

describe("diff viewer", () => {
  it("renders added and removed lines with colors", () => {
    const { container } = renderWithProviders(<DiffViewer diff={diff} />);
    expect(screen.getByTestId("diff-viewer")).toBeInTheDocument();
    const added = container.querySelectorAll(".bg-\\[\\#014b01AA\\]\\/20");
    const removed = container.querySelectorAll(".bg-\\[\\#750000AA\\]\\/20");
    expect(added.length).toBeGreaterThan(0);
    expect(removed.length).toBeGreaterThan(0);
  });

  it("renders hunk header", () => {
    const { container } = renderWithProviders(<DiffViewer diff={diff} />);
    const hunk = container.querySelectorAll(".bg-\\[\\#525252\\]\\/30");
    expect(hunk.length).toBeGreaterThan(0);
  });
});

describe("changes panel", () => {
  const changes: ChangedFile[] = [
    {
      path: "src/a.ts",
      status: "modified",
      additions: 2,
      deletions: 1,
      diff,
    },
  ];

  it("shows totals and per-file additions/deletions", () => {
    renderWithProviders(<ChangesPanel changes={changes} />);
    expect(screen.getAllByText("+2").length).toBeGreaterThan(0);
    expect(screen.getAllByText("-1").length).toBeGreaterThan(0);
    expect(screen.getByTestId("changes-file-src/a.ts")).toBeInTheDocument();
  });

  it("expands diff on click", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ChangesPanel changes={changes} />);
    const btn = screen.getByTestId("changes-file-src/a.ts");
    await user.click(btn);
    expect(screen.getByTestId("diff-viewer")).toBeInTheDocument();
  });

  it("shows empty state with no changes", () => {
    renderWithProviders(<ChangesPanel changes={[]} />);
    expect(screen.getByTestId("changes-empty")).toBeInTheDocument();
  });
});
