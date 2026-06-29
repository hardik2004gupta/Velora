"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import {
  Search,
  Download,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  AlertCircle,
  SlidersHorizontal,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useRequests } from "@/hooks/useRequests";
import { cn } from "@/lib/utils";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const SORT_OPTIONS = [
  { value: "created_at", label: "Date" },
  { value: "latency_ms", label: "Latency" },
  { value: "cost_usd", label: "Cost" },
  { value: "provider", label: "Provider" },
] as const;

const PROVIDER_DOT: Record<string, string> = {
  openai: "bg-green-400",
  anthropic: "bg-orange-400",
  gemini: "bg-blue-400",
};

const PROVIDER_TEXT: Record<string, string> = {
  openai: "text-green-400",
  anthropic: "text-orange-400",
  gemini: "text-blue-400",
};

function StatusBadge({ status }: { status: string }) {
  if (status === "success")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
        <span className="h-1 w-1 rounded-full bg-emerald-400" />
        ok
      </span>
    );
  return (
    <Badge variant="destructive" className="text-[10px] px-1.5 py-0 h-4">
      {status}
    </Badge>
  );
}

function formatCost(usd: number): string {
  if (usd === 0) return "$0.00";
  if (usd < 0.0001) return `$${usd.toExponential(2)}`;
  return `$${usd.toFixed(6)}`;
}

function formatLatency(ms: number | null): string {
  if (ms === null) return "—";
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${ms}ms`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function downloadExport(format: "csv" | "json") {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("velora_access_token") : null;
  const url = `${BASE_URL}/api/v1/requests/export?format=${format}`;
  fetch(url, { headers: { Authorization: `Bearer ${token}` } })
    .then((r) => r.blob())
    .then((blob) => {
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objectUrl;
      a.download = `velora_requests.${format}`;
      a.click();
      URL.revokeObjectURL(objectUrl);
    })
    .catch(() => {});
}

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const [provider, setProvider] = useState("");
  const [status, setStatus] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const { data, isLoading, error, refetch } = useRequests({
    page,
    provider: provider || undefined,
    status: status || undefined,
    search: search || undefined,
    sortBy,
    sortDir,
  });

  const applySearch = useCallback(() => {
    setSearch(searchInput);
    setPage(1);
  }, [searchInput]);

  const clearFilters = useCallback(() => {
    setProvider("");
    setStatus("");
    setSortBy("created_at");
    setSortDir("desc");
    setSearch("");
    setSearchInput("");
    setPage(1);
  }, []);

  const total = data?.total ?? 0;
  const items = data?.items ?? [];
  const hasNext = data?.has_next ?? false;
  const limit = 20;
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const hasActiveFilters = !!(provider || status || search);

  return (
    <div className="p-6 space-y-5 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Request History</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Browse, search, and inspect your inference log.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => downloadExport("csv")}
            className="flex items-center gap-1.5 rounded-lg border border-border/60 px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <Download className="h-3 w-3" />
            CSV
          </button>
          <button
            onClick={() => downloadExport("json")}
            className="flex items-center gap-1.5 rounded-lg border border-border/60 px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <Download className="h-3 w-3" />
            JSON
          </button>
        </div>
      </div>

      {/* Filters bar */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Search */}
        <div className="flex items-center gap-1.5 rounded-lg border border-border/60 bg-card/60 px-3 py-1.5 text-sm focus-within:border-velora-500/40 focus-within:bg-card transition-colors">
          <Search className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && applySearch()}
            placeholder="Search prompt or request ID…"
            className="w-56 bg-transparent text-xs text-foreground placeholder:text-muted-foreground/50 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-1.5 rounded-lg border border-border/60 bg-card/60 px-2 py-1 text-xs">
          <SlidersHorizontal className="h-3 w-3 text-muted-foreground" />

          {/* Provider */}
          <select
            value={provider}
            onChange={(e) => { setProvider(e.target.value); setPage(1); }}
            className="bg-transparent text-xs text-foreground focus:outline-none cursor-pointer"
          >
            <option value="">All providers</option>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="gemini">Gemini</option>
          </select>

          <span className="text-border">|</span>

          {/* Status */}
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="bg-transparent text-xs text-foreground focus:outline-none cursor-pointer"
          >
            <option value="">All statuses</option>
            <option value="success">Success</option>
            <option value="error">Error</option>
          </select>

          <span className="text-border">|</span>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
            className="bg-transparent text-xs text-foreground focus:outline-none cursor-pointer"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>Sort: {o.label}</option>
            ))}
          </select>

          <span className="text-border">|</span>

          <button
            onClick={() => setSortDir((d) => (d === "desc" ? "asc" : "desc"))}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {sortDir === "desc" ? "↓ Newest" : "↑ Oldest"}
          </button>
        </div>

        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 rounded-lg border border-border/60 px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <RotateCcw className="h-3 w-3" /> Clear
          </button>
        )}
      </div>

      {/* Table */}
      <div className="rounded-xl border border-border/60 bg-card/60 overflow-hidden">
        {/* Table header */}
        <div className="flex items-center justify-between border-b border-border/50 px-4 py-3">
          <span className="text-xs font-medium text-muted-foreground">
            {isLoading ? "Loading…" : `${total.toLocaleString()} request${total !== 1 ? "s" : ""}`}
          </span>
          <button
            onClick={refetch}
            className="text-muted-foreground hover:text-foreground transition-colors"
            title="Refresh"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        </div>

        {error ? (
          <div className="flex items-center gap-2 m-4 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-xs text-destructive">
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            {error}
          </div>
        ) : (
          <>
            {/* Column headers */}
            <div className="grid grid-cols-[1.8fr_2.5fr_auto_auto_auto_auto_auto] gap-x-4 border-b border-border/40 px-4 py-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60">
              <span>Request</span>
              <span>Prompt</span>
              <span>Strategy</span>
              <span>Tokens</span>
              <span>Latency</span>
              <span>Cost</span>
              <span>Status</span>
            </div>

            <div className="divide-y divide-border/30">
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <div
                    key={i}
                    className="grid grid-cols-[1.8fr_2.5fr_auto_auto_auto_auto_auto] gap-x-4 px-4 py-3 items-center"
                  >
                    <Skeleton className="h-3.5 w-28" />
                    <Skeleton className="h-3.5 w-40" />
                    <Skeleton className="h-4 w-14 rounded-full" />
                    <Skeleton className="h-3.5 w-10" />
                    <Skeleton className="h-3.5 w-12" />
                    <Skeleton className="h-3.5 w-14" />
                    <Skeleton className="h-4 w-12 rounded-full" />
                  </div>
                ))
              ) : items.length === 0 ? (
                <div className="py-16 text-center">
                  <p className="text-sm font-medium text-muted-foreground">No requests found</p>
                  {hasActiveFilters && (
                    <button
                      onClick={clearFilters}
                      className="mt-2 text-xs text-velora-400 hover:underline"
                    >
                      Clear filters
                    </button>
                  )}
                </div>
              ) : (
                items.map((req) => (
                  <Link
                    key={req.id}
                    href={`/history/${req.request_id ?? req.id}`}
                    className="grid grid-cols-[1.8fr_2.5fr_auto_auto_auto_auto_auto] gap-x-4 px-4 py-3 items-center hover:bg-muted/30 transition-colors group"
                  >
                    {/* ID + provider/model */}
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span className={cn("h-1.5 w-1.5 rounded-full shrink-0", PROVIDER_DOT[req.provider] ?? "bg-muted-foreground")} />
                        <span className={cn("text-xs font-medium truncate", PROVIDER_TEXT[req.provider] ?? "text-foreground")}>
                          {req.model}
                        </span>
                      </div>
                      <div className="text-[10px] font-mono text-muted-foreground/50 truncate">
                        {formatDate(req.created_at)}
                      </div>
                    </div>

                    {/* Prompt preview */}
                    <div className="min-w-0 truncate text-xs text-muted-foreground">
                      {req.prompt ?? <span className="italic opacity-40">no preview</span>}
                    </div>

                    {/* Strategy */}
                    <Badge variant="outline" className="text-[10px] whitespace-nowrap font-normal">
                      {req.routing_strategy}
                    </Badge>

                    {/* Tokens */}
                    <span className="text-xs text-muted-foreground tabular-nums whitespace-nowrap">
                      {req.total_tokens.toLocaleString()}
                    </span>

                    {/* Latency */}
                    <span className="text-xs text-muted-foreground tabular-nums whitespace-nowrap">
                      {formatLatency(req.latency_ms)}
                    </span>

                    {/* Cost */}
                    <span className="text-xs font-mono text-muted-foreground tabular-nums whitespace-nowrap">
                      {formatCost(req.cost_usd)}
                    </span>

                    {/* Status */}
                    <StatusBadge status={req.status} />
                  </Link>
                ))
              )}
            </div>

            {/* Pagination */}
            {!isLoading && total > limit && (
              <div className="flex items-center justify-between border-t border-border/40 px-4 py-3">
                <span className="text-[11px] text-muted-foreground">
                  Page {page} of {totalPages} &middot; {total.toLocaleString()} total
                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="flex h-7 w-7 items-center justify-center rounded-md border border-border/50 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-30 transition-colors"
                  >
                    <ChevronLeft className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={!hasNext}
                    className="flex h-7 w-7 items-center justify-center rounded-md border border-border/50 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-30 transition-colors"
                  >
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
