"use client";

import { useEffect, useState, useCallback } from "react";
import { api, APIError } from "@/lib/api";
import type {
  ConversationAnalytics,
  CostOverTime,
  DashboardOverview,
  LatencyAnalytics,
  ProviderDistribution,
  ProvidersStatusResponse,
  RoutingInsights,
  TokenAnalytics,
} from "@/types";

// ---------------------------------------------------------------------------
// Generic fetch hook factory
// ---------------------------------------------------------------------------

function useAnalyticsQuery<T>(path: string, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    api
      .get<T>(path)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof APIError ? err.message : "Failed to load data");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { data, isLoading, error, refetch };
}

// ---------------------------------------------------------------------------
// Dashboard overview
// ---------------------------------------------------------------------------

export function useDashboardOverview(periodDays = 30) {
  return useAnalyticsQuery<DashboardOverview>(
    `/api/v1/analytics/overview?period_days=${periodDays}`,
    [periodDays]
  );
}

// ---------------------------------------------------------------------------
// Cost over time
// ---------------------------------------------------------------------------

export function useCostOverTime(periodDays = 30) {
  return useAnalyticsQuery<CostOverTime>(
    `/api/v1/analytics/cost?period_days=${periodDays}`,
    [periodDays]
  );
}

// ---------------------------------------------------------------------------
// Latency analytics
// ---------------------------------------------------------------------------

export function useLatencyAnalytics(periodDays = 30) {
  return useAnalyticsQuery<LatencyAnalytics>(
    `/api/v1/analytics/latency?period_days=${periodDays}`,
    [periodDays]
  );
}

// ---------------------------------------------------------------------------
// Provider distribution
// ---------------------------------------------------------------------------

export function useProviderDistribution(periodDays = 30) {
  return useAnalyticsQuery<ProviderDistribution>(
    `/api/v1/analytics/providers?period_days=${periodDays}`,
    [periodDays]
  );
}

// ---------------------------------------------------------------------------
// Token analytics
// ---------------------------------------------------------------------------

export function useTokenAnalytics(periodDays = 30) {
  return useAnalyticsQuery<TokenAnalytics>(
    `/api/v1/analytics/tokens?period_days=${periodDays}`,
    [periodDays]
  );
}

// ---------------------------------------------------------------------------
// Conversation analytics
// ---------------------------------------------------------------------------

export function useConversationAnalytics(periodDays = 30) {
  return useAnalyticsQuery<ConversationAnalytics>(
    `/api/v1/analytics/conversations?period_days=${periodDays}`,
    [periodDays]
  );
}

// ---------------------------------------------------------------------------
// Routing insights
// ---------------------------------------------------------------------------

export function useRoutingInsights(periodDays = 30) {
  return useAnalyticsQuery<RoutingInsights>(
    `/api/v1/analytics/routing?period_days=${periodDays}`,
    [periodDays]
  );
}

// ---------------------------------------------------------------------------
// Provider health status (live checks)
// ---------------------------------------------------------------------------

export function useProvidersStatus(autoRefreshMs = 60_000) {
  const [data, setData] = useState<ProvidersStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);

  const fetch = useCallback(() => {
    setIsLoading(true);
    setError(null);
    api
      .get<ProvidersStatusResponse>("/api/v1/providers/status")
      .then((res) => {
        setData(res);
        setLastRefreshed(new Date());
      })
      .catch((err: unknown) => {
        setError(
          err instanceof APIError ? err.message : "Failed to fetch provider status"
        );
      })
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    fetch();
    if (autoRefreshMs > 0) {
      const id = setInterval(fetch, autoRefreshMs);
      return () => clearInterval(id);
    }
  }, [fetch, autoRefreshMs]);

  return { data, isLoading, error, refetch: fetch, lastRefreshed };
}
