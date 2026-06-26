"use client";

import { Zap, DollarSign, Timer, Star, Settings2 } from "lucide-react";
import { cn } from "@/lib/utils";

export type Strategy = "auto" | "cheapest" | "fastest" | "quality" | "manual";

const STRATEGIES: {
  id: Strategy;
  label: string;
  icon: React.ElementType;
  description: string;
}[] = [
  { id: "auto", label: "Auto", icon: Zap, description: "Best composite score" },
  { id: "cheapest", label: "Cheapest", icon: DollarSign, description: "Lowest token cost" },
  { id: "fastest", label: "Fastest", icon: Timer, description: "Lowest latency" },
  { id: "quality", label: "Quality", icon: Star, description: "Highest benchmark score" },
  { id: "manual", label: "Manual", icon: Settings2, description: "Pick provider yourself" },
];

const PROVIDERS = [
  { id: "openai", label: "OpenAI" },
  { id: "anthropic", label: "Anthropic" },
  { id: "gemini", label: "Gemini" },
];

interface Props {
  strategy: Strategy;
  manualProvider: string;
  onStrategyChange: (s: Strategy) => void;
  onManualProviderChange: (p: string) => void;
  disabled?: boolean;
}

export function StrategySelector({
  strategy,
  manualProvider,
  onStrategyChange,
  onManualProviderChange,
  disabled,
}: Props) {
  return (
    <div className="flex items-center gap-2">
      {/* Strategy tabs */}
      <div className="flex rounded-lg border border-border/50 bg-muted/30 p-0.5">
        {STRATEGIES.map((s) => {
          const Icon = s.icon;
          const isActive = strategy === s.id;
          return (
            <button
              key={s.id}
              onClick={() => onStrategyChange(s.id)}
              disabled={disabled}
              title={s.description}
              className={cn(
                "flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-all",
                isActive
                  ? "bg-velora-500 text-white shadow-sm"
                  : "text-muted-foreground hover:text-foreground disabled:opacity-40"
              )}
            >
              <Icon className="h-3 w-3" />
              {s.label}
            </button>
          );
        })}
      </div>

      {/* Manual provider dropdown */}
      {strategy === "manual" && (
        <select
          value={manualProvider}
          onChange={(e) => onManualProviderChange(e.target.value)}
          disabled={disabled}
          className="rounded-md border border-border/50 bg-card px-2.5 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-velora-500/50 disabled:opacity-40"
        >
          {PROVIDERS.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
