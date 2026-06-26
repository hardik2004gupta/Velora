"use client";

import { useState } from "react";
import {
  BarChart3,
  Coins,
  Clock,
  MessageSquare,
  Zap,
  Route,
  TrendingUp,
  AlertCircle,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  CostAreaChart,
  LatencyLineChart,
  ProviderPieChart,
  StatusDonutChart,
  TokenBarChart,
  RoutingBarChart,
} from "@/components/analytics/charts";
import {
  useDashboardOverview,
  useCostOverTime,
  useLatencyAnalytics,
  useProviderDistribution,
  useTokenAnalytics,
  useConversationAnalytics,
  useRoutingInsights,
} from "@/hooks/useAnalytics";

// ---------------------------------------------------------------------------
// Period selector
// ---------------------------------------------------------------------------

const PERIODS = [
  { label: "24h", days: 1 },
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
] as const;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmt(v: number | undefined | null, decimals = 0) {
  if (v == null) return "—";
  return v.toLocaleString(undefined, { maximumFractionDigits: decimals });
}

function fmtCost(v: number | undefined | null) {
  if (v == null) return "—";
  if (v === 0) return "$0.0000";
  if (v < 0.0001) return `$${v.toExponential(2)}`;
  return `$${v.toFixed(4)}`;
}

function fmtMs(v: number | undefined | null) {
  if (v == null) return "—";
  if (v >= 1000) return `${(v / 1000).toFixed(1)}s`;
  return `${Math.round(v)}ms`;
}

// ---------------------------------------------------------------------------
// Summary stat card
// ---------------------------------------------------------------------------

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  color = "text-velora-400",
  bg = "bg-velora-500/10",
  isLoading,
  error,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  sub?: string;
  color?: string;
  bg?: string;
  isLoading?: boolean;
  error?: string | null;
}) {
  return (
    <Card className="border-border/50">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <div className={`rounded-md p-2 ${bg}`}>
          <Icon className={`h-4 w-4 ${color}`} />
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-7 w-28 mb-1" />
        ) : error ? (
          <p className="text-sm text-destructive">—</p>
        ) : (
          <div className="text-2xl font-bold">{value}</div>
        )}
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Chart wrapper
// ---------------------------------------------------------------------------

function ChartCard({
  title,
  description,
  height = "h-52",
  isLoading,
  error,
  children,
}: {
  title: string;
  description?: string;
  height?: string;
  isLoading?: boolean;
  error?: string | null;
  children: React.ReactNode;
}) {
  return (
    <Card className="border-border/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <div className={`${height} w-full`}>
          {isLoading ? (
            <Skeleton className="h-full w-full rounded-md" />
          ) : error ? (
            <div className="flex h-full items-center justify-center gap-2 text-xs text-destructive">
              <AlertCircle className="h-3.5 w-3.5" /> {error}
            </div>
          ) : (
            children
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Inline stat row
// ---------------------------------------------------------------------------

function InlineStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border/30 last:border-0">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-xs font-medium font-mono">{value}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AnalyticsPage() {
  const [period, setPeriod] = useState(30);

  const overview = useDashboardOverview(period);
  const cost = useCostOverTime(period);
  const latency = useLatencyAnalytics(period);
  const providers = useProviderDistribution(period);
  const tokens = useTokenAnalytics(period);
  const conversations = useConversationAnalytics(period);
  const routing = useRoutingInsights(period);

  // Derived data for charts
  const tokenBarData = tokens.data
    ? [
        {
          name: "Tokens",
          prompt: tokens.data.prompt_tokens,
          completion: tokens.data.completion_tokens,
        },
      ]
    : [];

  const statusData = providers.data
    ? (() => {
        const success = providers.data.providers.reduce(
          (s, p) => s + Math.round((p.success_rate / 100) * p.requests),
          0
        );
        const total = providers.data.total_requests;
        const error = total - success;
        return [
          { name: "success", value: success },
          { name: "error", value: error },
        ].filter((d) => d.value > 0);
      })()
    : [];

  const routingBarData = routing.data
    ? Object.entries(routing.data.strategy_distribution).map(([strategy, count]) => ({
        strategy,
        count,
      }))
    : [];

  const periodLabel =
    period === 1 ? "last 24 hours" : period === 7 ? "last 7 days" : "last 30 days";

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground text-sm">
            Cost, latency, and usage insights across all providers.
          </p>
        </div>

        {/* Period selector */}
        <div className="flex items-center gap-1 rounded-lg border border-border/50 bg-card p-1">
          {PERIODS.map((p) => (
            <button
              key={p.days}
              onClick={() => setPeriod(p.days)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                period === p.days
                  ? "bg-velora-500 text-white"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary cards — 7 stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={BarChart3}
          label="Total Requests"
          value={fmt(overview.data?.total_requests)}
          sub={periodLabel}
          color="text-velora-400"
          bg="bg-velora-500/10"
          isLoading={overview.isLoading}
          error={overview.error}
        />
        <StatCard
          icon={MessageSquare}
          label="Conversations"
          value={fmt(overview.data?.total_conversations)}
          sub={periodLabel}
          color="text-purple-400"
          bg="bg-purple-500/10"
          isLoading={overview.isLoading}
          error={overview.error}
        />
        <StatCard
          icon={Coins}
          label="Total Cost"
          value={fmtCost(cost.data?.total ?? overview.data?.total_cost_usd)}
          sub={periodLabel}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
          isLoading={overview.isLoading || cost.isLoading}
          error={overview.error}
        />
        <StatCard
          icon={Clock}
          label="Avg Latency"
          value={fmtMs(latency.data?.avg_ms ?? overview.data?.avg_latency_ms)}
          sub={periodLabel}
          color="text-amber-400"
          bg="bg-amber-500/10"
          isLoading={overview.isLoading || latency.isLoading}
          error={overview.error}
        />
        <StatCard
          icon={Zap}
          label="Total Tokens"
          value={fmt(tokens.data?.total_tokens)}
          sub={`avg ${fmt(tokens.data?.avg_per_request, 0)}/req`}
          color="text-blue-400"
          bg="bg-blue-500/10"
          isLoading={tokens.isLoading}
          error={tokens.error}
        />
        <StatCard
          icon={TrendingUp}
          label="P50 Latency"
          value={fmtMs(latency.data?.p50_ms)}
          sub="median response time"
          color="text-cyan-400"
          bg="bg-cyan-500/10"
          isLoading={latency.isLoading}
          error={latency.error}
        />
        <StatCard
          icon={TrendingUp}
          label="P95 Latency"
          value={fmtMs(latency.data?.p95_ms)}
          sub="95th percentile"
          color="text-rose-400"
          bg="bg-rose-500/10"
          isLoading={latency.isLoading}
          error={latency.error}
        />
        <StatCard
          icon={Route}
          label="Top Strategy"
          value={routing.data?.most_used_strategy ?? "—"}
          sub={`via ${routing.data?.most_selected_provider ?? "—"}`}
          color="text-orange-400"
          bg="bg-orange-500/10"
          isLoading={routing.isLoading}
          error={routing.error}
        />
      </div>

      {/* Charts — row 1: cost + latency */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Cost Over Time"
          description={`Daily spend by provider — ${periodLabel}`}
          height="h-56"
          isLoading={cost.isLoading}
          error={cost.error}
        >
          <CostAreaChart data={cost.data?.data ?? []} />
        </ChartCard>

        <ChartCard
          title="Average Latency"
          description={`Daily average response time — ${periodLabel}`}
          height="h-56"
          isLoading={latency.isLoading}
          error={latency.error}
        >
          <LatencyLineChart data={latency.data?.data ?? []} />
        </ChartCard>
      </div>

      {/* Charts — row 2: provider pie + status donut */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Provider Distribution"
          description="Request share by provider"
          height="h-56"
          isLoading={providers.isLoading}
          error={providers.error}
        >
          <ProviderPieChart data={providers.data?.providers ?? []} />
        </ChartCard>

        <ChartCard
          title="Request Status"
          description="Success vs error breakdown"
          height="h-56"
          isLoading={providers.isLoading}
          error={providers.error}
        >
          <StatusDonutChart data={statusData} />
        </ChartCard>
      </div>

      {/* Charts — row 3: token bar + routing bar */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Token Usage"
          description="Prompt vs completion tokens"
          height="h-48"
          isLoading={tokens.isLoading}
          error={tokens.error}
        >
          <TokenBarChart data={tokenBarData} />
        </ChartCard>

        <ChartCard
          title="Routing Strategy"
          description="Requests by strategy"
          height="h-48"
          isLoading={routing.isLoading}
          error={routing.error}
        >
          <RoutingBarChart data={routingBarData} />
        </ChartCard>
      </div>

      {/* Detailed stats — row 4: provider table + latency/conversation breakdown */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Provider comparison table */}
        <Card className="border-border/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Provider Comparison</CardTitle>
            <CardDescription>Requests, cost, latency, and success rate</CardDescription>
          </CardHeader>
          <CardContent>
            {providers.isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full rounded" />)}
              </div>
            ) : providers.error ? (
              <p className="text-xs text-destructive">{providers.error}</p>
            ) : !providers.data?.providers.length ? (
              <p className="text-xs text-muted-foreground">No data for this period.</p>
            ) : (
              <>
                {/* Header */}
                <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-3 pb-2 border-b border-border/50 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                  <span>Provider</span>
                  <span>Reqs</span>
                  <span>Cost</span>
                  <span>Latency</span>
                  <span>Success</span>
                </div>
                <div className="divide-y divide-border/30">
                  {providers.data.providers.map((p) => (
                    <div
                      key={p.provider}
                      className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-3 py-2.5 text-xs items-center"
                    >
                      <span className="font-medium capitalize">{p.provider}</span>
                      <span className="text-muted-foreground tabular-nums">{p.requests.toLocaleString()}</span>
                      <span className="font-mono text-muted-foreground tabular-nums">{fmtCost(p.cost)}</span>
                      <span className="text-muted-foreground tabular-nums">
                        {p.avg_latency_ms != null ? fmtMs(p.avg_latency_ms) : "—"}
                      </span>
                      <Badge
                        variant={p.success_rate >= 95 ? "success" : p.success_rate >= 80 ? "secondary" : "destructive"}
                        className="text-[10px]"
                      >
                        {p.success_rate.toFixed(0)}%
                      </Badge>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Detailed stats: latency + tokens + conversations */}
        <div className="space-y-4">
          {/* Latency detail */}
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Latency Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {latency.isLoading ? (
                <Skeleton className="h-20 w-full" />
              ) : (
                <>
                  <InlineStat label="Average" value={fmtMs(latency.data?.avg_ms)} />
                  <InlineStat label="P50 (median)" value={fmtMs(latency.data?.p50_ms)} />
                  <InlineStat label="P95" value={fmtMs(latency.data?.p95_ms)} />
                  {latency.data?.by_provider &&
                    Object.entries(latency.data.by_provider).map(([prov, ms]) => (
                      <InlineStat
                        key={prov}
                        label={`${prov.charAt(0).toUpperCase() + prov.slice(1)} avg`}
                        value={fmtMs(ms)}
                      />
                    ))}
                </>
              )}
            </CardContent>
          </Card>

          {/* Token detail */}
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Token Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {tokens.isLoading ? (
                <Skeleton className="h-20 w-full" />
              ) : (
                <>
                  <InlineStat label="Total tokens" value={fmt(tokens.data?.total_tokens)} />
                  <InlineStat label="Prompt tokens" value={fmt(tokens.data?.prompt_tokens)} />
                  <InlineStat label="Completion tokens" value={fmt(tokens.data?.completion_tokens)} />
                  <InlineStat label="Avg per request" value={fmt(tokens.data?.avg_per_request, 0)} />
                </>
              )}
            </CardContent>
          </Card>

          {/* Conversation detail */}
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Conversation Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {conversations.isLoading ? (
                <Skeleton className="h-12 w-full" />
              ) : (
                <>
                  <InlineStat label="Total conversations" value={fmt(conversations.data?.total_conversations)} />
                  <InlineStat
                    label="Avg messages / conversation"
                    value={fmt(conversations.data?.avg_messages_per_conversation, 1)}
                  />
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
