"use client";

import Link from "next/link";
import {
  Trophy,
  DollarSign,
  Clock,
  Activity,
  Zap,
  ChevronRight,
  Database,
  GitBranch,
  Info,
  ArrowRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { usePlaygroundStore } from "@/store/playground";
import type { RoutingDecision, RoutingCandidate } from "@/types";
import { cn } from "@/lib/utils";

const STRATEGY_META: Record<string, { label: string; color: string; desc: string }> = {
  auto: { label: "Auto", color: "bg-velora-500/15 text-velora-400 border-velora-500/30", desc: "Weighted composite score (quality 35%, cost 30%, latency 25%, health 10%)" },
  cheapest: { label: "Cheapest", color: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30", desc: "Lowest cost per token among healthy providers" },
  fastest: { label: "Fastest", color: "bg-blue-500/15 text-blue-400 border-blue-500/30", desc: "Lowest average latency among healthy providers" },
  quality: { label: "Quality", color: "bg-purple-500/15 text-purple-400 border-purple-500/30", desc: "Highest quality score among healthy providers" },
  manual: { label: "Manual", color: "bg-amber-500/15 text-amber-400 border-amber-500/30", desc: "Provider explicitly selected by user" },
};

const PROVIDER_COLORS: Record<string, { text: string; dot: string; bg: string }> = {
  openai: { text: "text-green-400", dot: "bg-green-400", bg: "bg-green-500/10" },
  anthropic: { text: "text-orange-400", dot: "bg-orange-400", bg: "bg-orange-500/10" },
  gemini: { text: "text-blue-400", dot: "bg-blue-400", bg: "bg-blue-500/10" },
};

const BREAKDOWN_META: Record<string, { label: string; color: string; weight: string }> = {
  quality: { label: "Quality", color: "bg-purple-500", weight: "35%" },
  cost: { label: "Cost", color: "bg-emerald-500", weight: "30%" },
  latency: { label: "Latency", color: "bg-blue-500", weight: "25%" },
  health: { label: "Health", color: "bg-amber-500", weight: "10%" },
};

function ScoreBar({
  value,
  colorClass,
  animate = true,
}: {
  value: number;
  colorClass: string;
  animate?: boolean;
}) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted/50">
      <div
        className={cn("h-full rounded-full", colorClass, animate && "score-bar-animated")}
        style={{ width: `${Math.min(value * 100, 100)}%` }}
      />
    </div>
  );
}

function ProviderDot({ provider }: { provider: string }) {
  const cfg = PROVIDER_COLORS[provider];
  if (!cfg) return null;
  return <span className={cn("h-2 w-2 rounded-full shrink-0", cfg.dot)} />;
}

function CandidateCard({
  candidate,
  rank,
  isWinner,
  totalCandidates,
}: {
  candidate: RoutingCandidate;
  rank: number;
  isWinner: boolean;
  totalCandidates: number;
}) {
  const pCfg = PROVIDER_COLORS[candidate.provider] ?? { text: "text-foreground", dot: "bg-muted-foreground", bg: "bg-muted/10" };

  return (
    <div
      className={cn(
        "relative rounded-xl border p-4 transition-all duration-200 animate-fade-in-up",
        isWinner
          ? "border-velora-500/40 bg-velora-500/5 shadow-sm shadow-velora-500/10"
          : "border-border/60 bg-card/60"
      )}
      style={{ animationDelay: `${rank * 60}ms` }}
    >
      {/* Winner ribbon */}
      {isWinner && (
        <div className="absolute -top-px left-4 right-4 h-px bg-gradient-to-r from-transparent via-velora-500/60 to-transparent" />
      )}

      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2.5">
          {isWinner ? (
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-500/20">
              <Trophy className="h-3.5 w-3.5 text-amber-400" />
            </div>
          ) : (
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-muted/60">
              <span className="text-[11px] font-semibold text-muted-foreground">{rank}</span>
            </div>
          )}
          <div>
            <div className="flex items-center gap-1.5">
              <ProviderDot provider={candidate.provider} />
              <span className={cn("text-sm font-semibold capitalize", pCfg.text)}>
                {candidate.provider}
              </span>
              <ChevronRight className="h-3 w-3 text-muted-foreground/50" />
              <span className="text-xs text-muted-foreground font-mono">{candidate.model}</span>
            </div>
            <div className="mt-0.5 flex items-center gap-3 text-[11px] text-muted-foreground">
              <span className="flex items-center gap-1">
                <DollarSign className="h-2.5 w-2.5" />
                ${candidate.cost_per_1k.toFixed(5)}/1K
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-2.5 w-2.5" />
                {candidate.avg_latency_ms}ms
              </span>
              <span className="flex items-center gap-1">
                <Activity className="h-2.5 w-2.5" />
                {(candidate.quality_score * 100).toFixed(0)}% quality
              </span>
            </div>
          </div>
        </div>

        {/* Score badge */}
        <div className={cn(
          "flex flex-col items-end shrink-0",
        )}>
          <span className={cn(
            "text-2xl font-bold tabular-nums",
            isWinner ? "text-velora-400" : "text-muted-foreground"
          )}>
            {candidate.score.toFixed(3)}
          </span>
          <span className="text-[10px] text-muted-foreground">composite</span>
        </div>
      </div>

      {/* Overall score bar */}
      <ScoreBar
        value={candidate.score}
        colorClass={isWinner ? "bg-gradient-to-r from-velora-500 to-purple-500" : "bg-muted-foreground/40"}
      />

      {/* Score breakdown */}
      {candidate.score_breakdown && Object.keys(candidate.score_breakdown).length > 0 && (
        <div className="mt-3 space-y-2 pt-3 border-t border-border/40">
          {Object.entries(candidate.score_breakdown).map(([key, val]) => {
            const meta = BREAKDOWN_META[key];
            return (
              <div key={key} className="flex items-center gap-2.5">
                <div className="w-[72px] shrink-0">
                  <span className="text-[11px] text-muted-foreground">{meta?.label ?? key}</span>
                  {meta && (
                    <span className="ml-1 text-[9px] text-muted-foreground/50">×{meta.weight}</span>
                  )}
                </div>
                <div className="flex-1">
                  <ScoreBar
                    value={val}
                    colorClass={meta?.color ?? "bg-velora-500"}
                  />
                </div>
                <span className="w-9 text-right text-[11px] font-mono text-muted-foreground tabular-nums">
                  {(val * 100).toFixed(0)}%
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function RoutingFlowHeader({
  decision,
  cacheHit,
  fallbackProvider,
}: {
  decision: RoutingDecision;
  cacheHit?: boolean | null;
  fallbackProvider?: string | null;
}) {
  const stratMeta = STRATEGY_META[decision.strategy] ?? STRATEGY_META.auto;
  const [providerPart, modelPart] = decision.selected.split("/");
  const pCfg = PROVIDER_COLORS[providerPart] ?? { text: "text-foreground", dot: "bg-muted-foreground", bg: "bg-muted/10" };

  return (
    <div className="rounded-xl border border-border/60 bg-card/60 p-5">
      {/* Flow visualization */}
      <div className="flex items-center gap-2 flex-wrap mb-4">
        <div className="flex items-center gap-2 rounded-lg border border-border/60 bg-background/60 px-3 py-1.5">
          <Zap className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">Request</span>
        </div>
        <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/40 shrink-0" />
        <div className={cn("flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium", stratMeta.color)}>
          {stratMeta.label} strategy
        </div>
        <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/40 shrink-0" />
        <div className={cn("flex items-center gap-2 rounded-lg border border-border/60 px-3 py-1.5", pCfg.bg)}>
          <ProviderDot provider={providerPart} />
          <span className={cn("text-xs font-semibold capitalize", pCfg.text)}>{providerPart}</span>
          <span className="text-xs text-muted-foreground font-mono">/{modelPart}</span>
        </div>
        {cacheHit && (
          <>
            <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/40 shrink-0" />
            <div className="flex items-center gap-1.5 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-1.5">
              <Database className="h-3.5 w-3.5 text-cyan-400" />
              <span className="text-xs text-cyan-400 font-medium">Cache Hit</span>
            </div>
          </>
        )}
        {fallbackProvider && (
          <Badge variant="secondary" className="flex items-center gap-1 bg-amber-500/10 text-amber-400 border-amber-500/30 text-[11px]">
            <GitBranch className="h-3 w-3" />
            Fallback: {fallbackProvider}
          </Badge>
        )}
      </div>

      {/* Reason */}
      <div className="flex items-start gap-2.5 rounded-lg bg-muted/30 px-3.5 py-2.5">
        <Info className="h-3.5 w-3.5 text-velora-400 mt-0.5 shrink-0" />
        <p className="text-sm text-muted-foreground leading-relaxed">{decision.reason}</p>
      </div>

      {/* Strategy description */}
      <p className="mt-2 text-[11px] text-muted-foreground/60 pl-1">
        {stratMeta.desc}
      </p>
    </div>
  );
}

function DecisionView({
  decision,
  cacheHit,
  fallbackProvider,
}: {
  decision: RoutingDecision;
  cacheHit?: boolean | null;
  fallbackProvider?: string | null;
}) {
  return (
    <div className="space-y-5">
      <RoutingFlowHeader decision={decision} cacheHit={cacheHit} fallbackProvider={fallbackProvider} />

      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/70">
            All Candidates
          </h2>
          <span className="text-[11px] text-muted-foreground/50">sorted by composite score</span>
        </div>
        <div className="space-y-2.5">
          {decision.candidates.map((c, i) => (
            <CandidateCard
              key={`${c.provider}/${c.model}`}
              candidate={c}
              rank={i + 1}
              isWinner={`${c.provider}/${c.model}` === decision.selected}
              totalCandidates={decision.candidates.length}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

const DEMO_DECISION: RoutingDecision = {
  strategy: "auto",
  selected: "openai/gpt-4o-mini",
  reason:
    "openai/gpt-4o-mini achieved the highest composite score (0.851) — strong balance of quality, competitive cost, and below-average latency.",
  candidates: [
    {
      provider: "openai",
      model: "gpt-4o-mini",
      cost_per_1k: 0.000375,
      avg_latency_ms: 820,
      health: "healthy",
      quality_score: 0.78,
      score: 0.851,
      score_breakdown: { quality: 0.78, cost: 0.91, latency: 0.79, health: 1.0 },
    },
    {
      provider: "gemini",
      model: "gemini-2.0-flash",
      cost_per_1k: 0.00025,
      avg_latency_ms: 650,
      health: "healthy",
      quality_score: 0.75,
      score: 0.832,
      score_breakdown: { quality: 0.75, cost: 1.0, latency: 1.0, health: 1.0 },
    },
    {
      provider: "anthropic",
      model: "claude-haiku-4-5-20251001",
      cost_per_1k: 0.0024,
      avg_latency_ms: 950,
      health: "healthy",
      quality_score: 0.80,
      score: 0.727,
      score_breakdown: { quality: 0.80, cost: 0.58, latency: 0.67, health: 1.0 },
    },
  ],
};

export default function InspectorPage() {
  const lastRoutingDecision = usePlaygroundStore((s) => s.lastRoutingDecision);
  const lastCacheHit = usePlaygroundStore((s) => s.lastCacheHit);
  const lastFallbackProvider = usePlaygroundStore((s) => s.lastFallbackProvider);

  const hasLive = !!lastRoutingDecision;

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight">Routing Inspector</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Full decision transparency — every score, every candidate, every reason.
        </p>
      </div>

      {/* How it works explainer */}
      <div className="rounded-xl border border-velora-500/20 bg-velora-500/5 p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-velora-500/15">
            <Zap className="h-3.5 w-3.5 text-velora-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-velora-400">How the Inspector Works</h3>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Every request generates a <code className="text-velora-300 bg-velora-500/10 px-1 rounded text-[11px]">RoutingDecision</code> object
              containing all candidate providers, per-dimension scores (quality, cost, latency, health), and a plain-English explanation.
              Routing is <strong className="text-foreground/80">fully deterministic</strong> — no ML, no black boxes.
            </p>
          </div>
        </div>
      </div>

      {/* Live decision or demo */}
      {hasLive ? (
        <div className="space-y-1">
          <div className="flex items-center gap-2 mb-3">
            <span className="flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
            <span className="text-xs font-medium text-emerald-400">Live — from last Playground request</span>
            <Link href="/playground" className="ml-auto text-[11px] text-velora-400 hover:underline flex items-center gap-1">
              Back to Playground <ChevronRight className="h-3 w-3" />
            </Link>
          </div>
          <DecisionView decision={lastRoutingDecision} cacheHit={lastCacheHit} fallbackProvider={lastFallbackProvider} />
        </div>
      ) : (
        <div className="space-y-4">
          <div className="rounded-xl border border-dashed border-border/60 bg-card/30 p-6 text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-muted/50">
              <Zap className="h-5 w-5 text-muted-foreground/50" />
            </div>
            <p className="text-sm font-medium text-muted-foreground">No live decision yet</p>
            <p className="mt-1 text-xs text-muted-foreground/60">
              Send a message in the{" "}
              <Link href="/playground" className="text-velora-400 hover:underline">
                Playground
              </Link>{" "}
              to see a real routing decision here.
            </p>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="flex h-1.5 w-1.5 rounded-full bg-amber-400/60" />
              <span className="text-xs font-medium text-muted-foreground/70">Demo — example decision</span>
            </div>
            <DecisionView decision={DEMO_DECISION} />
          </div>
        </div>
      )}
    </div>
  );
}
