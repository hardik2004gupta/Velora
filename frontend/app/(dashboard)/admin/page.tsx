import { Metadata } from "next";
import { Shield, Users, BarChart3, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export const metadata: Metadata = { title: "Admin" };

export default function AdminPage() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10">
          <Shield className="h-5 w-5 text-amber-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Admin Panel</h1>
          <p className="text-muted-foreground">Platform-wide management — admin access required.</p>
        </div>
        <Badge variant="warning" className="ml-auto">Admin Only</Badge>
      </div>

      {/* Warning */}
      <div className="rounded-md border border-amber-500/20 bg-amber-500/5 p-4">
        <div className="flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5 shrink-0" />
          <p className="text-sm text-amber-200/80">
            This panel is only accessible to users with{" "}
            <code className="text-amber-400 text-xs">is_admin = true</code>. The backend enforces this
            with the{" "}
            <code className="text-amber-400 text-xs">get_current_admin_user</code> dependency.
          </p>
        </div>
      </div>

      {/* Platform stats */}
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: "Total Users", icon: Users, value: "—" },
          { label: "Total Requests", icon: BarChart3, value: "—" },
          { label: "Platform Cost", icon: BarChart3, value: "—" },
        ].map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label} className="border-border/50">
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">{stat.label}</CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* User table */}
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="text-base">All Users</CardTitle>
          <CardDescription>Manage user accounts and status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between rounded-md border border-border/50 p-3">
                <div className="flex items-center gap-3">
                  <Skeleton className="h-8 w-8 rounded-full" />
                  <div className="space-y-1">
                    <Skeleton className="h-3.5 w-32" />
                    <Skeleton className="h-3 w-44" />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Skeleton className="h-5 w-14 rounded-full" />
                  <Skeleton className="h-8 w-20 rounded-md" />
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-md border border-dashed border-border/50 p-4 text-center">
            <p className="text-xs text-muted-foreground">User management requires backend connection.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
