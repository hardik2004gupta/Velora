import { Metadata } from "next";
import { MessageSquare, Zap, ChevronDown, Send } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const metadata: Metadata = { title: "Playground" };

export default function PlaygroundPage() {
  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-4 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">AI Playground</h1>
          <p className="text-muted-foreground">
            Chat with any model. Every request goes through Velora&apos;s intelligent router.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Auto routing
          </Badge>
        </div>
      </div>

      <div className="flex flex-1 gap-4 overflow-hidden">
        {/* Chat area */}
        <div className="flex flex-1 flex-col overflow-hidden rounded-lg border border-border/50 bg-card">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="flex h-full items-center justify-center">
              <div className="text-center space-y-3">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-velora-500/10">
                  <MessageSquare className="h-6 w-6 text-velora-400" />
                </div>
                <div>
                  <p className="font-medium">Start a conversation</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Type a message below. Velora will route it to the best available model.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Input */}
          <div className="border-t border-border/50 p-4">
            <div className="flex items-end gap-3">
              <div className="flex-1 rounded-md border border-border bg-background px-3 py-2.5 text-sm text-muted-foreground">
                Message Velora... (requires backend connection)
              </div>
              <button
                disabled
                className="flex h-10 w-10 items-center justify-center rounded-md bg-velora-500/20 text-velora-400"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Routing inspector panel */}
        <div className="hidden w-80 flex-col gap-3 lg:flex">
          <Card className="border-border/50">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-velora-400" />
                <CardTitle className="text-sm">Routing Decision</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-md border border-dashed border-border/50 p-4 text-center">
                <p className="text-xs text-muted-foreground">
                  Routing decisions will appear here after each request.
                </p>
              </div>

              {/* Strategy selector preview */}
              <div>
                <p className="mb-1.5 text-xs font-medium text-muted-foreground">Strategy</p>
                <div className="grid grid-cols-2 gap-1.5">
                  {["Auto", "Cheapest", "Fastest", "Quality"].map((s, i) => (
                    <div
                      key={s}
                      className={`rounded-md border px-2 py-1.5 text-xs font-medium text-center cursor-pointer transition-colors ${
                        i === 0
                          ? "border-velora-500/50 bg-velora-500/10 text-velora-400"
                          : "border-border/50 text-muted-foreground hover:border-border"
                      }`}
                    >
                      {s}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
