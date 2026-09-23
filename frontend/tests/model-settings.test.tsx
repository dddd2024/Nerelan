import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SettingsPage } from "@/routes/settings";
import { getDefaultModelControlClient, resetDefaultModelControlClientForTests } from "@/lib/model-control-client";
import { renderWithProviders } from "./test-utils";

describe("Connection and Binding settings workspace", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("renders the Connection and Binding surface", async () => {
    renderWithProviders(<SettingsPage />);

    expect(
      await screen.findByRole("heading", { name: "连接与绑定" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("配置页面正在开发中。")).not.toBeInTheDocument();
    expect(
      await screen.findByTestId("connection-item-coding-connection"),
    ).toBeInTheDocument();
    expect(
      await screen.findByTestId("binding-item-coding-binding"),
    ).toBeInTheDocument();
  });

  it.each([false, true])("removes stale OAuth continuation when status lookup fails: %s", async (statusUnavailable) => {
    const client = getDefaultModelControlClient();
    await client.upsertConnection({
      connectionId: "gpt-account", name: "GPT account", provider: "openai",
      baseUrl: "https://api.openai.com/v1", authMethod: "account_login", enabled: true,
    });
    vi.spyOn(client, "startAccountAuth").mockResolvedValue({
      status: "awaiting_browser", provider: "openai", callbackMethod: "auto",
      authorizationUrl: "https://auth.example.test/authorize", expiresInSeconds: 300,
    });
    vi.spyOn(client, "completeAccountAuth").mockRejectedValue(new Error("internal model control error"));
    const statusLookup = vi.spyOn(client, "getAccountAuthStatus");
    if (statusUnavailable) {
      statusLookup.mockRejectedValue(new Error("status lookup unavailable"));
    } else {
      statusLookup.mockResolvedValue({
        status: "failed", provider: "openai", externalSessionStatus: "missing",
      });
    }
    const open = vi.spyOn(window, "open").mockReturnValue(null);
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);
    await user.click(await screen.findByTestId("connection-item-gpt-account"));
    expect(screen.queryByText("API Key 只发送到模型控制服务，不写入浏览器存储。")).not.toBeInTheDocument();
    await user.click(screen.getByTestId("account-auth-start"));
    expect(await screen.findByTestId("account-auth-browser-link")).toBeInTheDocument();
    await user.click(screen.getByTestId("account-auth-complete"));
    expect(await screen.findByText(statusUnavailable
      ? "暂时无法确认登录状态，请稍后重试。浏览器授权成功不代表账号连接已完成。"
      : "账号登录未完成。请检查服务端网络配置，然后重新点击浏览器登录。")).toBeInTheDocument();
    if (statusUnavailable) {
      expect(screen.queryByTestId("account-auth-status")).not.toBeInTheDocument();
    } else {
      expect(screen.getByTestId("account-auth-status")).toHaveTextContent("登录失败");
    }
    expect(screen.queryByTestId("account-auth-browser-link")).not.toBeInTheDocument();
    expect(screen.queryByTestId("account-auth-complete")).not.toBeInTheDocument();
    expect(screen.getByTestId("account-auth-start")).toBeEnabled();
    open.mockRestore();
  });

  it("configures a Connection through mock Model Control and never persists its API Key in browser storage", async () => {
    const localStorageSpy = vi.spyOn(Storage.prototype, "setItem");
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);

    await user.click(screen.getByRole("button", { name: "新建连接" }));
    await user.type(screen.getByLabelText("连接 ID"), "test-conn");
    await user.type(screen.getByLabelText("连接名称"), "测试连接");
    await user.clear(screen.getByLabelText("Provider"));
    await user.type(screen.getByLabelText("Provider"), "openai-compatible");
    await user.clear(screen.getByLabelText("Base URL"));
    await user.type(screen.getByLabelText("Base URL"), "https://api.example.com/v1");
    await user.type(screen.getByLabelText("API Key"), "secret-value");
    await user.click(screen.getByRole("button", { name: "保存连接" }));

    expect(await screen.findByText("连接已保存")).toBeInTheDocument();
    expect(localStorageSpy).not.toHaveBeenCalled();
    expect(screen.queryByText("secret-value")).not.toBeInTheDocument();

    const apiKeyField = screen.getByLabelText("API Key") as HTMLInputElement;
    expect(apiKeyField.value).toBe("");

    const secretStatus = screen.getByText("密钥：进程会话");
    expect(secretStatus).toBeInTheDocument();

    localStorageSpy.mockRestore();
  });

  it("creates a Binding that references an enabled Connection and an operational OpenCode executor", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);

    await user.click(screen.getByRole("button", { name: "新建绑定" }));
    await user.type(screen.getByLabelText("绑定 ID"), "test-binding");
    await user.type(screen.getByLabelText("绑定名称"), "测试绑定");
    await user.selectOptions(screen.getByLabelText("执行器"), "opencode");
    await user.selectOptions(screen.getByLabelText("连接"), "coding-connection");
    await user.type(screen.getByLabelText("Model ID"), "test-model");
    await user.click(screen.getByRole("button", { name: "保存绑定" }));

    expect(await screen.findByText("绑定已保存")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "API Key" })).not.toBeInTheDocument();
  });

  it("shows sanitized external-session readiness in the settings list for executor-managed connections", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);

    await user.click(screen.getByRole("button", { name: "新建连接" }));
    await user.type(screen.getByLabelText("连接 ID"), "session-conn");
    await user.type(screen.getByLabelText("连接名称"), "会话连接");
    await user.clear(screen.getByLabelText("Base URL"));
    await user.type(screen.getByLabelText("Base URL"), "https://api.example.com/v1");
    await user.selectOptions(screen.getByLabelText("认证方式"), "account_login");
    await user.click(screen.getByRole("button", { name: "保存连接" }));

    expect(await screen.findByText("连接已保存")).toBeInTheDocument();

    expect(
      await screen.findByTestId("connection-list-external-session-session-conn"),
    ).toHaveTextContent("外部会话：由执行器管理");

    await user.click(await screen.findByTestId("connection-item-session-conn"));
    expect(
      screen.getByTestId("connection-external-session-readiness"),
    ).toHaveTextContent("外部会话状态：由执行器管理");
    expect(screen.getByTestId("test-connection-button")).toBeDisabled();
  });
});
