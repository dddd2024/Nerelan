import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { InboxPage } from "@/routes/inbox";


describe("Human Inbox page", () => {
  it("renders the composer and seeded mock item", async () => {
    renderWithProviders(<InboxPage />);
    expect(screen.getByRole("heading", { name: /想法收件箱/ })).toBeInTheDocument();
    expect(screen.getByLabelText("描述想法")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText("支持定时触发的无人值守窗口")).toBeInTheDocument(),
    );
    expect(
      screen.getByText(/捕获的内容只是展示状态，不具备执行权限/),
    ).toBeInTheDocument();
  });

  it("captures a new inert idea", async () => {
    const user = userEvent.setup();
    renderWithProviders(<InboxPage />);
    await user.type(screen.getByLabelText("描述想法"), "夜间自动处理积压任务");
    await user.click(screen.getByTestId("inbox-capture-button"));
    await waitFor(() =>
      expect(screen.getAllByText("夜间自动处理积压任务").length).toBeGreaterThan(0),
    );
  });

  it("promotes a captured item to a DRAFT goal once and keeps history", async () => {
    const user = userEvent.setup();
    renderWithProviders(<InboxPage />);
    await user.type(screen.getByLabelText("描述想法"), "晋升这条想法");
    await user.click(screen.getByTestId("inbox-capture-button"));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /晋升 晋升这条想法/ })).toBeInTheDocument(),
    );
    await user.click(screen.getByRole("button", { name: /晋升 晋升这条想法/ }));
    await waitFor(() =>
      expect(screen.getByText("已晋升为目标")).toBeInTheDocument(),
    );
    expect(screen.queryByRole("button", { name: /晋升 晋升这条想法/ })).not.toBeInTheDocument();
  });

  it("dismisses a captured item without deleting history", async () => {
    const user = userEvent.setup();
    renderWithProviders(<InboxPage />);
    await user.type(screen.getByLabelText("描述想法"), "忽略这条想法");
    await user.click(screen.getByTestId("inbox-capture-button"));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /忽略 忽略这条想法/ })).toBeInTheDocument(),
    );
    await user.click(screen.getByRole("button", { name: /忽略 忽略这条想法/ }));
    await waitFor(() => expect(screen.getByText("已忽略")).toBeInTheDocument());
    expect(screen.getByText("忽略这条想法")).toBeInTheDocument();
  });
});
