import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import type { PropsWithChildren } from "react";
import { useTasks, SIDEBAR_TASK_REFRESH_MS } from "@/hooks/use-tasks";
import { fetchTasks } from "@/lib/task-client";

vi.mock("@/lib/task-client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/task-client")>()),
  fetchTasks: vi.fn(),
}));

afterEach(() => {
  vi.clearAllMocks();
});

// Regression for #1201: a Goal launched from a different route materializes
// a Task while the user is still viewing an older task's detail page.
test("sidebar's watched task query discovers newly created Tasks without navigation", async () => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  let visible = [
    { id: "old", title: "Old task", status: "FAILED",
      updated_at: "2026-10-17T06:04:09Z", repository: "dddd2024/Nerelan" },
  ];
  vi.mocked(fetchTasks).mockImplementation(async () => [...visible]);
  const wrapper = ({ children }: PropsWithChildren) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  const { result, unmount } = renderHook(() => useTasks({ watch: true }), { wrapper });
  try {
    await waitFor(() => expect(result.current.data?.[0]?.id).toBe("old"));
    visible = [
      { id: "new", title: "New background task", status: "QUEUED",
        updated_at: "2026-10-17T07:48:22Z", repository: "dddd2024/Nerelan" },
      ...visible,
    ];
    await waitFor(
      () => expect(result.current.data?.some((task) => task.id === "new")).toBe(true),
      { timeout: SIDEBAR_TASK_REFRESH_MS + 2_000 },
    );
    expect(vi.mocked(fetchTasks).mock.calls.length).toBeGreaterThanOrEqual(2);
  } finally {
    unmount();
    client.clear();
  }
}, SIDEBAR_TASK_REFRESH_MS + 5_000);
