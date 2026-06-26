import { Metadata } from "next";
import { Search, Trophy, DollarSign, Clock, Activity } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const metadata: Metadata = { title: "Routing Inspector" };

const mockDecision = {
  strategy: "auto",
  selected: "openai/gpt-4o-mini",
  reason: "Best composite score across quality, cost, and latency",
  candidates: [
    { provider: "openai", model: "gpt-4o-mini", cost_per_1k: 0.00015, avg_latency_ms: 820, health: "healthy", quality_score: 0.78, score: 0.91 },
    { provider: "anthropic", model: "claude-haiku-4-5", cost_per_1k: 0.0008, avg_latency_ms: 950, health: "healthy", quality_score: 0.82, score: 0.84 },
    { provider: "gemini", model: "gemini-2.0-flash", cost_per_1k: 0.0001, avg_latency_ms: 650, health: "healthy", quality_score: 0.72, score: 0.87 },
  ],
};

export default function InspectorPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Routing Inspector</h1>
        <p className="text-muted-foreground">
          Understand exactly why Velora chose each provider — full decision transparency.
        </p>
      </div>

      {/* How it works */}
      <Card className="border-velora-500/20 bg-velora-500/5">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-velora-400" />
            <CardTitle className="text-sm text-velora-400">How the Inspector Works</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Every request through Velora generates a{" "}
            <code className="text-velora-400 text-xs">RoutingDecision</code> object. It shows all
            candidate providers, their scores, and why the winning provider was selected. This makes
            AI routing completely explainable — no black-box decisions.
          </p>
        </CardContent>
      </Card>

      {/* Example decision */}
      <div>
        <h2 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Example Decision
        </h2>
        <Card className="border-border/50">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="info">Strategy: {mockDecision.strategy}</Badge>
                <Badge variant="success">Selected: {mockDecision.selected}</Badge>
              </div>
            </div>
            <CardDescription>{mockDecision.reason}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {mockDecision.candidates.map((c, i) => (
                <div
                  key={c.provider}
                  className={`rounded-md border p-3 ${
                    i === 0
                      ? "border-velora-500/30 bg-velora-500/5"
                      : "border-border/50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {i === 0 && <Trophy className="h-3.5 w-3.5 text-amber-400" />}
                      <span className="text-sm font-medium capitalize">{c.provider}</span>
                      <span className="text-xs text-muted-foreground">/ {c.model}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-sm font-bold text-velora-400">{c.score.toFixed(2)}</span>
                      <span className="text-xs text-muted-foreground">score</span>
                    </div>
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-3 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <DollarSign className="h-3 w-3" />
                      ${c.cost_per_1k}/1K
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {c.avg_latency_ms}ms
                    </div>
                    <div className="flex items-center gap-1">
                      <Activity className="h-3 w-3" />
                      {(c.quality_score * 100).toFixed(0)}% quality
                    </div>
                  </div>
                  {/* Score bar */}
                  <div className="mt-2 h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full rounded-full bg-velora-500"
                      style={{ width: `${c.score * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="rounded-md border border-dashed border-border/50 p-6 text-center">
        <p className="text-sm text-muted-foreground">
          Use the <a href="/playground" className="text-velora-400 hover:underline">Playground</a> to
          generate real routing decisions, or browse{" "}
          <a href="/history" className="text-velora-400 hover:underline">History</a> to inspect past requests.
        </p>
      </div>
    </div>
  );
}
