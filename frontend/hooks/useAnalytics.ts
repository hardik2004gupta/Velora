"use client";

import { useEffect, useState } from "react";
import { api, APIError } from "@/lib/api";
import type { DashboardOverview } from "@/types";

interface UseOverviewResult {
  data: DashboardOverview | null;
  isLoading: boolean;
  error: string | null;
}

export function useDashboardOverview(periodDays = 30): UseOverviewResult {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    api
      .get<DashboardOverview>(`/api/v1/analytics/overview?period_days=${periodDays}`)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof APIError ? err.message : "Failed to load overview");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [periodDays]);

  return { data, isLoading, error };
}
