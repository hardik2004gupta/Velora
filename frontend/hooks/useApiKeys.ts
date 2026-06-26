"use client";

import { useCallback, useEffect, useState } from "react";
import { api, APIError } from "@/lib/api";
import type { UserAPIKey, UserAPIKeyCreateResponse } from "@/types";

// ---------------------------------------------------------------------------
// List keys
// ---------------------------------------------------------------------------

export function useApiKeys() {
  const [data, setData] = useState<UserAPIKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    api
      .get<UserAPIKey[]>("/api/v1/api-keys")
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (!cancelled)
          setError(err instanceof APIError ? err.message : "Failed to load API keys");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [tick]);

  return { data, isLoading, error, refetch };
}

// ---------------------------------------------------------------------------
// Create key
// ---------------------------------------------------------------------------

export async function createApiKey(name: string): Promise<UserAPIKeyCreateResponse> {
  return api.post<UserAPIKeyCreateResponse>("/api/v1/api-keys", { name });
}

// ---------------------------------------------------------------------------
// Revoke key
// ---------------------------------------------------------------------------

export async function revokeApiKey(id: string): Promise<void> {
  await api.delete(`/api/v1/api-keys/${id}`);
}

// ---------------------------------------------------------------------------
// Cache stats
// ---------------------------------------------------------------------------

export interface CacheStats {
  hits: number;
  misses: number;
  hit_rate: number;
  total_requests_served: number;
  cached_entries: number;
}

export function useCacheStats() {
  const [data, setData] = useState<CacheStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    api
      .get<CacheStats>("/api/v1/cache/stats")
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (!cancelled)
          setError(err instanceof APIError ? err.message : "Failed to load cache stats");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [tick]);

  return { data, isLoading, error, refetch };
}

export async function clearCache(): Promise<{ cleared: number; message: string }> {
  return api.post<{ cleared: number; message: string }>("/api/v1/cache/clear", {});
}
