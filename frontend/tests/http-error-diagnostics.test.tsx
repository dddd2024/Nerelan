import type { ReactNode } from "react";
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fetchGoal, fetchGoalsPage, PlatformClientError } from "@/lib/platform-client";
import { goalReadRetryDelay, useGoal } from "@/hooks/use-platform";

beforeEach(() => vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1"));
afterEach(() => {
  cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.unstubAllEnvs(); vi.useRealTimers();
});

describe("request failure evidence", () => {
  it("preserves HTTP overload and bounded timing without query, headers or body data", async () => {
    vi.spyOn(performance, "now").mockReturnValueOnce(10).mockReturnValueOnce(55);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      error: "busy", error_class: "busy", retryable: true, private_payload: "PRIVATE_BODY",
    }), { status: 503, headers: { "X-Nerelan-Request-Id": "0123456789abcdef", "X-Nerelan-Elapsed-Ms": "17" } })));
    const failure = await fetchGoalsPage({ cursor: "PRIVATE_QUERY" }).catch((error: unknown) => error);
    expect(failure).toBeInstanceOf(PlatformClientError);
    expect(failure).toMatchObject({ status: 503, errorClass: "busy", retryable: true,
      diagnostics: { method: "GET", route: "/api/goals", elapsedMs: 45, requestId: "0123456789abcdef", serverElapsedMs: 17 } });
    expect(JSON.stringify(failure)).not.toMatch(/PRIVATE_BODY|PRIVATE_QUERY/);
  });

  it.each([
    [new DOMException("PRIVATE_ERROR", "AbortError"), "cancelled", false],
    [new DOMException("PRIVATE_ERROR", "TimeoutError"), "timeout", true],
    [new TypeError("PRIVATE_ERROR"), "network_error", true],
  ])("keeps browser failure distinctions without guessing a stopped host", async (error, errorClass, retryable) => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(error));
    const failure = await fetchGoal("goal-read").catch((value: unknown) => value);
    expect(failure).toMatchObject({ status: 0, errorClass, retryable });
    expect(String(failure)).not.toContain("PRIVATE_ERROR");
    expect(String(failure)).not.toContain("启动器仍在运行");
  });

  it("preserves a proxy HTTP status when its body is not JSON", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>PRIVATE_PROXY</html>", { status: 502 })));
    const failure = await fetchGoal("goal-read").catch((error: unknown) => error);
    expect(failure).toMatchObject({ status: 502, errorClass: "invalid_response", retryable: true });
    expect(JSON.stringify(failure)).not.toContain("PRIVATE_PROXY");
  });

  it.each([400, 404, 409])("does not retry a non-JSON HTTP%s refusal", async (status) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>refused</html>", { status })));
    await expect(fetchGoal("refused")).rejects.toMatchObject({ status, errorClass: "invalid_response", retryable: false });
  });

  it("classifies cancellation while reading the body and preserves auth failures", async () => {
    const response = new Response();
    vi.spyOn(response, "text").mockRejectedValue(new DOMException("obsolete", "AbortError"));
    const fetch = vi.fn().mockResolvedValueOnce(response)
      .mockResolvedValueOnce(new Response('{"error":"local_client_required","retryable":true}', { status: 401 }));
    vi.stubGlobal("fetch", fetch);
    await expect(fetchGoal("obsolete")).rejects.toMatchObject({ errorClass: "cancelled", retryable: false });
    await expect(fetchGoal("current")).rejects.toMatchObject({ status: 401, retryable: false });
  });

  it("forwards cancellation to an obsolete in-flight read", async () => {
    const controller = new AbortController();
    const fetch = vi.fn((_input: RequestInfo | URL, init?: RequestInit) => new Promise<Response>((_resolve, reject) => {
      init?.signal?.addEventListener("abort", () => reject(new DOMException("obsolete", "AbortError")));
    }));
    vi.stubGlobal("fetch", fetch);
    const pending = fetchGoal("obsolete", controller.signal);
    controller.abort();
    await expect(pending).rejects.toMatchObject({ errorClass: "cancelled", retryable: false });
    expect(fetch).toHaveBeenCalledTimes(1);
  });
});

describe("goal reads", () => {
  function mount(client: QueryClient, id: string) {
    return renderHook(() => useGoal(id), { wrapper: ({ children }: { children: ReactNode }) =>
      <QueryClientProvider client={client}>{children}</QueryClientProvider> });
  }

  it("deduplicates concurrent slow reads using the existing query cache", async () => {
    let complete!: (response: Response) => void;
    const fetch = vi.fn(() => new Promise<Response>((resolve) => { complete = resolve; }));
    vi.stubGlobal("fetch", fetch);
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const first = mount(client, "shared");
    const second = mount(client, "shared");
    expect(fetch).toHaveBeenCalledTimes(1);
    await act(async () => complete(new Response('{"id":"shared","status":"RUNNING"}')));
    await waitFor(() => expect(first.result.current.data?.id).toBe("shared"));
    expect(second.result.current.data?.id).toBe("shared");
    client.clear();
  });

  it("retains cached content during backoff then recovers without an extra poll storm", async () => {
    vi.useFakeTimers();
    vi.spyOn(Math, "random").mockReturnValue(0);
    const fetch = vi.fn().mockResolvedValueOnce(new Response('{"error":"busy","error_class":"busy","retryable":true}', { status: 503 }))
      .mockResolvedValue(new Response('{"id":"cached","status":"COMPLETED"}'));
    vi.stubGlobal("fetch", fetch);
    const client = new QueryClient();
    client.setQueryData(["goals", "cached"], { id: "cached", status: "RUNNING" });
    const hook = mount(client, "cached");
    act(() => { void client.invalidateQueries({ queryKey: ["goals", "cached"] }); });
    await act(async () => { await vi.advanceTimersByTimeAsync(4_000); });
    expect(hook.result.current.data?.id).toBe("cached");
    expect(fetch).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(1_000); });
    expect(fetch).toHaveBeenCalledTimes(2);
    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(hook.result.current.data?.status).toBe("COMPLETED");
    expect(hook.result.current.error).toBeNull();
    client.clear();
  });

  it("stops polling a non-JSON rejection while retaining the cached completed goal", async () => {
    vi.useFakeTimers();
    const fetch = vi.fn(async () => new Response("<html>missing</html>", { status: 404 }));
    vi.stubGlobal("fetch", fetch);
    const client = new QueryClient();
    client.setQueryData(["goals", "missing"], { id: "missing", status: "COMPLETED" });
    const hook = mount(client, "missing");
    act(() => { void client.invalidateQueries({ queryKey: ["goals", "missing"] }); });
    await act(async () => { await vi.advanceTimersByTimeAsync(60_000); });
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(hook.result.current.data?.status).toBe("COMPLETED");
    expect(hook.result.current.error).toMatchObject({ status: 404, retryable: false });
    client.clear();
  });

  it("caps backoff with jitter", () => {
    for (const value of [0, 0.999]) {
      vi.spyOn(Math, "random").mockReturnValue(value);
      expect(goalReadRetryDelay(0)).toBeGreaterThanOrEqual(5_000);
      expect(goalReadRetryDelay(100)).toBe(30_000);
    }
  });
});
