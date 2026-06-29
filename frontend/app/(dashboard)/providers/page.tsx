"use client";

import { CheckCircle2, AlertTriangle, XCircle, RefreshCw, Clock, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useProvidersStatus } from "@/hooks/useAnalytics";
import type { ProviderStatusDetail } from "@/types";
import { cn } from "@/lib/utils";

const STATUS_CONFIG = {
  healthy: {
    icon: CheckCircle2,
    textColor: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/20",
    dotColor: "bg-emerald-400",
    label: "Healthy",
    badgeVariant: "success" as const,
  },
  degraded: {
    icon: AlertTriangle,
    textColor: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/20",
    dotColor: "bg-amber-400",
    label: "Degraded",
    badgeVariant: "secondary" as const,
  },
  down: {
    icon: XCircle,
    textColor: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/20",
    dotColor: "bg-red-400",
    label: "Down",
    badgeVariant: "destructive" as const,
  },
};

const PROVIDER_META: Record<string, { label: string; accentColor: string; dotColor: string; textColor: string }> = {
  openai: { label: "OpenAI", accentColor: "border-green-500/20", dotColor: "bg-green-400", textColor: "text-green-400" },
  anthropic: { label: "Anthropic", accentColor: "border-orange-500/20", dotColor: "bg-orange-400", textColor: "text-orange-400" },
  gemini: { label: "Google Gemini", accentColor: "border-blue-500/20", dotColor: "bg-blue-400", textColor: "text-blue-400" },
};

const MODEL_LABELS: Record<string, string[]> = {
  openai: ["gpt-4o", "gpt-4o-mini"],
  anthropic: ["claude-sonnet-4-6", "claude-haiku-4-5"],
  gemini: ["gemini-2.0-flash", "gemini-2.0-pro"],
};

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

function UptimeBar({ value }: { value: number | null }) {
  const pct = value ?? 0;
  const color = pct >= 95 ? "bg-emerald-500" : pct >= 80 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="h-1 w-full overflow-hidden rounded-full bg-muted/50">
      <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
    </div>
  );
}

function MetricCell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground/60 mb-0.5">{label}</p>
      <p className="text-sm font-semibold font-mono">{value}</p>
    </div>
  );
}

function ProviderCard({ p }: { p: ProviderStatusDetail }) {
  const cfg = STATUS_CONFIG[p.status] ?? STATUS_CONFIG.down;
  const StatusIcon = cfg.icon;
  const meta = PROVIDER_META[p.provider] ?? { label: p.provider, accentColor: "", dotColor: "bg-muted-foreground", textColor: "text-muted-foreground" };
  const models = MODEL_LABELS[p.provider] ?? [];

  return (
    <div className={cn(
      "rounded-xl border bg-card/60 overflow-hidden transition-all duration-200 hover:bg-card/80",
      p.status === "healthy" ? meta.accentColor : cfg.borderColor
    )}>
      {/* Top accent line */}
      <div className={cn("h-px w-full", cfg.dotColor, "opacity-60")} />

      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className={cn("flex h-8 w-8 items-center justify-center rounded-lg", cfg.bgColor)}>
              <Zap className={cn("h-4 w-4", cfg.textColor)} />
            </div>
            <div>
              <h3 className="text-sm font-semibold">{meta.label}</h3>
              <p className="text-[10px] text-muted-foreground">
                {p.last_checked_at ? `Checked ${timeAgo(p.last_checked_at)}` : "Never checked"}
              </p>
            </div>
          </div>
          <div className={cn("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium", cfg.textColor, cfg.bgColor, cfg.borderColor)}>
            <span className={cn("h-1.5 w-1.5 rounded-full", cfg.dotColor)} />
            {cfg.label}
          </div>
        </div>

        {/* Error message */}
        {p.error_message && (
          <div className="mb-4 rounded-lg border border-destructive/20 bg-destructive/5 px-3 py-2">
            <p className="text-[11px] font-mono text-destructive/80 truncate">{p.error_message}</p>
          </div>
        )}

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <MetricCell label="Latency" value={fmtMs(p.latency_ms)} />
          <MetricCell label="Avg Latency" value={fmtMs(p.avg_latency_ms)} />
        </div>

        {/* Uptime bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground/60">Uptime</span>
            <span className="text-xs font-semibold font-mono">{fmtUptime(p.uptime_percentage)}</span>
          </div>
          <UptimeBar value={p.uptime_percentage} />
        </div>

        {/* Streaming + models */}
        <div className="pt-3 border-t border-border/40">
          <div className="flex items-center gap-2 mb-2.5">
            <span className="text-[10px] font-medium text-muted-foreground/60 uppercase tracking-wider">Streaming</span>
            <span className="text-[11px] font-medium text-emerald-400">Supported</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {models.map((m) => (
              <span
                key={m}
                className="rounded-md border border-border/50 bg-muted/30 px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground"
              >
                {m}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ProviderCardSkeleton() {
  return (
    <div className="rounded-xl border border-border/60 bg-card/60 overflow-hidden">
      <div className="h-px w-full bg-muted" />
      <div className="p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Skeleton className="h-8 w-8 rounded-lg" />
            <div className="space-y-1">
              <Skeleton className="h-3.5 w-20" />
              <Skeleton className="h-2.5 w-16" />
            </div>
          </div>
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><Skeleton className="h-2.5 w-12 mb-1" /><Skeleton className="h-4 w-10" /></div>
          <div><Skeleton className="h-2.5 w-12 mb-1" /><Skeleton className="h-4 w-10" /></div>
        </div>
        <Skeleton className="h-1.5 w-full rounded-full" />
        <div className="flex gap-1.5 pt-2">
          <Skeleton className="h-5 w-20 rounded-md" />
          <Skeleton className="h-5 w-24 rounded-md" />
        </div>
      </div>
    </div>
  );
}

export default function ProvidersPage() {
  const { data, isLoading, error, refetch, lastRefreshed } = useProvidersStatus(60_000);

  const providers = data?.providers ?? [];
  const healthyCnt = providers.filter((p) => p.status === "healthy").length;

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Provider Status</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Real-time health monitoring for all connected AI providers.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {!isLoading && providers.length > 0 && (
            <span className="text-xs text-muted-foreground">
              <span className="font-semibold text-emerald-400">{healthyCnt}/{providers.length}</span> healthy
            </span>
          )}
          {lastRefreshed && (
            <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
              <Clock className="h-3 w-3" />
              {timeAgo(lastRefreshed.toISOString())}
            </span>
          )}
          <button
            onClick={refetch}
            disabled={isLoading}
            className="flex items-center gap-1.5 rounded-lg border border-border/60 px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", isLoading && "animate-spin")} />
            Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Provider cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {isLoading
          ? [1, 2, 3].map((i) => <ProviderCardSkeleton key={i} />)
          : providers.map((p) => <ProviderCard key={p.provider} p={p} />)}
      </div>

      {/* Comparison table */}
      {!isLoading && providers.length > 0 && (
        <div className="rounded-xl border border-border/60 bg-card/60 overflow-hidden">
          <div className="border-b border-border/50 px-5 py-3.5">
            <h2 className="text-sm font-semibold">Side-by-side Comparison</h2>
            <p className="text-xs text-muted-foreground mt-0.5">Health and performance metrics</p>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-[1.5fr_auto_auto_auto_auto_auto] gap-x-6 pb-2.5 border-b border-border/40 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60">
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
                const meta = PROVIDER_META[p.provider] ?? { label: p.provider, textColor: "text-foreground", dotColor: "" };
                return (
                  <div
                    key={p.provider}
                    className="grid grid-cols-[1.5fr_auto_auto_auto_auto_auto] gap-x-6 py-3 text-xs items-center"
                  >
                    <div className="flex items-center gap-2">
                      <span className={cn("h-1.5 w-1.5 rounded-full", meta.dotColor)} />
                      <span className="font-medium">{meta.label}</span>
                    </div>
                    <div className={cn("flex items-center gap-1 text-[11px] font-medium", cfg.textColor)}>
                      <span className={cn("h-1.5 w-1.5 rounded-full", cfg.dotColor)} />
                      {cfg.label}
                    </div>
                    <span className="font-mono text-muted-foreground tabular-nums">{fmtMs(p.latency_ms)}</span>
                    <span className="font-mono text-muted-foreground tabular-nums">{fmtMs(p.avg_latency_ms)}</span>
                    <span className="text-muted-foreground tabular-nums">{fmtUptime(p.uptime_percentage)}</span>
                    <span className="text-emerald-400 font-medium">Yes</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Footer note */}
      <p className="text-center text-[11px] text-muted-foreground/50">
        Health checks auto-refresh every 60 seconds. Results are persisted to the database.
      </p>
    </div>
  );
}
