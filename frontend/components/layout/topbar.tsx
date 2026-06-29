"use client";

import { useTheme } from "next-themes";
import { usePathname } from "next/navigation";
import { Moon, Sun, LogOut, Settings, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuthStore } from "@/store/auth";
import { useRouter } from "next/navigation";
import Link from "next/link";

const PAGE_LABELS: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/playground": "Playground",
  "/inspector": "Routing Inspector",
  "/history": "Request History",
  "/analytics": "Analytics",
  "/providers": "Provider Status",
  "/api-keys": "API Keys",
  "/settings": "Settings",
  "/admin": "Admin",
};

export function Topbar() {
  const { theme, setTheme } = useTheme();
  const { user, clearAuth } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  function handleLogout() {
    clearAuth();
    router.push("/login");
  }

  const initials =
    user?.full_name
      ?.split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2) ?? "?";

  const pageLabel =
    Object.entries(PAGE_LABELS).find(([key]) => pathname.startsWith(key))?.[1] ?? "Velora";

  return (
    <header className="flex h-14 items-center justify-between border-b border-border/50 bg-card/40 px-5">
      {/* Page title breadcrumb */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted-foreground/60 font-medium">Velora</span>
        <span className="text-muted-foreground/40">/</span>
        <span className="font-semibold text-foreground">{pageLabel}</span>
      </div>

      <div className="flex items-center gap-1">
        {/* Theme toggle */}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground hover:text-foreground"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Toggle theme"
        >
          <Sun className="h-3.5 w-3.5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-3.5 w-3.5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>

        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="flex h-8 items-center gap-1.5 px-2 text-sm"
            >
              <Avatar className="h-6 w-6">
                <AvatarFallback className="bg-velora-500/20 text-velora-400 text-[10px] font-bold">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <span className="hidden font-medium sm:block max-w-[120px] truncate">
                {user?.full_name ?? "User"}
              </span>
              <ChevronDown className="h-3 w-3 text-muted-foreground/60" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <DropdownMenuLabel className="py-2">
              <div className="flex flex-col gap-0.5">
                <span className="text-sm font-semibold">{user?.full_name}</span>
                <span className="text-[11px] text-muted-foreground font-normal">{user?.email}</span>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/settings" className="flex items-center gap-2 text-sm">
                <Settings className="h-3.5 w-3.5" />
                Settings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="flex items-center gap-2 text-sm text-destructive focus:text-destructive"
              onClick={handleLogout}
            >
              <LogOut className="h-3.5 w-3.5" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
