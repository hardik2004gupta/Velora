"use client";

import Link from "next/link";
import {
  BarChart3,
  DollarSign,
  Clock,
  ArrowUpRight,
  AlertCircle,
  MessageSquare,
  Database,
  Activity,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardOverview } from "@/hooks/useAnalytics";
import { useRequests } from "@/hooks/useRequests";
import { useCacheStats } from "@/hooks/useApiKeys";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";

const PROVIDER_COLORS: Record<string, string> = {
  openai: "text-green-400",
  anthropic: "text-orange-400",
  gemini: "text-blue-400",
};

function formatCost(usd: number): string {
  if (usd === 0) return "$0.0000";
  if (usd < 0.0001) return `$${usd.toExponential(2)}`;
  return `$${usd.toFixed(4)}`;
}

function formatLatency(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms)}ms`;
}

function formatRequestLatency(ms: number | null): string {
  if (ms === null) return "—";
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${ms}ms`;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function StatCard({
  title,
  value,
  description,
  icon: Icon,
  color,
  bg,
  loading,
}: {
  title: string;
  value: string | null;
  description: string;
  icon: React.ElementType;
  color: string;
  bg: string;
  loading: boolean;
}) {
  return (
    <div className="rounded-xl border border-border/60 bg-card/60 p-4 space-y-3 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">{title}</span>
        <div className={cn("rounded-lg p-1.5", bg)}>
          <Icon className={cn("h-3.5 w-3.5", color)} />
        </div>
      </div>
      {loading || value === null ? (
        <Skeleton className="h-7 w-28" />
      ) : (
        <div className="text-2xl font-bold tracking-tight">{value}</div>
      )}
      <p className="text-[11px] text-muted-foreground">{description}</p>
    </div>
  );
}

export default function DashboardPage() {
  const { data: overview, isLoading: overviewLoading, error: overviewError } = useDashboardOverview(30);
  const { data: recentData, isLoading: recentLoading } = useRequests({ limit: 5, sortBy: "created_at", sortDir: "desc" });
  const { data: cacheData, isLoading: cacheLoading } = useCacheStats();
  const user = useAuthStore((s) => s.user);

  const firstName = user?.full_name?.split(" ")[0] ?? "there";

  const statCards = [
    {
      title: "Total Requests",
      value: overviewLoading ? null : (overview?.total_requests.toLocaleString() ?? "—"),
      description: "Last 30 days",
      icon: BarChart3,
      color: "text-velora-400",
      bg: "bg-velora-500/10",
      loading: overviewLoading,
    },
    {
      title: "Total Cost",
      value: overviewLoading ? null : (overview ? formatCost(overview.total_cost_usd) : "—"),
      description: "USD spent last 30 days",
      icon: DollarSign,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      loading: overviewLoading,
    },
    {
      title: "Avg Latency",
      value: overviewLoading ? null : (overview ? formatLatency(overview.avg_latency_ms) : "—"),
      description: "Across all providers",
      icon: Clock,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      loading: overviewLoading,
    },
    {
      title: "Conversations",
      value: overviewLoading ? null : (overview?.total_conversations.toLocaleString() ?? "—"),
      description: "Distinct threads",
      icon: MessageSquare,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      loading: overviewLoading,
    },
    {
      title: "Cache Hit Rate",
      value: cacheLoading ? null : (cacheData ? `${Math.round(cacheData.hit_rate * 100)}%` : "—"),
      description: `${cacheData?.hits ?? 0} hits · ${cacheData?.cached_entries ?? 0} entries`,
      icon: Database,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10",
      loading: cacheLoading,
    },
  ];

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">
            Good {getTimeOfDay()}, {firstName}
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Here&apos;s your inference activity overview.
          </p>
        </div>
        <Link
          href="/playground"
          className="flex items-center gap-2 rounded-lg bg-velora-500 px-4 py-2 text-sm font-medium text-white hover:bg-velora-600 transition-colors"
        >
          <MessageSquare className="h-3.5 w-3.5" />
          New chat
        </Link>
      </div>

      {overviewError && (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-xs text-destructive">
          <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
          Could not load overview stats: {String(overviewError)}
        </div>
      )}

      {/* Stats grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {statCards.map((stat, i) => (
          <div key={stat.title} style={{ animationDelay: `${i * 50}ms` }}>
            <StatCard {...stat} />
          </div>
        ))}
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        {/* Recent requests */}
        <div className="rounded-xl border border-border/60 bg-card/60">
          <div className="flex items-center justify-between border-b border-border/50 px-4 py-3">
            <div>
              <h2 className="text-sm font-semibold">Recent Requests</h2>
              <p className="text-[11px] text-muted-foreground">Your latest inference calls</p>
            </div>
            <Link
              href="/history"
              className="flex items-center gap-1 text-[11px] text-velora-400 hover:underline"
            >
              View all <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="p-3 space-y-1.5">
            {recentLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center justify-between rounded-lg px-3 py-2.5">
                  <div className="space-y-1.5">
                    <Skeleton className="h-3 w-28" />
                    <Skeleton className="h-2.5 w-20" />
                  </div>
                  <div className="space-y-1.5 flex flex-col items-end">
                    <Skeleton className="h-3 w-14" />
                    <Skeleton className="h-2.5 w-16" />
                  </div>
                </div>
              ))
            ) : recentData?.items.length === 0 ? (
              <div className="rounded-lg border border-dashed border-border/50 p-6 text-center">
                <p className="text-xs text-muted-foreground">
                  No requests yet.{" "}
                  <Link href="/playground" className="text-velora-400 hover:underline">
                    Start chatting
                  </Link>{" "}
                  to see your history here.
                </p>
              </div>
            ) : (
              recentData?.items.map((req) => (
                <Link
                  key={req.id}
                  href={`/history/${req.request_id ?? req.id}`}
                  className="flex items-center justify-between rounded-lg px-3 py-2.5 hover:bg-muted/40 transition-colors group"
                >
                  <div className="flex flex-col gap-0.5 min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          "text-[13px] font-medium capitalize truncate",
                          PROVIDER_COLORS[req.provider] ?? "text-foreground"
                        )}
                      >
                        {req.model}
                      </span>
                      {req.status === "success" ? (
                        <Badge variant="success" className="text-[9px] px-1.5 py-0 h-4">ok</Badge>
                      ) : (
                        <Badge variant="destructive" className="text-[9px] px-1.5 py-0 h-4">{req.status}</Badge>
                      )}
                    </div>
                    <span className="text-[11px] text-muted-foreground truncate max-w-[180px]">
                      {req.prompt ?? req.provider}
                    </span>
                  </div>
                  <div className="flex flex-col items-end gap-0.5 shrink-0 ml-3">
                    <span className="text-[13px] font-mono text-muted-foreground">
                      {formatCost(req.cost_usd)}
                    </span>
                    <span className="text-[11px] text-muted-foreground/60">
                      {formatRequestLatency(req.latency_ms)} · {timeAgo(req.created_at)}
                    </span>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Provider health */}
        <div className="rounded-xl border border-border/60 bg-card/60">
          <div className="flex items-center justify-between border-b border-border/50 px-4 py-3">
            <div>
              <h2 className="text-sm font-semibold">Provider Status</h2>
              <p className="text-[11px] text-muted-foreground">Real-time provider health</p>
            </div>
            <Link
              href="/providers"
              className="flex items-center gap-1 text-[11px] text-velora-400 hover:underline"
            >
              View all <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="p-3 space-y-1.5">
            {(["OpenAI", "Anthropic", "Google Gemini"] as const).map((provider) => (
              <div
                key={provider}
                className="flex items-center justify-between rounded-lg px-3 py-2.5"
              >
                <div className="flex items-center gap-2.5">
                  <div className="h-2 w-2 rounded-full bg-muted animate-pulse" />
                  <span className="text-[13px] font-medium">{provider}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Skeleton className="h-3.5 w-12" />
                  <Skeleton className="h-5 w-16 rounded-full" />
                </div>
              </div>
            ))}
            <div className="mt-2 rounded-lg border border-dashed border-border/50 p-3 text-center">
              <p className="text-[11px] text-muted-foreground">
                Live health data on the{" "}
                <Link href="/providers" className="text-velora-400 hover:underline">
                  Providers
                </Link>{" "}
                page.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid gap-3 sm:grid-cols-3">
        {[
          {
            href: "/playground",
            icon: MessageSquare,
            title: "Playground",
            desc: "Chat with any provider",
            color: "text-velora-400",
            bg: "bg-velora-500/10",
          },
          {
            href: "/inspector",
            icon: Activity,
            title: "Inspector",
            desc: "Inspect routing decisions",
            color: "text-purple-400",
            bg: "bg-purple-500/10",
          },
          {
            href: "/analytics",
            icon: BarChart3,
            title: "Analytics",
            desc: "Cost & latency trends",
            color: "text-emerald-400",
            bg: "bg-emerald-500/10",
          },
        ].map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center gap-3 rounded-xl border border-border/60 bg-card/40 px-4 py-3 hover:border-border hover:bg-card/80 transition-all group"
          >
            <div className={cn("rounded-lg p-2 shrink-0", item.bg)}>
              <item.icon className={cn("h-4 w-4", item.color)} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium">{item.title}</p>
              <p className="text-[11px] text-muted-foreground truncate">{item.desc}</p>
            </div>
            <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground/40 ml-auto shrink-0 group-hover:text-muted-foreground transition-colors" />
          </Link>
        ))}
      </div>
    </div>
  );
}

function getTimeOfDay(): string {
  const h = new Date().getHours();
  if (h < 12) return "morning";
  if (h < 17) return "afternoon";
  return "evening";
}
