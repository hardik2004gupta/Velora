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
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useRequests } from "@/hooks/useRequests";
import { cn } from "@/lib/utils";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const SORT_OPTIONS = [
  { value: "created_at", label: "Date" },
  { value: "latency_ms", label: "Latency" },
  { value: "cost_usd", label: "Cost" },
  { value: "provider", label: "Provider" },
] as const;

const PROVIDER_COLORS: Record<string, string> = {
  openai: "text-green-400",
  anthropic: "text-orange-400",
  gemini: "text-blue-400",
};

function StatusBadge({ status }: { status: string }) {
  if (status === "success") return <Badge variant="success">success</Badge>;
  if (status === "error") return <Badge variant="destructive">error</Badge>;
  return <Badge variant="secondary">{status}</Badge>;
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

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Request History</h1>
          <p className="text-muted-foreground text-sm">
            Browse, search, and inspect your inference request log.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => downloadExport("csv")}
            className="flex items-center gap-1.5 rounded-md border border-border/50 px-3 py-2 text-xs text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <Download className="h-3.5 w-3.5" />
            CSV
          </button>
          <button
            onClick={() => downloadExport("json")}
            className="flex items-center gap-1.5 rounded-md border border-border/50 px-3 py-2 text-xs text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <Download className="h-3.5 w-3.5" />
            JSON
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Search */}
        <div className="flex items-center gap-1 rounded-md border border-border/50 bg-card px-3 py-2 text-sm focus-within:border-velora-500/50">
          <Search className="h-3.5 w-3.5 text-muted-foreground" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && applySearch()}
            placeholder="Search prompt, request ID…"
            className="w-52 bg-transparent text-sm text-foreground placeholder-muted-foreground/60 focus:outline-none"
          />
          <button onClick={applySearch} className="text-xs text-velora-400 hover:underline">
            Go
          </button>
        </div>

        {/* Provider */}
        <select
          value={provider}
          onChange={(e) => { setProvider(e.target.value); setPage(1); }}
          className="rounded-md border border-border/50 bg-card px-2.5 py-2 text-xs text-foreground focus:outline-none"
        >
          <option value="">All providers</option>
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
          <option value="gemini">Gemini</option>
        </select>

        {/* Status */}
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="rounded-md border border-border/50 bg-card px-2.5 py-2 text-xs text-foreground focus:outline-none"
        >
          <option value="">All statuses</option>
          <option value="success">success</option>
          <option value="error">error</option>
        </select>

        {/* Sort */}
        <select
          value={sortBy}
          onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
          className="rounded-md border border-border/50 bg-card px-2.5 py-2 text-xs text-foreground focus:outline-none"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              Sort: {o.label}
            </option>
          ))}
        </select>

        <button
          onClick={() => setSortDir((d) => (d === "desc" ? "asc" : "desc"))}
          className="rounded-md border border-border/50 bg-card px-2.5 py-2 text-xs text-muted-foreground hover:bg-muted"
        >
          {sortDir === "desc" ? "↓ Newest" : "↑ Oldest"}
        </button>

        {(provider || status || search) && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <RotateCcw className="h-3 w-3" /> Clear
          </button>
        )}
      </div>

      {/* Table */}
      <Card className="border-border/50">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              {isLoading ? "Loading…" : `${total.toLocaleString()} request${total !== 1 ? "s" : ""}`}
            </CardTitle>
            {!isLoading && (
              <button
                onClick={refetch}
                className="text-xs text-muted-foreground hover:text-foreground"
                title="Refresh"
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              {error}
            </div>
          ) : (
            <>
              {/* Column headers */}
              <div className="grid grid-cols-[1.5fr_2fr_auto_auto_auto_auto_auto] gap-x-4 border-b border-border/50 pb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                <span>Request</span>
                <span>Prompt</span>
                <span>Strategy</span>
                <span>Tokens</span>
                <span>Latency</span>
                <span>Cost</span>
                <span>Status</span>
              </div>

              <div className="mt-1 divide-y divide-border/30">
                {isLoading ? (
                  Array.from({ length: 8 }).map((_, i) => (
                    <div
                      key={i}
                      className="grid grid-cols-[1.5fr_2fr_auto_auto_auto_auto_auto] gap-x-4 py-3 items-center"
                    >
                      <Skeleton className="h-3.5 w-28" />
                      <Skeleton className="h-3.5 w-40" />
                      <Skeleton className="h-5 w-16 rounded-full" />
                      <Skeleton className="h-3.5 w-10" />
                      <Skeleton className="h-3.5 w-14" />
                      <Skeleton className="h-3.5 w-16" />
                      <Skeleton className="h-5 w-16 rounded-full" />
                    </div>
                  ))
                ) : items.length === 0 ? (
                  <div className="py-16 text-center">
                    <p className="text-sm text-muted-foreground">No requests found.</p>
                    {(search || provider || status) && (
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
                      className="grid grid-cols-[1.5fr_2fr_auto_auto_auto_auto_auto] gap-x-4 py-3 items-center rounded-sm px-1 hover:bg-muted/30 transition-colors"
                    >
                      {/* ID + provider/model */}
                      <div className="min-w-0">
                        <div className="text-[11px] font-mono text-muted-foreground truncate">
                          {req.request_id ?? req.id.slice(0, 16)}
                        </div>
                        <div
                          className={cn(
                            "text-xs font-medium capitalize truncate",
                            PROVIDER_COLORS[req.provider] ?? "text-foreground"
                          )}
                        >
                          {req.provider}/{req.model}
                        </div>
                        <div className="text-[10px] text-muted-foreground/60">
                          {formatDate(req.created_at)}
                        </div>
                      </div>

                      {/* Prompt preview */}
                      <div className="min-w-0 truncate text-xs text-muted-foreground">
                        {req.prompt ?? <span className="italic opacity-50">—</span>}
                      </div>

                      {/* Strategy */}
                      <Badge variant="outline" className="text-[10px] whitespace-nowrap">
                        {req.routing_strategy}
                      </Badge>

                      {/* Tokens */}
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {req.total_tokens.toLocaleString()}
                      </span>

                      {/* Latency */}
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {formatLatency(req.latency_ms)}
                      </span>

                      {/* Cost */}
                      <span className="text-xs font-mono text-muted-foreground whitespace-nowrap">
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
                <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    Page {page} of {totalPages} — {total.toLocaleString()} total
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="rounded p-1 hover:bg-muted disabled:opacity-30"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setPage((p) => p + 1)}
                      disabled={!hasNext}
                      className="rounded p-1 hover:bg-muted disabled:opacity-30"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
