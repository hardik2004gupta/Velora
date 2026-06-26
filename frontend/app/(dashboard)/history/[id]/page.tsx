"use client";

import { use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  Clock,
  Coins,
  Zap,
  MessageSquare,
  Route,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useRequestDetail } from "@/hooks/useRequests";
import { cn } from "@/lib/utils";

const PROVIDER_COLORS: Record<string, string> = {
  openai: "text-green-400",
  anthropic: "text-orange-400",
  gemini: "text-blue-400",
};

function formatCost(usd: number): string {
  if (usd === 0) return "$0.00";
  if (usd < 0.0001) return `$${usd.toExponential(2)}`;
  return `$${usd.toFixed(6)}`;
}

function formatLatency(ms: number | null): string {
  if (ms === null) return "—";
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`;
  return `${ms}ms`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  className,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  sub?: string;
  className?: string;
}) {
  return (
    <div className="rounded-lg border border-border/50 bg-card p-4 space-y-1">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Icon className={cn("h-3.5 w-3.5", className)} />
        {label}
      </div>
      <div className="text-xl font-semibold tracking-tight">{value}</div>
      {sub && <div className="text-[11px] text-muted-foreground">{sub}</div>}
    </div>
  );
}

function PreBlock({ content, label }: { content: string; label: string }) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</p>
      <pre className="whitespace-pre-wrap break-words rounded-lg border border-border/50 bg-muted/30 p-4 text-sm leading-relaxed text-foreground font-mono">
        {content}
      </pre>
    </div>
  );
}

export default function RequestDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: req, isLoading, error } = useRequestDetail(id);

  if (isLoading) {
    return (
      <div className="p-6 space-y-6 max-w-4xl mx-auto">
        <Skeleton className="h-5 w-24" />
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
        <Skeleton className="h-48 rounded-lg" />
        <Skeleton className="h-48 rounded-lg" />
      </div>
    );
  }

  if (error || !req) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-4">
        <Link
          href="/history"
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to history
        </Link>
        <div className="flex items-center gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          {error ?? "Request not found."}
        </div>
      </div>
    );
  }

  const isError = req.status === "error";

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Back nav */}
      <Link
        href="/history"
        className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to history
      </Link>

      {/* Title row */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-0.5">
          <h1 className="text-xl font-bold tracking-tight font-mono">
            {req.request_id ?? req.id}
          </h1>
          <p className="text-xs text-muted-foreground">{formatDate(req.created_at)}</p>
        </div>
        <div className="flex items-center gap-2">
          {isError ? (
            <Badge variant="destructive" className="gap-1">
              <AlertCircle className="h-3 w-3" /> error
            </Badge>
          ) : (
            <Badge variant="success" className="gap-1">
              <CheckCircle2 className="h-3 w-3" /> success
            </Badge>
          )}
        </div>
      </div>

      {/* Error banner */}
      {isError && req.error_message && (
        <div className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium mb-0.5">Error</p>
            <p className="text-destructive/80 font-mono text-xs">{req.error_message}</p>
          </div>
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          icon={Zap}
          label="Latency"
          value={formatLatency(req.latency_ms)}
          className="text-yellow-400"
        />
        <StatCard
          icon={MessageSquare}
          label="Tokens"
          value={req.total_tokens.toLocaleString()}
          sub={`${req.prompt_tokens} prompt · ${req.completion_tokens} completion`}
          className="text-blue-400"
        />
        <StatCard
          icon={Coins}
          label="Cost"
          value={formatCost(req.cost_usd)}
          className="text-green-400"
        />
        <StatCard
          icon={Clock}
          label="Provider"
          value={req.provider}
          sub={req.model}
          className={PROVIDER_COLORS[req.provider] ?? "text-muted-foreground"}
        />
      </div>

      {/* Routing */}
      <Card className="border-border/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Route className="h-4 w-4 text-velora-400" />
            Routing Decision
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-3 text-xs">
            <div>
              <span className="text-muted-foreground">Strategy </span>
              <Badge variant="outline">{req.routing_strategy}</Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Selected </span>
              <span className={cn("font-medium capitalize", PROVIDER_COLORS[req.provider] ?? "text-foreground")}>
                {req.provider}/{req.model}
              </span>
            </div>
          </div>

          {req.routing_reason && (
            <p className="text-xs text-muted-foreground border-l-2 border-velora-500/40 pl-3 italic">
              {req.routing_reason}
            </p>
          )}

          {req.routing_decision?.candidates && req.routing_decision.candidates.length > 0 && (
            <div className="mt-3 space-y-1.5">
              <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Candidates
              </p>
              <div className="divide-y divide-border/30 rounded-lg border border-border/50 overflow-hidden">
                {req.routing_decision.candidates.map((c) => (
                  <div
                    key={`${c.provider}-${c.model}`}
                    className={cn(
                      "grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-4 px-3 py-2 text-xs items-center",
                      c.provider === req.provider && c.model === req.model
                        ? "bg-velora-500/5"
                        : ""
                    )}
                  >
                    <span className={cn("font-medium capitalize", PROVIDER_COLORS[c.provider] ?? "text-foreground")}>
                      {c.provider}/{c.model}
                      {c.provider === req.provider && c.model === req.model && (
                        <Badge variant="outline" className="ml-2 text-[9px]">selected</Badge>
                      )}
                    </span>
                    <span className="text-muted-foreground whitespace-nowrap">
                      ${c.cost_per_1k}/1k
                    </span>
                    <span className="text-muted-foreground whitespace-nowrap">
                      {c.avg_latency_ms}ms
                    </span>
                    <span className="text-muted-foreground whitespace-nowrap">
                      Q {c.quality_score.toFixed(2)}
                    </span>
                    <Badge
                      variant={
                        c.health === "healthy"
                          ? "success"
                          : c.health === "degraded"
                          ? "secondary"
                          : "destructive"
                      }
                      className="text-[9px]"
                    >
                      {c.health}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Prompt */}
      {req.prompt && <PreBlock content={req.prompt} label="Prompt" />}

      {/* Response */}
      {req.response && <PreBlock content={req.response} label="Response" />}
    </div>
  );
}
