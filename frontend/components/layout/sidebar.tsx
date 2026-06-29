"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  Search,
  History,
  BarChart3,
  Zap,
  Key,
  Settings,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { VeloraIcon } from "@/components/ui/velora-logo";

const NAV_SECTIONS = [
  {
    label: "Core",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/playground", label: "Playground", icon: MessageSquare },
      { href: "/inspector", label: "Inspector", icon: Search },
    ],
  },
  {
    label: "Data",
    items: [
      { href: "/history", label: "History", icon: History },
      { href: "/analytics", label: "Analytics", icon: BarChart3 },
      { href: "/providers", label: "Providers", icon: Zap },
    ],
  },
  {
    label: "Account",
    items: [
      { href: "/api-keys", label: "API Keys", icon: Key },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

function NavItem({
  href,
  label,
  icon: Icon,
  isActive,
}: {
  href: string;
  label: string;
  icon: React.ElementType;
  isActive: boolean;
}) {
  return (
    <li>
      <Link
        href={href}
        className={cn(
          "group relative flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] font-medium transition-all duration-150",
          isActive
            ? "bg-velora-500/10 text-velora-400"
            : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
        )}
      >
        {/* Left accent bar */}
        <span
          className={cn(
            "absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-r-full bg-velora-400 transition-all duration-150",
            isActive ? "opacity-100" : "opacity-0 group-hover:opacity-30"
          )}
        />
        <Icon
          className={cn(
            "h-3.5 w-3.5 shrink-0 transition-colors",
            isActive ? "text-velora-400" : "text-muted-foreground group-hover:text-foreground"
          )}
        />
        {label}
      </Link>
    </li>
  );
}

export function Sidebar() {
  const pathname = usePathname();

  function isActive(href: string) {
    return pathname === href || pathname.startsWith(href + "/");
  }

  return (
    <aside className="flex h-full w-[var(--sidebar-width)] flex-col border-r border-border/50 bg-card/40">
      {/* Logo */}
      <Link
        href="/dashboard"
        className="flex h-14 items-center gap-2.5 border-b border-border/50 px-4 hover:opacity-90 transition-opacity"
      >
        <VeloraIcon size={28} />
        <div className="flex flex-col">
          <span className="text-sm font-bold tracking-tight leading-none">Velora</span>
          <span className="text-[9px] font-medium uppercase tracking-[0.12em] text-muted-foreground/50 mt-0.5 leading-none">
            AI Inference
          </span>
        </div>
      </Link>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-2.5 space-y-4">
        {NAV_SECTIONS.map((section) => (
          <div key={section.label}>
            <p className="mb-1 px-2.5 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/50">
              {section.label}
            </p>
            <ul className="space-y-0.5">
              {section.items.map((item) => (
                <NavItem
                  key={item.href}
                  {...item}
                  isActive={isActive(item.href)}
                />
              ))}
            </ul>
          </div>
        ))}
      </nav>

      {/* Admin */}
      <div className="border-t border-border/50 p-2.5">
        <NavItem
          href="/admin"
          label="Admin"
          icon={Shield}
          isActive={isActive("/admin")}
        />
      </div>
    </aside>
  );
}
