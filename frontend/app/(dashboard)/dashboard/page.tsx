import { Metadata } from "next";
import { BarChart3, Zap, DollarSign, Clock, ArrowUpRight, TrendingUp } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export const metadata: Metadata = { title: "Dashboard" };

const statCards = [
  {
    title: "Total Requests",
    value: "—",
    description: "Last 30 days",
    icon: BarChart3,
    color: "text-velora-400",
    bg: "bg-velora-500/10",
  },
  {
    title: "Total Cost",
    value: "—",
    description: "Last 30 days",
    icon: DollarSign,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
  {
    title: "Avg Latency",
    value: "—",
    description: "Across all providers",
    icon: Clock,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
  },
  {
    title: "Cache Hit Rate",
    value: "—",
    description: "Prompt deduplication",
    icon: Zap,
    color: "text-purple-400",
    bg: "bg-purple-500/10",
  },
];

const recentRequests = [
  { provider: "openai", model: "gpt-4o-mini", status: "success", latency: "820ms", cost: "$0.0002", time: "2m ago" },
  { provider: "anthropic", model: "claude-haiku-4-5", status: "success", latency: "1.2s", cost: "$0.0008", time: "5m ago" },
  { provider: "gemini", model: "gemini-2.0-flash", status: "success", latency: "650ms", cost: "$0.0001", time: "8m ago" },
];

export default function DashboardPage() {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Overview of your AI inference activity.</p>
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title} className="border-border/50">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{stat.title}</CardTitle>
                <div className={`rounded-md p-2 ${stat.bg}`}>
                  <Icon className={`h-4 w-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
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
              <a href="/history" className="flex items-center gap-1 text-xs text-velora-400 hover:underline">
                View all <ArrowUpRight className="h-3 w-3" />
              </a>
            </div>
            <CardDescription>Your latest inference requests</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentRequests.map((req, i) => (
                <div key={i} className="flex items-center justify-between rounded-md border border-border/50 p-3">
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{req.model}</span>
                      <Badge variant="success" className="text-xs">{req.status}</Badge>
                    </div>
                    <span className="text-xs text-muted-foreground capitalize">{req.provider}</span>
                  </div>
                  <div className="flex flex-col items-end gap-0.5">
                    <span className="text-sm font-mono">{req.cost}</span>
                    <span className="text-xs text-muted-foreground">{req.latency} · {req.time}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3 rounded-md border border-dashed border-border/50 p-4 text-center">
              <p className="text-xs text-muted-foreground">
                Connect the backend to see your real requests here.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Provider health */}
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Provider Status</CardTitle>
              <a href="/providers" className="flex items-center gap-1 text-xs text-velora-400 hover:underline">
                View all <ArrowUpRight className="h-3 w-3" />
              </a>
            </div>
            <CardDescription>Real-time provider health</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {["OpenAI", "Anthropic", "Gemini"].map((provider) => (
                <div key={provider} className="flex items-center justify-between rounded-md border border-border/50 p-3">
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
            <div className="mt-3 rounded-md border border-dashed border-border/50 p-4 text-center">
              <p className="text-xs text-muted-foreground">Live data requires backend connection.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
