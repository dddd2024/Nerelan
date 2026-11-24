import { Link, useLocation } from "react-router";
import { Compass } from "lucide-react";
import { PageSurface } from "@/components/page-header";

/** An address the app does not know: say so, and offer the two ways back. */
export function NotFoundPage() {
  const location = useLocation();
  return (
    <PageSurface data-testid="not-found-page">
      <div className="mx-auto max-w-md rounded-2xl border border-dashed border-ra-border px-6 py-12 text-center">
        <Compass className="mx-auto h-6 w-6 text-ra-text-tertiary" aria-hidden="true" />
        <h1 className="mt-3 text-base font-medium text-ra-text">没有这个页面</h1>
        <p className="mt-1.5 break-all text-sm leading-6 text-ra-text-secondary">
          地址 <code className="font-mono text-xs">{location.pathname}</code> 不存在，可能是链接写错了或页面已移走。
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
          <Link to="/" className="inline-flex min-h-9 items-center rounded-md bg-ra-accent px-3 text-sm text-ra-base focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent focus-visible:ring-offset-2">
            回到首页
          </Link>
          <Link to="/goals" className="inline-flex min-h-9 items-center rounded-md border border-ra-border px-3 text-sm text-ra-text-secondary hover:bg-ra-tertiary focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
            查看所有目标
          </Link>
        </div>
      </div>
    </PageSurface>
  );
}
