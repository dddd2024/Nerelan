import type { CSSProperties } from "react";
import { cn } from "@/lib/cn";

const MARK_ASSET = "/nerelan-mark.svg";
const WORDMARK_ASSET = "/nerelan-wordmark.svg";

function maskStyle(asset: string): CSSProperties {
  return {
    WebkitMaskImage: `url("${asset}")`,
    maskImage: `url("${asset}")`,
    WebkitMaskRepeat: "no-repeat",
    maskRepeat: "no-repeat",
    WebkitMaskPosition: "center",
    maskPosition: "center",
    WebkitMaskSize: "contain",
    maskSize: "contain",
    backgroundColor: "currentColor",
  };
}

interface BrandAssetProps {
  className?: string;
}

export function NerelanMark({ className }: BrandAssetProps) {
  return (
    <span
      aria-hidden="true"
      data-testid="nerelan-mark"
      className={cn("inline-block shrink-0", className)}
      style={maskStyle(MARK_ASSET)}
    />
  );
}

export function NerelanWordmark({ className }: BrandAssetProps) {
  return (
    <span
      aria-hidden="true"
      data-testid="nerelan-wordmark"
      className={cn("inline-block shrink-0", className)}
      style={maskStyle(WORDMARK_ASSET)}
    />
  );
}
