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
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardOverview } from "@/hooks/useAnalytics";
import { useRequests } from "@/hooks/useRequests";
import { useCacheStats } from "@/hooks/useApiKeys";
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

export default function DashboardPage() {
  const { data: overview, isLoading: overviewLoading, error: overviewError } = useDashboardOverview(30);
  const { data: recentData, isLoading: recentLoading } = useRequests({ limit: 5, sortBy: "created_at", sortDir: "desc" });
  const { data: cacheData, isLoading: cacheLoading } = useCacheStats();

  const statCards = [
    {
      title: "Total Requests",
      value: overviewLoading ? null : (overview?.total_requests.toLocaleString() ?? "—"),
      description: "Last 30 days",
      icon: BarChart3,
      color: "text-velora-400",
      bg: "bg-velora-500/10",
    },
    {
      title: "Total Cost",
      value: overviewLoading ? null : (overview ? formatCost(overview.total_cost_usd) : "—"),
      description: "Last 30 days",
      icon: DollarSign,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
    },
    {
      title: "Avg Latency",
      value: overviewLoading ? null : (overview ? formatLatency(overview.avg_latency_ms) : "—"),
      description: "Across all providers",
      icon: Clock,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
    },
    {
      title: "Conversations",
      value: overviewLoading ? null : (overview?.total_conversations.toLocaleString() ?? "—"),
      description: "Distinct conversation threads",
      icon: MessageSquare,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
    },
    {
      title: "Cache Hit Rate",
      value: cacheLoading ? null : (cacheData ? `${Math.round(cacheData.hit_rate * 100)}%` : "—"),
      description: `${cacheData?.hits ?? 0} hits · ${cacheData?.cached_entries ?? 0} entries`,
      icon: Database,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10",
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Overview of your AI inference activity.</p>
      </div>

      {overviewError && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-xs text-destructive">
          <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
          Could not load overview stats: {overviewError}
        </div>
      )}

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title} className="border-border/50">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <div className={`rounded-md p-2 ${stat.bg}`}>
                  <Icon className={`h-4 w-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                {stat.value === null ? (
                  <Skeleton className="h-7 w-24 mt-0.5" />
                ) : (
                  <div className="text-2xl font-bold">{stat.value}</div>
                )}
                <p className="text-xs text-muted-foreground mt-1">{stat.description}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent requests */}
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Recent Requests</CardTitle>
              <Link
                href="/history"
                className="flex items-center gap-1 text-xs text-velora-400 hover:underline"
              >
                View all <ArrowUpRight className="h-3 w-3" />
              </Link>
            </div>
            <CardDescription>Your latest inference requests</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-md border border-border/50 p-3"
                  >
                    <div className="space-y-1.5">
                      <Skeleton className="h-3.5 w-32" />
                      <Skeleton className="h-3 w-20" />
                    </div>
                    <div className="space-y-1.5 items-end flex flex-col">
                      <Skeleton className="h-3.5 w-16" />
                      <Skeleton className="h-3 w-20" />
                    </div>
                  </div>
                ))
              ) : recentData?.items.length === 0 ? (
                <div className="rounded-md border border-dashed border-border/50 p-6 text-center">
                  <p className="text-xs text-muted-foreground">
                    No requests yet. Head to the{" "}
                    <Link href="/playground" className="text-velora-400 hover:underline">
                      Playground
                    </Link>{" "}
                    to get started.
                  </p>
                </div>
              ) : (
                recentData?.items.map((req) => (
                  <Link
                    key={req.id}
                    href={`/history/${req.request_id ?? req.id}`}
                    className="flex items-center justify-between rounded-md border border-border/50 p-3 hover:bg-muted/30 transition-colors"
                  >
                    <div className="flex flex-col gap-0.5 min-w-0">
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "text-sm font-medium capitalize truncate",
                            PROVIDER_COLORS[req.provider] ?? "text-foreground"
                          )}
                        >
                          {req.model}
                        </span>
                        {req.status === "success" ? (
                          <Badge variant="success" className="text-[10px]">ok</Badge>
                        ) : (
                          <Badge variant="destructive" className="text-[10px]">{req.status}</Badge>
                        )}
                      </div>
                      <span className="text-xs text-muted-foreground truncate max-w-[180px]">
                        {req.prompt ?? req.provider}
                      </span>
                    </div>
                    <div className="flex flex-col items-end gap-0.5 flex-shrink-0 ml-3">
                      <span className="text-sm font-mono text-muted-foreground">
                        {formatCost(req.cost_usd)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatRequestLatency(req.latency_ms)} · {timeAgo(req.created_at)}
                      </span>
                    </div>
                  </Link>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Provider health placeholder */}
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Provider Status</CardTitle>
              <Link
                href="/providers"
                className="flex items-center gap-1 text-xs text-velora-400 hover:underline"
              >
                View all <ArrowUpRight className="h-3 w-3" />
              </Link>
            </div>
            <CardDescription>Real-time provider health</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {["OpenAI", "Anthropic", "Gemini"].map((provider) => (
                <div
                  key={provider}
                  className="flex items-center justify-between rounded-md border border-border/50 p-3"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-muted animate-pulse" />
                    <span className="text-sm font-medium">{provider}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Skeleton className="h-4 w-16" />
                    <Skeleton className="h-5 w-16 rounded-full" />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3 rounded-md border border-dashed border-border/50 p-3 text-center">
              <p className="text-xs text-muted-foreground">
                Live health data on the{" "}
                <Link href="/providers" className="text-velora-400 hover:underline">
                  Providers
                </Link>{" "}
                page.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
