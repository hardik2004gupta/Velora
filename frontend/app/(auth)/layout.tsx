import { Cpu } from "lucide-react";
import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      {/* Subtle background glow */}
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_70%_50%_at_50%_-10%,rgba(99,102,241,0.10),transparent)]" />

      {/* Minimal nav */}
      <header className="relative z-10 border-b border-border/50 bg-background/60 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center px-6">
          <Link href="/" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-velora-500 to-purple-600">
              <Cpu className="h-3.5 w-3.5 text-white" />
            </div>
            <span className="text-sm font-bold tracking-tight">Velora</span>
          </Link>
        </div>
      </header>

      {/* Centered form */}
      <main className="relative z-10 flex min-h-[calc(100vh-3.5rem)] items-center justify-center px-4 py-12">
        {children}
      </main>
    </div>
  );
}
