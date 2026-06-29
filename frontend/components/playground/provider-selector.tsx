"use client";

import { ChevronDown, Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { ProvidersResponse } from "@/types";

interface ProviderSelectorProps {
  selectedProvider: string;
  selectedModel: string;
  onProviderChange: (provider: string) => void;
  onModelChange: (model: string) => void;
  disabled?: boolean;
}

const PROVIDER_COLORS: Record<string, string> = {
  openai: "bg-emerald-500",
  anthropic: "bg-orange-500",
  gemini: "bg-blue-500",
};

function StatusDot({ status }: { status: "healthy" | "down" }) {
  return (
    <span
      className={cn(
        "inline-block h-1.5 w-1.5 rounded-full",
        status === "healthy" ? "bg-emerald-400" : "bg-red-400"
      )}
    />
  );
}

export function ProviderSelector({
  selectedProvider,
  selectedModel,
  onProviderChange,
  onModelChange,
  disabled,
}: ProviderSelectorProps) {
  const { data, isLoading } = useQuery<ProvidersResponse>({
    queryKey: ["providers"],
    queryFn: () => api.get<ProvidersResponse>("/api/v1/providers"),
    staleTime: 60_000,
    retry: false,
  });

  const providers = data?.providers ?? [];
  const current = providers.find((p) => p.id === selectedProvider);
  const models = current?.models ?? [];

  // Default to first model when provider changes and no model is selected
  const effectiveModel =
    selectedModel || (models[0]?.id ?? "");

  return (
    <div className="flex items-center gap-2">
      {/* Provider dropdown */}
      <div className="relative">
        <label className="sr-only">Provider</label>
        <div className="flex items-center gap-1.5 rounded-md border border-border/50 bg-card px-2.5 py-1.5">
          {isLoading ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
          ) : (
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                PROVIDER_COLORS[selectedProvider] ?? "bg-muted"
              )}
            />
          )}
          <select
            value={selectedProvider}
            onChange={(e) => onProviderChange(e.target.value)}
            disabled={disabled || isLoading}
            className="appearance-none bg-transparent pr-5 text-xs font-medium text-foreground focus:outline-none disabled:opacity-50"
          >
            {providers.length > 0
              ? providers.map((p) => (
                  <option key={p.id} value={p.id} disabled={p.status === "down"}>
                    {p.name}
                    {p.status === "down" ? " (down)" : ""}
                  </option>
                ))
              : (
                  <option value={selectedProvider}>{selectedProvider}</option>
                )}
          </select>
          <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3 w-3 -translate-y-1/2 text-muted-foreground" />
        </div>
      </div>

      {/* Model dropdown */}
      <div className="relative">
        <label className="sr-only">Model</label>
        <div className="flex items-center rounded-md border border-border/50 bg-card px-2.5 py-1.5">
          <select
            value={effectiveModel}
            onChange={(e) => onModelChange(e.target.value)}
            disabled={disabled || models.length === 0}
            className="appearance-none bg-transparent pr-5 text-xs font-medium text-foreground focus:outline-none disabled:opacity-50"
          >
            {models.length > 0 ? (
              models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.id}
                </option>
              ))
            ) : (
              <option value="">Default model</option>
            )}
          </select>
          <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3 w-3 -translate-y-1/2 text-muted-foreground" />
        </div>
      </div>

      {/* Status indicator */}
      {current && (
        <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
          <StatusDot status={current.status} />
          {current.status}
        </div>
      )}
    </div>
  );
}
