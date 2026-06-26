"use client";

import { CheckCircle2, AlertTriangle, XCircle, Zap, RefreshCw, Clock } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useProvidersStatus } from "@/hooks/useAnalytics";
import type { ProviderStatusDetail } from "@/types";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Config maps
// ---------------------------------------------------------------------------

const STATUS_CONFIG = {
  healthy: {
    icon: CheckCircle2,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    badge: "success" as const,
    dot: "bg-emerald-400",
  },
  degraded: {
    icon: AlertTriangle,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    badge: "secondary" as const,
    dot: "bg-amber-400",
  },
  down: {
    icon: XCircle,
    color: "text-red-400",
    bg: "bg-red-500/10",
    badge: "destructive" as const,
    dot: "bg-red-400",
  },
};

const DISPLAY_NAMES: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  gemini: "Google Gemini",
};

const MODEL_LABELS: Record<string, string[]> = {
  openai: ["gpt-4o", "gpt-4o-mini"],
  anthropic: ["claude-sonnet-4-6", "claude-haiku-4-5"],
  gemini: ["gemini-2.0-flash", "gemini-2.0-pro"],
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtMs(ms: number | null) {
  if (ms === null) return "—";
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${ms}ms`;
}

function fmtUptime(v: number | null) {
  if (v === null) return "—";
  return `${v.toFixed(1)}%`;
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  return `${Math.floor(mins / 60)}h ago`;
}

// ---------------------------------------------------------------------------
// Provider card
// ---------------------------------------------------------------------------

function ProviderCard({ p }: { p: ProviderStatusDetail }) {
  const cfg = STATUS_CONFIG[p.status] ?? STATUS_CONFIG.down;
  const Icon = cfg.icon;
  const models = MODEL_LABELS[p.provider] ?? [];

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={cn("rounded-md p-1.5", cfg.bg)}>
              <Zap className={cn("h-4 w-4", cfg.color)} />
            </div>
            <div>
              <CardTitle className="text-base">
                {DISPLAY_NAMES[p.provider] ?? p.provider}
              </CardTitle>
              <p className="text-[11px] text-muted-foreground">
                {p.last_checked_at ? timeAgo(p.last_checked_at) : "never checked"}
              </p>
            </div>
          </div>
          <Badge variant={cfg.badge} className="gap-1 text-xs">
            <Icon className="h-3 w-3" />
            {p.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {p.error_message && (
          <p className="text-[11px] text-destructive/80 bg-destructive/5 border border-destructive/20 rounded px-2 py-1 font-mono">
            {p.error_message}
          </p>
        )}

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">Latency</p>
            <p className="font-medium font-mono">{fmtMs(p.latency_ms)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Avg Latency</p>
            <p className="font-medium font-mono">{fmtMs(p.avg_latency_ms)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Uptime</p>
            <p className="font-medium">{fmtUptime(p.uptime_percentage)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Streaming</p>
            <p className="font-medium text-emerald-400">Supported</p>
          </div>
        </div>

        <div>
          <p className="text-xs text-muted-foreground mb-2">Available models</p>
          <div className="flex flex-wrap gap-1.5">
            {models.map((m) => (
              <Badge key={m} variant="outline" className="text-[10px] font-mono">
                {m}
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Comparison table
// ---------------------------------------------------------------------------

function ComparisonTable({ providers }: { providers: ProviderStatusDetail[] }) {
  if (!providers.length) return null;

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Provider Comparison</CardTitle>
        <CardDescription>Side-by-side health and performance metrics</CardDescription>
      </CardHeader>
      <CardContent>
        {/* Header row */}
        <div className="grid grid-cols-[1.5fr_auto_auto_auto_auto_auto] gap-x-4 pb-2 border-b border-border/50 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          <span>Provider</span>
          <span>Status</span>
          <span>Latency</span>
          <span>Avg Latency</span>
          <span>Uptime</span>
          <span>Streaming</span>
        </div>
        <div className="divide-y divide-border/30">
          {providers.map((p) => {
            const cfg = STATUS_CONFIG[p.status] ?? STATUS_CONFIG.down;
            const Icon = cfg.icon;
            return (
              <div
                key={p.provider}
                className="grid grid-cols-[1.5fr_auto_auto_auto_auto_auto] gap-x-4 py-3 text-xs items-center"
              >
                <span className="font-medium">
                  {DISPLAY_NAMES[p.provider] ?? p.provider}
                </span>
                <Badge variant={cfg.badge} className="gap-1 text-[10px]">
                  <Icon className="h-2.5 w-2.5" />
                  {p.status}
                </Badge>
                <span className="font-mono text-muted-foreground">{fmtMs(p.latency_ms)}</span>
                <span className="font-mono text-muted-foreground">{fmtMs(p.avg_latency_ms)}</span>
                <span className="text-muted-foreground">{fmtUptime(p.uptime_percentage)}</span>
                <span className="text-emerald-400">✓</span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ProvidersPage() {
  const { data, isLoading, error, refetch, lastRefreshed } = useProvidersStatus(60_000);

  const providers = data?.providers ?? [];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Provider Status</h1>
          <p className="text-muted-foreground text-sm">
            Real-time health monitoring for all connected AI providers.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastRefreshed && (
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {timeAgo(lastRefreshed.toISOString())}
            </span>
          )}
          <button
            onClick={refetch}
            disabled={isLoading}
            className="flex items-center gap-1.5 rounded-md border border-border/50 px-3 py-2 text-xs text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-50"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", isLoading && "animate-spin")} />
            Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Provider cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {isLoading
          ? [1, 2, 3].map((i) => (
              <Card key={i} className="border-border/50">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <Skeleton className="h-8 w-32" />
                    <Skeleton className="h-6 w-20 rounded-full" />
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    {[1, 2, 3, 4].map((j) => (
                      <div key={j}>
                        <Skeleton className="h-3 w-16 mb-1" />
                        <Skeleton className="h-4 w-12" />
                      </div>
                    ))}
                  </div>
                  <Skeleton className="h-6 w-full" />
                </CardContent>
              </Card>
            ))
          : providers.map((p) => <ProviderCard key={p.provider} p={p} />)}
      </div>

      {/* Comparison table */}
      {!isLoading && providers.length > 0 && (
        <ComparisonTable providers={providers} />
      )}

      {/* Footer note */}
      <div className="rounded-md border border-dashed border-border/50 p-4 text-center">
        <p className="text-xs text-muted-foreground">
          Health checks run on demand when this page loads and auto-refresh every 60 seconds.
          Results are persisted in the database.
        </p>
      </div>
    </div>
  );
}
