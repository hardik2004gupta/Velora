"use client";

import Link from "next/link";
import { Trophy, DollarSign, Clock, Activity, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import type { RoutingDecision } from "@/types";

interface Props {
  decision: RoutingDecision;
}

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

export function RoutingDecisionCard({ decision }: Props) {
  const [expanded, setExpanded] = useState(false);

  const winner = decision.candidates.find(
    (c) => `${c.provider}/${c.model}` === decision.selected
  ) ?? decision.candidates[0];

  const topThree = decision.candidates.slice(0, expanded ? undefined : 3);

  return (
    <div className="mt-2 rounded-lg border border-velora-500/20 bg-velora-500/5 text-xs">
      {/* Header row */}
      <div className="flex items-center justify-between px-3 py-2">
        <div className="flex items-center gap-2">
          <Trophy className="h-3 w-3 text-amber-400" />
          <span className="font-medium text-foreground">
            Routed to{" "}
            <span className={cn("capitalize", PROVIDER_COLORS[winner?.provider ?? ""] ?? "text-velora-400")}>
              {winner?.provider}
            </span>
            {" / "}
            <span className="text-muted-foreground">{winner?.model}</span>
          </span>
          <span className="rounded-full bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
            {STRATEGY_LABELS[decision.strategy] ?? decision.strategy}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/inspector"
            className="text-velora-400 hover:underline"
          >
            Inspector →
          </Link>
          <button
            onClick={() => setExpanded((v) => !v)}
            className="text-muted-foreground hover:text-foreground"
          >
            {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* Reason */}
      <div className="border-t border-velora-500/10 px-3 py-1.5 text-muted-foreground">
        {decision.reason}
      </div>

      {/* Candidate list */}
      {expanded && (
        <div className="border-t border-velora-500/10 px-3 py-2 space-y-1.5">
          {topThree.map((c, i) => (
            <div
              key={`${c.provider}/${c.model}`}
              className={cn(
                "flex items-center gap-3 rounded-md px-2 py-1.5",
                i === 0 && decision.candidates[0].provider === c.provider
                  ? "bg-velora-500/10"
                  : "bg-muted/30"
              )}
            >
              <span className={cn("capitalize font-medium w-16", PROVIDER_COLORS[c.provider] ?? "text-foreground")}>
                {c.provider}
              </span>
              <span className="flex-1 text-muted-foreground truncate">{c.model}</span>
              <div className="flex items-center gap-2 text-muted-foreground">
                <span className="flex items-center gap-0.5">
                  <DollarSign className="h-3 w-3" />
                  {c.cost_per_1k.toFixed(5)}
                </span>
                <span className="flex items-center gap-0.5">
                  <Clock className="h-3 w-3" />
                  {c.avg_latency_ms}ms
                </span>
                <span className="flex items-center gap-0.5">
                  <Activity className="h-3 w-3" />
                  {(c.quality_score * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex items-center gap-1.5 w-20">
                <div className="flex-1 h-1 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full rounded-full bg-velora-500"
                    style={{ width: `${c.score * 100}%` }}
                  />
                </div>
                <span className="text-velora-400 font-medium">{c.score.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
