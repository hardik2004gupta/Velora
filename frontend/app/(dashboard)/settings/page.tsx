import { Metadata } from "next";
import { User, Bell, Shield, Sliders } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

export const metadata: Metadata = { title: "Settings" };

export default function SettingsPage() {
  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your account preferences.</p>
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
            <Button variant="outline" size="sm" className="border-destructive/30 text-destructive hover:bg-destructive/10" disabled>
              Delete Account
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
