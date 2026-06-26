"use client";

import { useCallback, useEffect, useState } from "react";
import { api, APIError } from "@/lib/api";
import type { RequestListResponse, RequestRecord, RequestSummary } from "@/types";

interface UseRequestsOptions {
  page?: number;
  limit?: number;
  provider?: string;
  status?: string;
  search?: string;
  sortBy?: string;
  sortDir?: "asc" | "desc";
}

interface UseRequestsResult {
  data: RequestListResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useRequests(options: UseRequestsOptions = {}): UseRequestsResult {
  const {
    page = 1,
    limit = 20,
    provider,
    status,
    search,
    sortBy = "created_at",
    sortDir = "desc",
  } = options;

  const [data, setData] = useState<RequestListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("limit", String(limit));
    params.set("sort_by", sortBy);
    params.set("sort_dir", sortDir);
    if (provider) params.set("provider", provider);
    if (status) params.set("status", status);
    if (search) params.set("search", search);

    api
      .get<RequestListResponse>(`/api/v1/requests?${params.toString()}`)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof APIError ? err.message : "Failed to load requests");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, limit, provider, status, search, sortBy, sortDir, tick]);

  return { data, isLoading, error, refetch };
}

interface UseRequestDetailResult {
  data: RequestRecord | null;
  isLoading: boolean;
  error: string | null;
}

export function useRequestDetail(requestId: string): UseRequestDetailResult {
  const [data, setData] = useState<RequestRecord | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!requestId) return;
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    api
      .get<RequestRecord>(`/api/v1/requests/${requestId}`)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof APIError ? err.message : "Failed to load request");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [requestId]);

  return { data, isLoading, error };
}
