"use client";

import { useState } from "react";
import { User, Shield, Sliders, Database, RefreshCw, Trash2, Check } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useCacheStats, clearCache } from "@/hooks/useApiKeys";

// ---------------------------------------------------------------------------
// Cache management section
// ---------------------------------------------------------------------------

function CacheSection() {
  const { data, isLoading, refetch } = useCacheStats();
  const [clearing, setClearing] = useState(false);
  const [clearMsg, setClearMsg] = useState<string | null>(null);

  async function handleClear() {
    setClearing(true);
    setClearMsg(null);
    try {
      const result = await clearCache();
      setClearMsg(result.message);
      refetch();
    } catch {
      setClearMsg("Failed to clear cache.");
    } finally {
      setClearing(false);
    }
  }

  const hitRatePct = data ? Math.round(data.hit_rate * 100) : null;

  return (
    <Card className="border-border/50">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Database className="h-4 w-4 text-velora-400" />
          <CardTitle className="text-base">Prompt Cache</CardTitle>
        </div>
        <CardDescription>
          Redis-backed prompt caching — identical requests return cached responses instantly.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {(
            [
              {
                label: "Hit Rate",
                value: isLoading ? "—" : `${hitRatePct}%`,
                highlight: hitRatePct !== null && hitRatePct >= 30,
              },
              {
                label: "Cache Hits",
                value: isLoading ? "—" : (data?.hits.toLocaleString() ?? "—"),
                highlight: false,
              },
              {
                label: "Cache Misses",
                value: isLoading ? "—" : (data?.misses.toLocaleString() ?? "—"),
                highlight: false,
              },
              {
                label: "Cached Entries",
                value: isLoading ? "—" : (data?.cached_entries.toLocaleString() ?? "—"),
                highlight: false,
              },
            ] as const
          ).map((stat) => (
            <div
              key={stat.label}
              className="rounded-md border border-border/50 p-3 text-center"
            >
              <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
              <p
                className={`text-lg font-mono font-semibold ${
                  stat.highlight ? "text-emerald-400" : ""
                }`}
              >
                {stat.value}
              </p>
            </div>
          ))}
        </div>

        <Separator />

        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Cache TTL</p>
            <p className="text-xs text-muted-foreground">
              Cached responses expire after <strong>1 hour</strong>. Clear manually to invalidate early.
            </p>
          </div>
          <Badge variant="outline" className="font-mono text-xs">3600s</Badge>
        </div>

        {clearMsg && (
          <div className="flex items-center gap-1.5 text-xs text-emerald-400">
            <Check className="h-3.5 w-3.5" />
            {clearMsg}
          </div>
        )}

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refetch}
            disabled={isLoading}
          >
            {isLoading ? (
              <RefreshCw className="mr-1.5 h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
            )}
            Refresh Stats
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="border-destructive/30 text-destructive hover:bg-destructive/10"
            onClick={handleClear}
            disabled={clearing}
          >
            {clearing ? (
              <RefreshCw className="mr-1.5 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Trash2 className="mr-1.5 h-3.5 w-3.5" />
            )}
            Clear Cache
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function SettingsPage() {
  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Settings</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">Manage your account preferences.</p>
      </div>

      {/* Profile */}
      <Card className="border-border/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <User className="h-4 w-4 text-velora-400" />
            <CardTitle className="text-base">Profile</CardTitle>
          </div>
          <CardDescription>Your account information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Full Name</Label>
              <Input placeholder="Your name" disabled />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input type="email" placeholder="you@example.com" disabled />
            </div>
          </div>
          <Button variant="outline" size="sm" disabled>
            Update Profile
          </Button>
        </CardContent>
      </Card>

      {/* Inference defaults */}
      <Card className="border-border/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sliders className="h-4 w-4 text-velora-400" />
            <CardTitle className="text-base">Inference Defaults</CardTitle>
          </div>
          <CardDescription>Default parameters for the Playground</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Default Routing Strategy</Label>
              <div className="rounded-md border border-border/50 px-3 py-2 text-sm text-muted-foreground bg-muted/30">
                Auto (composite score)
              </div>
            </div>
            <div className="space-y-2">
              <Label>Max Tokens</Label>
              <Input type="number" placeholder="2048" disabled />
            </div>
            <div className="space-y-2">
              <Label>Temperature</Label>
              <Input type="number" placeholder="0.70" step="0.01" min="0" max="2" disabled />
            </div>
          </div>
          <Button variant="outline" size="sm" disabled>
            Save Defaults
          </Button>
        </CardContent>
      </Card>

      {/* Cache management */}
      <CacheSection />

      {/* Security */}
      <Card className="border-border/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-velora-400" />
            <CardTitle className="text-base">Security</CardTitle>
          </div>
          <CardDescription>Password and account security</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Change Password</Label>
            <Input type="password" placeholder="Current password" disabled />
            <Input type="password" placeholder="New password (min. 8 chars)" disabled />
          </div>
          <Button variant="outline" size="sm" disabled>
            Update Password
          </Button>
          <Separator />
          <div>
            <p className="text-sm font-medium text-destructive">Danger Zone</p>
            <p className="text-xs text-muted-foreground mt-1 mb-3">
              Permanently delete your account and all associated data.
            </p>
            <Button
              variant="outline"
              size="sm"
              className="border-destructive/30 text-destructive hover:bg-destructive/10"
              disabled
            >
              Delete Account
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
