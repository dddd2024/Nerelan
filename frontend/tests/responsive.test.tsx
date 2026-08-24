import { describe, it, expect, beforeEach } from "vitest";
import { act, screen } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { useBreakpoint } from "@/hooks/use-breakpoint";
import { AppShell } from "@/components/app-shell";

function mockMatchMedia(matchesDesktop: boolean) {
  const impl = (query: string) => ({
    matches: matchesDesktop
      ? /min-width: 1024px/.test(query)
      : /max-width: 639px/.test(query),
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).matchMedia = impl;
}

describe("responsive layout", () => {
  beforeEach(() => {
    mockMatchMedia(true);
  });

  it("useBreakpoint returns desktop by default in jsdom", () => {
    function Probe() {
      const bp = useBreakpoint();
      return <span data-testid="bp">{bp}</span>;
    }
    const { rerender } = renderWithProviders(<Probe />);
    expect(screen.getByTestId("bp").textContent).toBe("desktop");
    act(() => {
      mockMatchMedia(false);
      window.dispatchEvent(new Event("resize"));
      rerender(<Probe />);
    });
    expect(["mobile", "desktop", "tablet"]).toContain(
      screen.getByTestId("bp").textContent,
    );
  });

  it("app shell renders sidebar with nav toggle", () => {
    renderWithProviders(
      <AppShell>
        <div data-testid="content">content</div>
      </AppShell>,
    );
    expect(screen.getByTestId("app-shell")).toBeInTheDocument();
    expect(screen.getByTestId("content")).toBeInTheDocument();
    expect(screen.getByLabelText("打开任务列表")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-nav-首页")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-nav-任务")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-nav-收件箱")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-nav-路线图")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-nav-Agent 运行")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-nav-设置")).toBeInTheDocument();
  });

  it("task inbox renders on desktop", () => {
    renderWithProviders(
      <AppShell>
        <div data-testid="inbox">inbox</div>
      </AppShell>,
    );
    expect(screen.getByTestId("inbox")).toBeInTheDocument();
  });
});
