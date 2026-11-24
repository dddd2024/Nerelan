import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StepRetry, poolLabel } from "@/components/step-retry";
import type { PlatformRetryOptions } from "@/lib/platform-client";
import { CLIENT_CREDENTIAL_MISSING } from "@/lib/http-errors";

const OPTIONS: PlatformRetryOptions = {
  available: true, reason: "", revision: 4, routing_retries_left: 1,
  pool: [{ binding_ref: "b-kimi", model_id: "kimi-k3", executor_id: "opencode" },
    { binding_ref: "b-codex", model_id: "", executor_id: "" }],
  automatic_retries_left: { T001: 1 },
};

function mount(options?: PlatformRetryOptions) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <StepRetry goalId="goal-1" planTaskId="T001" options={options} />
    </QueryClientProvider>,
  );
}

function stubFetch(status: number, body: unknown) {
  const fetchMock = vi.fn(async () => new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => vi.unstubAllGlobals());

describe("StepRetry", () => {
  it("asks for a window when none is active", () => {
    mount({ ...OPTIONS, available: false, reason: "owner_retry_no_active_window", pool: [] });
    expect(screen.getByTestId("goal-retry-unavailable-T001").textContent).toBe("要重试这一步，先开一个执行窗口。");
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("retries with the router's choice and says what it costs", async () => {
    const fetchMock = stubFetch(200, { id: "goal-1" });
    mount(OPTIONS);
    expect(screen.getByText(/还会自动重试 1 次/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /重试（自动选模型）/ }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toContain("/api/goals/goal-1/tasks/T001/retry");
    expect(JSON.parse(String(init.body))).toEqual({ expected_revision: 4, binding_ref: "" });
  });

  it("retries with a model from the window's pool", async () => {
    const fetchMock = stubFetch(200, { id: "goal-1" });
    mount(OPTIONS);
    const pick = screen.getByRole("button", { name: "用这个模型重试" }) as HTMLButtonElement;
    expect(pick.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("换一个模型"), { target: { value: "b-kimi" } });
    fireEvent.click(pick);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({ expected_revision: 4, binding_ref: "b-kimi" });
  });

  it("offers only the automatic choice without a confirmed pool", () => {
    mount({ ...OPTIONS, pool: [] });
    expect(screen.queryByLabelText("换一个模型")).toBeNull();
  });

  it("names the host's reason when it refuses", async () => {
    stubFetch(409, { error: "owner_retry_model_outside_window" });
    mount(OPTIONS);
    fireEvent.click(screen.getByRole("button", { name: /重试（自动选模型）/ }));
    expect((await screen.findByRole("alert")).textContent).toBe("这个模型不在本窗口确认过的模型里。");
  });

  it("says a missing credential plainly instead of a generic failure", async () => {
    stubFetch(401, { error: "client_session_required" });
    mount(OPTIONS);
    fireEvent.click(screen.getByRole("button", { name: /重试（自动选模型）/ }));
    expect((await screen.findByRole("alert")).textContent).toBe(CLIENT_CREDENTIAL_MISSING);
  });

  it("labels pool entries by model and agent", () => {
    expect(poolLabel(OPTIONS.pool[0])).toBe("kimi-k3 · opencode");
    expect(poolLabel(OPTIONS.pool[1])).toBe("b-codex");
  });
});
