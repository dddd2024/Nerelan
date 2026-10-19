import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createHttpModelControlClient } from "@/lib/model-control-client";
import { MagpieSettingsEditor } from "@/components/magpie-settings";

const settings = { enabled: false, executable: "", base_url: "http://127.0.0.1:3425" };
function response(body: unknown, ok = true) {
  return { ok, text: async () => JSON.stringify(body) } as Response;
}
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe("Magpie settings", () => {
  it.each(["MAGPIE_DISABLED", "ALREADY_RUNNING", "STARTED", "START_FAILED", "UNREACHABLE"])("shows %s, probe time, reason and model count", async status => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({ settings, runtime: {
      status, reason: "example reason", last_probe_at: "2026-10-19T10:00:00Z", model_count: 9,
    } })));
    render(<MagpieSettingsEditor client={createHttpModelControlClient()} />);
    expect(await screen.findByText(`${status} (example reason)`)).toBeInTheDocument();
    expect(screen.getByText("Models served: 9")).toBeInTheDocument();
    expect(screen.getByText("Last probe: 2026-10-19T10:00:00Z")).toBeInTheDocument();
  });

  it("edits and saves Owner settings", async () => {
    const fetch = vi.fn().mockResolvedValueOnce(response({ settings, runtime: {
      status: "MAGPIE_DISABLED", reason: "", last_probe_at: null, model_count: 0,
    } })).mockResolvedValueOnce(response({ ...settings, enabled: true }));
    vi.stubGlobal("fetch", fetch);
    const user = userEvent.setup();
    render(<MagpieSettingsEditor client={createHttpModelControlClient()} />);
    await user.click(await screen.findByRole("checkbox", { name: "Start Magpie with Nerelan" }));
    await user.type(screen.getByLabelText("Magpie executable"), "F:\\magpie\\magpie.exe");
    await user.clear(screen.getByLabelText("Magpie base URL"));
    await user.type(screen.getByLabelText("Magpie base URL"), "http://localhost:3426");
    await user.click(screen.getByRole("button", { name: "Save Magpie settings" }));
    expect(await screen.findByText("Magpie settings saved.")).toBeInTheDocument();
    expect(JSON.parse(fetch.mock.calls[1][1].body)).toEqual({ enabled: true,
      executable: "F:\\magpie\\magpie.exe", base_url: "http://localhost:3426" });
    expect(fetch.mock.calls[1][1].method).toBe("PUT");
    expect(screen.getByText("Last probe: Never")).toBeInTheDocument();
  });

  it("reports rejected settings without claiming they were saved", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(response({ settings, runtime: {
      status: "MAGPIE_DISABLED", reason: "", last_probe_at: null, model_count: 0,
    } })).mockResolvedValueOnce(response({ error: "Magpie executable must be an existing file" }, false)));
    render(<MagpieSettingsEditor client={createHttpModelControlClient()} />);
    await userEvent.click(await screen.findByRole("button", { name: "Save Magpie settings" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("must be an existing file"));
    expect(screen.queryByText("Magpie settings saved.")).not.toBeInTheDocument();
  });
});
