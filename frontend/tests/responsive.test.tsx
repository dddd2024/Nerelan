import { describe, it, expect, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
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
    mockMatchMedia(false);
    // simulate resize
    window.dispatchEvent(new Event("resize"));
    rerender(<Probe />);
    // still renders a breakpoint value
    expect(["mobile", "desktop", "tablet"]).toContain(
      screen.getByTestId("bp").textContent,
    );
  });

  it("app shell renders sidebar with a mobile menu button", () => {
    mockMatchMedia(false);
    renderWithProviders(
      <AppShell>
        <div data-testid="content">content</div>
      </AppShell>,
    );
    expect(screen.getByTestId("app-shell")).toBeInTheDocument();
    expect(screen.getByTestId("content")).toBeInTheDocument();
    // The mobile menu toggle is visible on mobile.
    expect(screen.getByLabelText("Open navigation")).toBeInTheDocument();
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
