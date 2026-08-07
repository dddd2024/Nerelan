import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SettingsPage } from "@/routes/settings";
import { resetDefaultModelControlClientForTests } from "@/lib/model-control-client";
import { renderWithProviders } from "./test-utils";

describe("model settings workspace", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("replaces the placeholder with model profile controls", async () => {
    renderWithProviders(<SettingsPage />);

    expect(
      await screen.findByRole("heading", { name: "模型配置" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("配置页面正在开发中。")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "新建配置" })).toBeInTheDocument();
    expect(await screen.findByText("默认代码模型")).toBeInTheDocument();
  });

  it("creates a profile without persisting its API key in browser storage", async () => {
    const localStorageSpy = vi.spyOn(Storage.prototype, "setItem");
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);

    await screen.findByText("默认代码模型");
    await user.click(screen.getByRole("button", { name: "新建配置" }));
    await user.type(screen.getByLabelText("配置 ID"), "sensenova-code");
    await user.type(screen.getByLabelText("配置名称"), "商汤代码模型");
    await user.selectOptions(screen.getByLabelText("Provider"), "openai-compatible");
    await user.selectOptions(screen.getByLabelText("执行器"), "openhands");
    await user.clear(screen.getByLabelText("Base URL"));
    await user.type(
      screen.getByLabelText("Base URL"),
      "https://api.example.com/v1",
    );
    await user.type(screen.getByLabelText("Model ID"), "sensenova-code");
    await user.type(
      screen.getByLabelText("API Key（仅本次提交）"),
      "secret-value",
    );
    await user.click(screen.getByRole("button", { name: "保存配置" }));

    expect(
      await screen.findByRole("heading", { name: "商汤代码模型" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("API Key（仅本次提交）")).toHaveValue("");
    expect(localStorageSpy).not.toHaveBeenCalled();
    localStorageSpy.mockRestore();
  });

  it("tests, sets default and deletes a saved profile", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);

    await screen.findByText("默认代码模型");
    await user.click(screen.getByRole("button", { name: "测试连接" }));
    expect(await screen.findByText("连接成功")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "新建配置" }));
    await user.type(screen.getByLabelText("配置 ID"), "review-model");
    await user.type(screen.getByLabelText("配置名称"), "审查模型");
    await user.clear(screen.getByLabelText("Base URL"));
    await user.type(
      screen.getByLabelText("Base URL"),
      "http://localhost:4000/v1",
    );
    await user.type(screen.getByLabelText("Model ID"), "review-strong");
    await user.click(screen.getByRole("button", { name: "保存配置" }));

    await user.click(screen.getByRole("button", { name: "设为默认" }));
    await waitFor(() => {
      expect(screen.getByText("默认配置")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "删除配置" }));
    expect(await screen.findByText("配置已删除")).toBeInTheDocument();
    expect(screen.queryByText("审查模型")).not.toBeInTheDocument();
  });
});
