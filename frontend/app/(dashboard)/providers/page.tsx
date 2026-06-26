import { Metadata } from "next";
import { Zap, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const metadata: Metadata = { title: "Provider Status" };

const providers = [
  {
    name: "OpenAI",
    models: ["gpt-4o", "gpt-4o-mini"],
    status: "healthy" as const,
    latency: null,
    uptime: null,
  },
  {
    name: "Anthropic",
    models: ["claude-sonnet-4-6", "claude-haiku-4-5"],
    status: "healthy" as const,
    latency: null,
    uptime: null,
  },
  {
    name: "Gemini",
    models: ["gemini-2.0-flash", "gemini-2.0-pro"],
    status: "healthy" as const,
    latency: null,
    uptime: null,
  },
];

const statusConfig = {
  healthy: { icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/10", badge: "success" as const },
  degraded: { icon: AlertTriangle, color: "text-amber-400", bg: "bg-amber-500/10", badge: "warning" as const },
  down: { icon: XCircle, color: "text-red-400", bg: "bg-red-500/10", badge: "error" as const },
};

export default function ProvidersPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Provider Status</h1>
        <p className="text-muted-foreground">
          Real-time health monitoring for all connected AI providers.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {providers.map((provider) => {
          const cfg = statusConfig[provider.status];
          const Icon = cfg.icon;
          return (
            <Card key={provider.name} className="border-border/50">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`rounded-md p-1.5 ${cfg.bg}`}>
                      <Zap className={`h-4 w-4 ${cfg.color}`} />
                    </div>
                    <CardTitle className="text-base">{provider.name}</CardTitle>
                  </div>
                  <Badge variant={cfg.badge} className="gap-1">
                    <Icon className="h-3 w-3" />
                    {provider.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground">Latency</p>
                    <p className="font-medium">—</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Uptime</p>
                    <p className="font-medium">—</p>
                  </div>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Available models</p>
                  <div className="flex flex-wrap gap-1.5">
                    {provider.models.map((m) => (
                      <Badge key={m} variant="outline" className="text-xs font-mono">
                        {m}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="rounded-md border border-dashed border-border/50 p-6 text-center">
        <p className="text-sm text-muted-foreground">
          Live health checks run every 60 seconds once the backend is connected.
          Provider latency is measured and stored as a rolling average.
        </p>
      </div>
    </div>
  );
}
