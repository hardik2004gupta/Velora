import { Metadata } from "next";
import { History, Filter } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export const metadata: Metadata = { title: "Request History" };

export default function HistoryPage() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Request History</h1>
          <p className="text-muted-foreground">Browse and filter your inference request log.</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-md border border-border/50 px-3 py-2 text-sm text-muted-foreground">
            <Filter className="h-4 w-4" />
            Filter
          </div>
        </div>
      </div>

      <Card className="border-border/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">All Requests</CardTitle>
          <CardDescription>Paginated request log with routing details</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Table header */}
          <div className="grid grid-cols-6 gap-4 border-b border-border/50 pb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            <span className="col-span-2">Model</span>
            <span>Strategy</span>
            <span>Tokens</span>
            <span>Cost</span>
            <span>Status</span>
          </div>

          {/* Skeleton rows */}
          <div className="mt-3 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="grid grid-cols-6 gap-4 items-center py-2">
                <div className="col-span-2 flex flex-col gap-1">
                  <Skeleton className="h-3.5 w-32" />
                  <Skeleton className="h-3 w-20" />
                </div>
                <Skeleton className="h-5 w-16 rounded-full" />
                <Skeleton className="h-3.5 w-16" />
                <Skeleton className="h-3.5 w-14" />
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
            ))}
          </div>

          <div className="mt-4 rounded-md border border-dashed border-border/50 p-4 text-center">
            <p className="text-xs text-muted-foreground">
              Request history loads from the backend API. Connect the backend to see live data.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
