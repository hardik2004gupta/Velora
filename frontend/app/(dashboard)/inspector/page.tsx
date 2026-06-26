"use client";

import Link from "next/link";
import {
  Search,
  Trophy,
  DollarSign,
  Clock,
  Activity,
  Zap,
  ChevronRight,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { usePlaygroundStore } from "@/store/playground";
import type { RoutingDecision, RoutingCandidate } from "@/types";
import { cn } from "@/lib/utils";

const STRATEGY_LABELS: Record<string, string> = {
  auto: "Auto",
  cheapest: "Cheapest",
  fastest: "Fastest",
  quality: "Quality",
  manual: "Manual",
};

const PROVIDER_COLORS: Record<string, string> = {
  openai: "text-green-400",
  anthropic: "text-orange-400",
  gemini: "text-blue-400",
};

const BREAKDOWN_LABELS: Record<string, string> = {
  quality: "Quality",
  cost: "Cost rank",
  latency: "Speed rank",
  health: "Health",
};

function ScoreBar({ value, className }: { value: number; className?: string }) {
  return (
    <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
      <div
        className={cn("h-full rounded-full transition-all", className ?? "bg-velora-500")}
        style={{ width: `${Math.min(value * 100, 100)}%` }}
      />
    </div>
  );
}

function CandidateRow({
  candidate,
  rank,
  isWinner,
}: {
  candidate: RoutingCandidate;
  rank: number;
  isWinner: boolean;
}) {
  const providerColor = PROVIDER_COLORS[candidate.provider] ?? "text-foreground";
  return (
    <div
      className={cn(
        "rounded-lg border p-4 transition-colors",
        isWinner
          ? "border-velora-500/40 bg-velora-500/5"
          : "border-border/50 bg-card"
      )}
    >
      {/* Row header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {isWinner && <Trophy className="h-4 w-4 text-amber-400 flex-shrink-0" />}
          {!isWinner && (
            <span className="flex h-4 w-4 items-center justify-center rounded-full bg-muted text-[10px] font-medium text-muted-foreground">
              {rank}
            </span>
          )}
          <span className={cn("text-sm font-semibold capitalize", providerColor)}>
            {candidate.provider}
          </span>
          <ChevronRight className="h-3 w-3 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">{candidate.model}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-lg font-bold text-velora-400">
            {candidate.score.toFixed(3)}
          </span>
          <span className="text-xs text-muted-foreground">score</span>
        </div>
      </div>

      {/* Overall score bar */}
      <ScoreBar value={candidate.score} />

      {/* Stats row */}
      <div className="mt-3 grid grid-cols-3 gap-3 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <DollarSign className="h-3 w-3 flex-shrink-0" />
          <span>${candidate.cost_per_1k.toFixed(5)}/1K</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="h-3 w-3 flex-shrink-0" />
          <span>{candidate.avg_latency_ms}ms</span>
        </div>
        <div className="flex items-center gap-1">
          <Activity className="h-3 w-3 flex-shrink-0" />
          <span>{(candidate.quality_score * 100).toFixed(0)}% quality</span>
        </div>
      </div>

      {/* Score breakdown */}
      {candidate.score_breakdown && Object.keys(candidate.score_breakdown).length > 0 && (
        <div className="mt-3 space-y-1.5">
          {Object.entries(candidate.score_breakdown).map(([key, val]) => (
            <div key={key} className="flex items-center gap-2">
              <span className="w-20 flex-shrink-0 text-[11px] text-muted-foreground">
                {BREAKDOWN_LABELS[key] ?? key}
              </span>
              <div className="flex-1">
                <ScoreBar
                  value={val}
                  className={
                    key === "quality"
                      ? "bg-purple-500"
                      : key === "cost"
                      ? "bg-green-500"
                      : key === "latency"
                      ? "bg-blue-500"
                      : "bg-amber-500"
                  }
                />
              </div>
              <span className="w-10 text-right text-[11px] text-muted-foreground">
                {(val * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function DecisionView({ decision }: { decision: RoutingDecision }) {
  return (
    <div className="space-y-4">
      {/* Decision header */}
      <Card className="border-border/50">
        <CardHeader className="pb-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="info">
              Strategy: {STRATEGY_LABELS[decision.strategy] ?? decision.strategy}
            </Badge>
            <Badge variant="success">
              Selected: {decision.selected}
            </Badge>
          </div>
          <CardDescription className="text-sm">{decision.reason}</CardDescription>
        </CardHeader>
      </Card>

      {/* Candidates */}
      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          All Candidates — sorted by score
        </h2>
        <div className="space-y-2">
          {decision.candidates.map((c, i) => (
            <CandidateRow
              key={`${c.provider}/${c.model}`}
              candidate={c}
              rank={i + 1}
              isWinner={`${c.provider}/${c.model}` === decision.selected}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-dashed border-border/50 p-10 text-center">
        <Zap className="mx-auto mb-3 h-8 w-8 text-muted-foreground/40" />
        <p className="text-sm font-medium text-muted-foreground">No routing decision yet</p>
        <p className="mt-1 text-xs text-muted-foreground/60">
          Send a message in the{" "}
          <Link href="/playground" className="text-velora-400 hover:underline">
            Playground
          </Link>{" "}
          to generate a real routing decision.
        </p>
      </div>

      {/* Static explainer */}
      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          Example Decision (demo)
        </h2>
        <DecisionView
          decision={{
            strategy: "auto",
            selected: "openai/gpt-4o-mini",
            reason:
              "Selected openai/gpt-4o-mini with the highest composite score (0.85) — quality 78%, cost rank 91%, latency rank 79%.",
            candidates: [
              {
                provider: "openai",
                model: "gpt-4o-mini",
                cost_per_1k: 0.000375,
                avg_latency_ms: 820,
                health: "healthy",
                quality_score: 0.78,
                score: 0.85,
                score_breakdown: { quality: 0.78, cost: 0.91, latency: 0.79, health: 1.0 },
              },
              {
                provider: "gemini",
                model: "gemini-2.0-flash",
                cost_per_1k: 0.00025,
                avg_latency_ms: 650,
                health: "healthy",
                quality_score: 0.75,
                score: 0.83,
                score_breakdown: { quality: 0.75, cost: 1.0, latency: 1.0, health: 1.0 },
              },
              {
                provider: "anthropic",
                model: "claude-haiku-4-5-20251001",
                cost_per_1k: 0.0024,
                avg_latency_ms: 950,
                health: "healthy",
                quality_score: 0.80,
                score: 0.73,
                score_breakdown: { quality: 0.80, cost: 0.58, latency: 0.67, health: 1.0 },
              },
            ],
          }}
        />
      </div>
    </div>
  );
}

export default function InspectorPage() {
  const lastRoutingDecision = usePlaygroundStore((s) => s.lastRoutingDecision);

  return (
    <div className="p-6 space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Routing Inspector</h1>
        <p className="text-muted-foreground">
          Understand exactly why Velora chose each provider — full decision transparency.
        </p>
      </div>

      {/* How it works */}
      <Card className="border-velora-500/20 bg-velora-500/5">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-velora-400" />
            <CardTitle className="text-sm text-velora-400">How the Inspector Works</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Every request through Velora generates a{" "}
            <code className="text-velora-400 text-xs">RoutingDecision</code> object with all
            candidate providers, per-dimension scores, and a plain-English explanation.
            Routing is deterministic and rule-based — no black-box decisions.
          </p>
        </CardContent>
      </Card>

      {/* Decision or empty state */}
      {lastRoutingDecision ? (
        <DecisionView decision={lastRoutingDecision} />
      ) : (
        <EmptyState />
      )}
    </div>
  );
}
