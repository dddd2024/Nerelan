import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { SettingsPage } from "@/routes/settings";
import { resetDefaultModelControlClientForTests } from "@/lib/model-control-client";
import { renderWithProviders } from "./test-utils";

describe("Settings density contract", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("keeps Settings flat and compact while preserving authoritative controls", async () => {
    renderWithProviders(<SettingsPage />);

    expect(
      await screen.findByRole("heading", { name: "连接与绑定" }),
    ).toBeInTheDocument();

    const page = screen.getByTestId("settings-page");
    expect(page).toHaveClass("lg:px-7", "lg:py-7");

    const credentialNote = screen.getByTestId("settings-credential-note");
    expect(credentialNote).toHaveTextContent("浏览器不会把 API Key 写入 localStorage");
    expect(credentialNote.className).not.toContain("border");
    expect(credentialNote.className).not.toContain("rounded");
    expect(credentialNote.className).not.toContain("bg-ra-secondary");

    const appearance = screen.getByTestId("theme-selector");
    expect(appearance.className).not.toContain("rounded-2xl");
    expect(appearance.className).not.toContain("shadow-");
    expect(appearance.className).not.toContain("bg-ra-light");
    expect(screen.queryByText("presentation only")).not.toBeInTheDocument();
    expect(screen.getByTestId("theme-option-system")).toHaveAttribute("type", "radio");
    expect(screen.getByTestId("accent-option-cyan")).toHaveAttribute("type", "radio");

    const layout = screen.getByTestId("settings-model-access-layout");
    expect(layout.className).toContain("lg:grid-cols-[224px_minmax(0,1fr)]");

    const index = screen.getByTestId("settings-model-access-index");
    expect(index).toHaveClass("self-start");
    expect(index.className).not.toContain("border");
    expect(index.className).not.toContain("rounded-xl");
    expect(index.className).not.toContain("bg-ra-secondary");

    const connection = await screen.findByTestId("connection-item-coding-connection");
    const binding = await screen.findByTestId("binding-item-coding-binding");
    expect(connection.className).not.toContain("border");
    expect(binding.className).not.toContain("border");
    expect(connection).toHaveTextContent("密钥：");
    expect(screen.getByRole("button", { name: "新建连接" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "新建绑定" })).toBeEnabled();
  });
});
