import { Metadata } from "next";
import { BarChart3, TrendingUp, DollarSign, Zap } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export const metadata: Metadata = { title: "Analytics" };

const chartPlaceholders = [
  { title: "Cost Over Time", description: "Daily USD spend", icon: DollarSign },
  { title: "Latency by Provider", description: "P50/P95 latency trends", icon: Zap },
  { title: "Request Volume", description: "Requests per day", icon: TrendingUp },
  { title: "Provider Distribution", description: "Requests by provider", icon: BarChart3 },
];

export default function AnalyticsPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">
          Cost, latency, and usage insights across all providers.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total Cost", sub: "All time" },
          { label: "Avg Latency", sub: "Last 30 days" },
          { label: "Total Tokens", sub: "All time" },
          { label: "Cache Savings", sub: "Estimated" },
        ].map((stat) => (
          <Card key={stat.label} className="border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{stat.label}</CardTitle>
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-24 mb-1" />
              <p className="text-xs text-muted-foreground">{stat.sub}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Chart grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {chartPlaceholders.map((chart) => {
          const Icon = chart.icon;
          return (
            <Card key={chart.title} className="border-border/50">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4 text-velora-400" />
                  <CardTitle className="text-base">{chart.title}</CardTitle>
                </div>
                <CardDescription>{chart.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex h-48 items-center justify-center rounded-md border border-dashed border-border/50">
                  <p className="text-xs text-muted-foreground">
                    Chart renders with live backend data (Phase 3)
                  </p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
