"use client";

import { useState } from "react";
import {
  Key,
  Plus,
  Copy,
  Trash2,
  AlertTriangle,
  Check,
  RefreshCw,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useApiKeys, createApiKey, revokeApiKey } from "@/hooks/useApiKeys";
import type { UserAPIKey, UserAPIKeyCreateResponse } from "@/types";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

// ---------------------------------------------------------------------------
// New key dialog
// ---------------------------------------------------------------------------

function CreateKeyForm({
  onCreated,
  onCancel,
}: {
  onCreated: (result: UserAPIKeyCreateResponse) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await createApiKey(name.trim());
      onCreated(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create key");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="key-name">Key name</Label>
        <Input
          id="key-name"
          placeholder="e.g. Production, CI/CD, Local dev"
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={isLoading}
          autoFocus
        />
      </div>
      {error && (
        <p className="text-xs text-destructive">{error}</p>
      )}
      <div className="flex items-center gap-2">
        <Button type="submit" variant="gradient" size="sm" disabled={isLoading || !name.trim()}>
          {isLoading && <RefreshCw className="mr-1.5 h-3.5 w-3.5 animate-spin" />}
          Create Key
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// New key reveal
// ---------------------------------------------------------------------------

function NewKeyReveal({
  result,
  onDone,
}: {
  result: UserAPIKeyCreateResponse;
  onDone: () => void;
}) {
  const [copied, setCopied] = useState(false);

  function copy() {
    navigator.clipboard.writeText(result.key).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-emerald-500/30 bg-emerald-500/5 p-4">
        <div className="flex items-start gap-2 mb-3">
          <AlertTriangle className="h-4 w-4 text-emerald-400 mt-0.5 shrink-0" />
          <p className="text-sm font-medium text-emerald-400">
            Copy this key now — it will never be shown again
          </p>
        </div>
        <div className="flex items-center gap-2">
          <code className="flex-1 rounded bg-card border border-border/50 px-3 py-2 text-xs font-mono text-foreground break-all">
            {result.key}
          </code>
          <Button
            variant="outline"
            size="icon"
            className={cn("shrink-0 h-9 w-9", copied && "border-emerald-500 text-emerald-400")}
            onClick={copy}
          >
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          </Button>
        </div>
      </div>
      <Button size="sm" onClick={onDone}>
        I have copied the key
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Key row
// ---------------------------------------------------------------------------

function KeyRow({
  apiKey,
  onRevoke,
}: {
  apiKey: UserAPIKey;
  onRevoke: (id: string) => Promise<void>;
}) {
  const [revoking, setRevoking] = useState(false);

  async function handleRevoke() {
    setRevoking(true);
    try {
      await onRevoke(apiKey.id);
    } finally {
      setRevoking(false);
    }
  }

  return (
    <div className="flex items-center justify-between rounded-md border border-border/50 p-3">
      <div className="flex items-center gap-3 min-w-0">
        <div className={cn("h-2 w-2 rounded-full shrink-0", apiKey.is_active ? "bg-emerald-400" : "bg-muted-foreground")} />
        <div className="min-w-0">
          <p className="text-sm font-medium truncate">{apiKey.name}</p>
          <p className="text-xs text-muted-foreground font-mono">
            {apiKey.key_prefix}…
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3 shrink-0 ml-4">
        <div className="text-right hidden sm:block">
          <p className="text-xs text-muted-foreground">
            {apiKey.last_used_at ? `Used ${timeAgo(apiKey.last_used_at)}` : "Never used"}
          </p>
          <p className="text-xs text-muted-foreground">
            Created {timeAgo(apiKey.created_at)}
          </p>
        </div>
        <Badge variant={apiKey.is_active ? "success" : "secondary"} className="text-xs">
          {apiKey.is_active ? "active" : "inactive"}
        </Badge>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-destructive hover:bg-destructive/10"
          onClick={handleRevoke}
          disabled={revoking}
        >
          {revoking ? (
            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Trash2 className="h-3.5 w-3.5" />
          )}
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function APIKeysPage() {
  const { data: keys, isLoading, error, refetch } = useApiKeys();
  const [showCreate, setShowCreate] = useState(false);
  const [newKey, setNewKey] = useState<UserAPIKeyCreateResponse | null>(null);

  function handleCreated(result: UserAPIKeyCreateResponse) {
    setShowCreate(false);
    setNewKey(result);
  }

  function handleDone() {
    setNewKey(null);
    refetch();
  }

  async function handleRevoke(id: string) {
    try {
      await revokeApiKey(id);
      refetch();
    } catch {
      // ignore — key row handles its own loading state
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">API Keys</h1>
          <p className="text-muted-foreground text-sm">
            Personal keys for programmatic access via the{" "}
            <code className="text-[11px] bg-muted px-1 py-0.5 rounded">X-API-Key</code> header.
          </p>
        </div>
        {!showCreate && !newKey && (
          <Button
            variant="gradient"
            className="gap-2"
            onClick={() => setShowCreate(true)}
          >
            <Plus className="h-4 w-4" />
            New Key
          </Button>
        )}
      </div>

      {/* Security notice */}
      <div className="rounded-md border border-velora-500/20 bg-velora-500/5 p-4">
        <div className="flex items-start gap-3">
          <Key className="h-4 w-4 text-velora-400 mt-0.5 shrink-0" />
          <div className="text-sm">
            <p className="font-medium text-velora-400 mb-1">API Key Security</p>
            <p className="text-muted-foreground">
              Keys are shown <strong>once</strong> at creation and stored as bcrypt hashes. Format:{" "}
              <code className="text-velora-400 text-xs">vk-{"{"} 43 chars {"}"}</code>. Rate limit: 20 req/min per key.
            </p>
          </div>
        </div>
      </div>

      {/* New key reveal */}
      {newKey && (
        <Card className="border-emerald-500/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Key Created: {newKey.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <NewKeyReveal result={newKey} onDone={handleDone} />
          </CardContent>
        </Card>
      )}

      {/* Create form */}
      {showCreate && (
        <Card className="border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Create New Key</CardTitle>
            <CardDescription>Give this key a descriptive name</CardDescription>
          </CardHeader>
          <CardContent>
            <CreateKeyForm
              onCreated={handleCreated}
              onCancel={() => setShowCreate(false)}
            />
          </CardContent>
        </Card>
      )}

      {/* Key list */}
      <Card className="border-border/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Your Keys</CardTitle>
          <CardDescription>Active API keys for your account</CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive mb-4">
              {error}
            </div>
          )}

          {isLoading ? (
            <div className="space-y-2">
              {[1, 2].map((i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : keys.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted mb-3">
                <Key className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="font-medium text-sm">No API keys yet</p>
              <p className="text-xs text-muted-foreground mt-1">
                Create a key to access the Velora API programmatically.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {keys.map((k) => (
                <KeyRow key={k.id} apiKey={k} onRevoke={handleRevoke} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Usage example */}
      <Card className="border-border/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Usage</CardTitle>
          <CardDescription>Pass your key in the request header</CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="rounded-md bg-muted/50 border border-border/50 p-4 text-xs font-mono text-muted-foreground overflow-x-auto">
{`curl https://api.velora.dev/api/v1/chat \\
  -H "X-API-Key: vk-YOUR_KEY_HERE" \\
  -H "Content-Type: application/json" \\
  -d '{"messages":[{"role":"user","content":"Hello"}],"routing_strategy":"auto"}'`}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
