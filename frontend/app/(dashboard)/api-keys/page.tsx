import { Metadata } from "next";
import { Key, Plus, Copy, Trash2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export const metadata: Metadata = { title: "API Keys" };

export default function APIKeysPage() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">API Keys</h1>
          <p className="text-muted-foreground">
            Manage programmatic access keys for your organization.
          </p>
        </div>
        <Button variant="gradient" className="gap-2" disabled>
          <Plus className="h-4 w-4" />
          New Key
        </Button>
      </div>

      {/* Info box */}
      <div className="rounded-md border border-velora-500/20 bg-velora-500/5 p-4">
        <div className="flex items-start gap-3">
          <Key className="h-4 w-4 text-velora-400 mt-0.5 shrink-0" />
          <div className="text-sm">
            <p className="font-medium text-velora-400 mb-1">API Key Security</p>
            <p className="text-muted-foreground">
              Keys are shown <strong>once</strong> at creation and stored as bcrypt hashes.
              Use the <code className="text-velora-400 text-xs">X-API-Key</code> header to authenticate
              programmatic requests. Format:{" "}
              <code className="text-velora-400 text-xs">vk-{"{"}32-random-chars{"}"}</code>
            </p>
          </div>
        </div>
      </div>

      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="text-base">Your Keys</CardTitle>
          <CardDescription>Active API keys for this organization</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Empty state */}
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted mb-3">
              <Key className="h-6 w-6 text-muted-foreground" />
            </div>
            <p className="font-medium text-sm">No API keys yet</p>
            <p className="text-xs text-muted-foreground mt-1">
              Create an organization first, then generate keys for programmatic access.
            </p>
          </div>

          {/* Example row (static) */}
          <div className="mt-4 space-y-2 opacity-40 pointer-events-none">
            <div className="flex items-center justify-between rounded-md border border-border/50 p-3">
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 rounded-full bg-emerald-400" />
                <div>
                  <p className="text-sm font-medium">Production Key</p>
                  <p className="text-xs text-muted-foreground font-mono">vk-aBcD1234…</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="success">active</Badge>
                <Badge variant="outline">developer</Badge>
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Copy className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive">
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
