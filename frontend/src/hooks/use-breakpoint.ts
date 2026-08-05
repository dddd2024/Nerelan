import { useEffect, useState } from "react";

export type Breakpoint = "mobile" | "tablet" | "desktop";

const QUERIES: { bp: Breakpoint; query: string }[] = [
  { bp: "desktop", query: "(min-width: 1024px)" },
  { bp: "tablet", query: "(min-width: 640px)" },
  { bp: "mobile", query: "(max-width: 639px)" },
];

function resolveBreakpoint(): Breakpoint {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return "desktop";
  }
  for (const { bp, query } of QUERIES) {
    if (window.matchMedia(query).matches) return bp;
  }
  return "desktop";
}

/**
 * Return the current responsive breakpoint.
 */
export function useBreakpoint(): Breakpoint {
  const [bp, setBp] = useState<Breakpoint>(resolveBreakpoint);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }
    const handler = () => setBp(resolveBreakpoint());
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  return bp;
}

export const BREAKPOINT_LABELS: Record<Breakpoint, string> = {
  mobile: "Mobile",
  tablet: "Tablet",
  desktop: "Desktop",
};
