import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";
import { renderWithProviders } from "./test-utils";
import { SettingsPage } from "@/routes/settings";
import { SettingsHubPage, SettingsAppearancePage, SettingsUsagePage } from "@/routes/settings-sections";
import { getDefaultModelControlClient, resetDefaultModelControlClientForTests } from "@/lib/model-control-client";

beforeEach(() => resetDefaultModelControlClientForTests());
afterEach(() => vi.restoreAllMocks());

describe("modular settings navigation", () => {
  it("shows a compact index rather than mounting every editor", () => {
    renderWithProviders(<SettingsHubPage />);
    expect(screen.getByTestId("settings-hub")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /AI 资源与账号/ })).toHaveAttribute("href", "/settings/resources");
    expect(screen.getByRole("link", { name: /用量与额度/ })).toHaveAttribute("href", "/settings/usage");
    expect(screen.getByRole("link", { name: /Agent 与执行/ })).toHaveAttribute("href", "/settings/agents");
    expect(screen.getByRole("link", { name: /外观/ })).toHaveAttribute("href", "/settings/appearance");
    expect(screen.getByRole("link", { name: /模型与路由/ })).toHaveAttribute("href", "/settings/models");
    expect(screen.getByRole("link", { name: /高级配置/ })).toHaveAttribute("href", "/settings/advanced");
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

  it("resource page owns connections and Magpie but not bindings", async () => {
    renderWithProviders(<SettingsPage section="resources" />);
    expect(await screen.findByTestId("connection-item-coding-connection")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "AI 资源与账号", level: 1 })).toBeInTheDocument();
    expect(screen.queryByTestId("binding-item-coding-binding")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /新建连接/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /新建绑定/ })).not.toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Magpie" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "模型与路由" })).toHaveAttribute("href", "/settings/models");
  });

  it("model page owns bindings and does not infer the executed model", async () => {
    renderWithProviders(<SettingsPage section="models" />);
    expect(await screen.findByTestId("binding-item-coding-binding")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "模型与路由", level: 1 })).toBeInTheDocument();
    expect(screen.queryByTestId("connection-item-coding-connection")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /新建连接/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /新建绑定/ })).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Magpie" })).not.toBeInTheDocument();
    expect(screen.getByTestId("settings-section-note")).toHaveTextContent("以运行记录为准");
  });

  it("advanced page keeps every legacy connection and binding entry reachable", async () => {
    renderWithProviders(<SettingsPage section="advanced" />);
    expect(await screen.findByTestId("connection-item-coding-connection")).toBeInTheDocument();
    expect(await screen.findByTestId("binding-item-coding-binding")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /新建连接/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /新建绑定/ })).toBeInTheDocument();
    expect(screen.getByTestId("settings-migration-status")).toBeInTheDocument();
  });

  it("migration status never claims routed migration from an observed Magpie", async () => {
    vi.spyOn(getDefaultModelControlClient(), "getMagpie").mockResolvedValue({
      settings: { enabled: true, executable: "", base_url: "http://127.0.0.1:3425" },
      runtime: { status: "ALREADY_RUNNING", reason: "", last_probe_at: "2026-10-20T00:00:00Z", model_count: 4 },
    });
    renderWithProviders(<SettingsPage section="resources" />);
    expect(await screen.findByText("只读已接入")).toBeInTheDocument();
    expect(screen.getByTestId("migration-routing")).toHaveTextContent("实际路由待验证");
    expect(await screen.findByText("本地连接仍在使用")).toBeInTheDocument();
  });

  it("migration status shows disabled Magpie as not connected", async () => {
    renderWithProviders(<SettingsPage section="resources" />);
    expect(await screen.findByText("未接入")).toBeInTheDocument();
  });

  it("migration status reports an unreadable Magpie as unavailable data, not as offline", async () => {
    vi.spyOn(getDefaultModelControlClient(), "getMagpie").mockRejectedValue(new Error("boom"));
    renderWithProviders(<SettingsPage section="resources" />);
    expect(await screen.findByText("数据不可用")).toBeInTheDocument();
    expect(screen.getByTestId("migration-magpie")).toHaveTextContent("这不代表 Magpie 未运行");
  });
});
