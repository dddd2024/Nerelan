import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";
import { renderWithProviders } from "./test-utils";
import { SettingsPage } from "@/routes/settings";
import { SettingsHubPage, SettingsAppearancePage, SettingsUsagePage } from "@/routes/settings-sections";
import { resetDefaultModelControlClientForTests } from "@/lib/model-control-client";

beforeEach(() => resetDefaultModelControlClientForTests());

describe("modular settings navigation", () => {
  it("shows a compact index rather than mounting every editor", () => {
    renderWithProviders(<SettingsHubPage />);
    expect(screen.getByTestId("settings-hub")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /AI 资源与账号/ })).toHaveAttribute("href", "/settings/resources");
    expect(screen.getByRole("link", { name: /用量与额度/ })).toHaveAttribute("href", "/settings/usage");
    expect(screen.getByRole("link", { name: /Agent 与执行/ })).toHaveAttribute("href", "/settings/agents");
    expect(screen.getByRole("link", { name: /外观/ })).toHaveAttribute("href", "/settings/appearance");
    expect(screen.queryByTestId("settings-model-access-layout")).not.toBeInTheDocument();
    expect(screen.queryByTestId("theme-selector")).not.toBeInTheDocument();
  });

  it("opens appearance alone and provides a return path", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <Routes>
        <Route path="/settings" element={<SettingsHubPage />} />
        <Route path="/settings/appearance" element={<SettingsAppearancePage />} />
      </Routes>, { initialEntries: ["/settings"] },
    );
    await user.click(screen.getByRole("link", { name: /外观/ }));
    expect(screen.getByRole("heading", { name: "外观", level: 1 })).toBeInTheDocument();
    expect(screen.getByTestId("theme-selector")).toBeInTheDocument();
    expect(screen.queryByTestId("settings-model-access-layout")).not.toBeInTheDocument();
    await user.click(screen.getByRole("link", { name: /返回设置/ }));
    expect(screen.getByTestId("settings-hub")).toBeInTheDocument();
  });

  it("resource settings do not mount usage, agent or appearance sections", async () => {
    renderWithProviders(<SettingsPage section="resources" />);
    expect(await screen.findByTestId("settings-model-access-layout")).toBeInTheDocument();
    expect(screen.queryByTestId("theme-selector")).not.toBeInTheDocument();
    expect(screen.queryByTestId("agent-team-editor")).not.toBeInTheDocument();
  });

  it("usage page identifies observation versus estimate without claiming migrated routing", () => {
    renderWithProviders(<SettingsUsagePage />);
    expect(screen.getByRole("heading", { name: "用量与额度" })).toBeInTheDocument();
    expect(screen.getByText(/界面切换不会迁移账户或修改模型路由/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /返回设置/ })).toHaveAttribute("href", "/settings");
  });
});
