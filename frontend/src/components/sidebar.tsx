import { NavLink, useLocation } from "react-router";
import { Home, ListChecks, ShieldCheck, Settings, X } from "lucide-react";
import { cn } from "@/lib/cn";
import { useEffect, useRef } from "react";

export interface SidebarItem {
  to: string;
  label: string;
  icon: typeof Home;
}

const ITEMS: SidebarItem[] = [
  { to: "/", label: "首页", icon: Home },
  { to: "/tasks", label: "任务", icon: ListChecks },
  { to: "/approvals", label: "审批", icon: ShieldCheck },
  { to: "/settings", label: "设置", icon: Settings },
];

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const location = useLocation();
  const listRef = useRef<HTMLElement>(null);

  // Close mobile drawer on route change.
  useEffect(() => {
    onClose();
  }, [location.pathname, onClose]);

  return (
    <>
      {open ? (
        <button
          type="button"
          aria-label="关闭导航"
          tabIndex={-1}
          onClick={onClose}
          className="fixed inset-0 z-30 bg-slate-900/30 md:hidden"
        />
      ) : null}
      <aside
        ref={listRef}
        aria-label="主导航"
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 transform border-r border-slate-200 bg-white transition-transform duration-200 md:static md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
        data-testid="sidebar"
      >
        <div className="flex h-14 items-center justify-between border-b border-slate-100 px-4">
          <span className="text-sm font-semibold text-slate-800">
            reverse-agent
          </span>
          <button
            type="button"
            aria-label="关闭导航"
            onClick={onClose}
            className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 md:hidden"
          >
            <X aria-hidden="true" className="h-4 w-4" />
          </button>
        </div>
        <nav className="p-2">
          <ul className="space-y-1">
            {ITEMS.map((item, i) => {
              const Icon = item.icon;
              return (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === "/"}
                    onKeyDown={(e) => {
                      // Arrow key navigation between items.
                      const items = Array.from(
                        listRef.current?.querySelectorAll<HTMLAnchorElement>(
                          "a[href]",
                        ) ?? [],
                      );
                      const idx = items.findIndex(
                        (a) => a.getAttribute("href") === item.to,
                      );
                      if (e.key === "ArrowDown" && idx < items.length - 1) {
                        e.preventDefault();
                        items[idx + 1]?.focus();
                      } else if (e.key === "ArrowUp" && idx > 0) {
                        e.preventDefault();
                        items[idx - 1]?.focus();
                      }
                      void i;
                    }}
                    className={({ isActive }) =>
                      cn(
                        "flex items-center gap-2 rounded-md px-3 py-2 text-sm",
                        "focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400",
                        isActive
                          ? "bg-slate-100 font-medium text-slate-900"
                          : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                      )
                    }
                    data-testid={`nav-${item.label.toLowerCase()}`}
                  >
                    <Icon aria-hidden="true" className="h-4 w-4" />
                    <span>{item.label}</span>
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>
    </>
  );
}
