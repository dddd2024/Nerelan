import * as React from "react";
import { NavLink } from "react-router";
import { 
  Home, 
  Target, 
  Inbox, 
  Map, 
  Activity, 
  Settings,
  ChevronLeft,
  ChevronRight,
  Plus
} from "lucide-react";
import { cn } from "@/lib/cn";

interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
  onNewTask?: () => void;
}

const navigation = [
  { name: "仪表板", href: "/", icon: Home },
  { name: "目标", href: "/goals", icon: Target },
  { name: "任务", href: "/tasks", icon: Activity },
  { name: "收件箱", href: "/inbox", icon: Inbox },
  { name: "路线图", href: "/roadmap", icon: Map },
  { name: "设置", href: "/settings", icon: Settings },
];

export function Sidebar({ collapsed = false, onToggle, onNewTask }: SidebarProps) {
  return (
    <div
      className={cn(
        "flex flex-col h-full bg-ra-sidebar border-r border-ra-border transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-ra-border">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-ra-accent flex items-center justify-center">
              <span className="text-ra-base font-bold text-sm">RA</span>
            </div>
            <span className="font-semibold text-ra-text">Reverse Agent</span>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-2 rounded-lg hover:bg-ra-tertiary text-ra-text-secondary hover:text-ra-text transition-colors"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-ra-accent/10 text-ra-accent"
                  : "text-ra-text-secondary hover:bg-ra-tertiary hover:text-ra-text",
                collapsed && "justify-center"
              )
            }
          >
            <item.icon className="h-5 w-5 shrink-0" />
            {!collapsed && <span>{item.name}</span>}
          </NavLink>
        ))}
      </nav>

      {/* New Task Button */}
      <div className="p-3 border-t border-ra-border">
        <button
          onClick={onNewTask}
          className={cn(
            "w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-ra-accent text-ra-base font-medium hover:bg-ra-accent-hover transition-colors",
            collapsed && "px-2"
          )}
        >
          <Plus className="h-4 w-4" />
          {!collapsed && <span>新建任务</span>}
        </button>
      </div>
    </div>
  );
}
