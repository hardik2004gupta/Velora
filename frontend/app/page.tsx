import Link from "next/link";
import {
  Cpu,
  Zap,
  DollarSign,
  BarChart3,
  Search,
  Shield,
  Github,
  ArrowRight,
  CheckCircle2,
  Linkedin,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const features = [
  {
    icon: Zap,
    title: "Intelligent Routing",
    description:
      "Deterministic, rule-based routing across OpenAI, Anthropic, and Gemini. Four strategies: Auto, Cheapest, Fastest, and Highest Quality.",
    color: "text-velora-400",
    bg: "bg-velora-500/10",
  },
  {
    icon: Search,
    title: "Routing Decision Inspector",
    description:
      "Every request exposes a full RoutingDecision object: all candidates, their scores, and the exact reason the winning provider was chosen.",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
  },
  {
    icon: DollarSign,
    title: "Cost Analytics",
    description:
      "Per-request cost tracking with USD-accurate pricing tables. Daily spend trends, provider cost comparison, and cache savings reports.",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
  {
    icon: BarChart3,
    title: "Latency Monitoring",
    description:
      "Rolling average latency per provider stored in Redis. Provider health checks every 60s with automatic degraded-provider penalties.",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
  },
  {
    icon: Shield,
    title: "Enterprise Auth",
    description:
      "JWT access tokens + refresh token rotation. API key authentication with bcrypt hashing and prefix-based lookup. RBAC with 4 roles.",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  {
    icon: Cpu,
    title: "Redis Caching",
    description:
      "SHA-256 prompt hashing with 1-hour TTL. Identical prompts return cached completions — eliminates redundant provider calls.",
    color: "text-pink-400",
    bg: "bg-pink-500/10",
  },
];

const techStack = [
  { layer: "Frontend", items: ["Next.js 15", "TypeScript", "Tailwind CSS", "shadcn/ui", "TanStack Query", "Framer Motion"] },
  { layer: "Backend", items: ["FastAPI", "SQLAlchemy 2.0", "Alembic", "Pydantic v2", "httpx", "APScheduler"] },
  { layer: "Infrastructure", items: ["PostgreSQL (Neon)", "Redis (Upstash)", "Docker", "Railway", "Vercel", "GitHub Actions"] },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Background */}
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-velora-950/40 via-background to-background" />
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_bottom_right,_var(--tw-gradient-stops))] from-purple-950/20 via-transparent to-transparent" />

      {/* Nav */}
      <nav className="relative z-10 border-b border-border/50 bg-background/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-velora-500 to-purple-600">
              <Cpu className="h-3.5 w-3.5 text-white" />
            </div>
            <span className="font-bold tracking-tight">Velora</span>
          </div>
          <div className="flex items-center gap-2">
            <Button asChild variant="ghost" size="sm">
              <Link href="/login">Sign in</Link>
            </Button>
            <Button asChild variant="gradient" size="sm">
              <Link href="/register">Get started</Link>
            </Button>
          </div>
        </div>
      </nav>

      <main className="relative z-10">
        {/* Hero */}
        <section className="mx-auto max-w-7xl px-4 py-24 text-center">
          <Badge variant="outline" className="mb-6 gap-2 border-velora-500/30 bg-velora-500/5 text-velora-400">
            <span className="h-1.5 w-1.5 rounded-full bg-velora-400" />
            Production-Inspired AI Infrastructure
          </Badge>

          <h1 className="mx-auto max-w-3xl text-5xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl">
            The{" "}
            <span className="bg-gradient-to-r from-velora-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              intelligent gateway
            </span>{" "}
            for multi-provider AI
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground leading-relaxed">
            Route AI requests across OpenAI, Anthropic, and Gemini with deterministic scoring.
            Every decision is fully explainable via the{" "}
            <span className="text-foreground font-medium">Routing Decision Inspector</span>.
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Button asChild variant="gradient" size="lg" className="gap-2 text-base px-8">
              <Link href="/register">
                Get started free
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="gap-2 text-base">
              <Link href="https://github.com/hardik2004gupta" target="_blank" rel="noopener noreferrer">
                <Github className="h-4 w-4" />
                View on GitHub
              </Link>
            </Button>
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
            {["OpenAI", "Anthropic", "Gemini"].map((p) => (
              <div key={p} className="flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-velora-400" />
                {p}
              </div>
            ))}
          </div>
        </section>

        {/* Features */}
        <section className="mx-auto max-w-7xl px-4 py-16">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight">Everything you need</h2>
            <p className="mt-3 text-muted-foreground">
              Built for engineers who care about cost, reliability, and explainability.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="rounded-xl border border-border/50 bg-card/50 p-6 backdrop-blur-sm transition-colors hover:border-border"
                >
                  <div className={`mb-4 inline-flex rounded-lg p-2.5 ${feature.bg}`}>
                    <Icon className={`h-5 w-5 ${feature.color}`} />
                  </div>
                  <h3 className="mb-2 text-base font-semibold">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* Architecture highlight */}
        <section className="mx-auto max-w-7xl px-4 py-16">
          <div className="rounded-2xl border border-velora-500/20 bg-velora-500/5 p-8 md:p-12">
            <div className="md:flex md:items-center md:justify-between md:gap-12">
              <div className="max-w-lg">
                <Badge className="mb-4 bg-velora-500/20 text-velora-400 border-velora-500/30">
                  Signature Feature
                </Badge>
                <h2 className="text-3xl font-bold tracking-tight">
                  Routing Decision Inspector
                </h2>
                <p className="mt-4 text-muted-foreground leading-relaxed">
                  Every request exposes the full scoring matrix. See why gpt-4o-mini was chosen over
                  claude-haiku-4-5 — exact cost delta, latency difference, quality score, and the final
                  composite score. No more black-box AI routing.
                </p>
                <div className="mt-6 flex gap-3">
                  <Button asChild variant="gradient" size="sm">
                    <Link href="/register">Try it now</Link>
                  </Button>
                  <Button asChild variant="outline" size="sm">
                    <Link href="/inspector">See example</Link>
                  </Button>
                </div>
              </div>

              {/* Code preview */}
              <div className="mt-8 md:mt-0 md:flex-1">
                <div className="rounded-xl border border-border/50 bg-card/80 backdrop-blur-sm overflow-hidden">
                  <div className="flex items-center gap-2 border-b border-border/50 px-4 py-2.5">
                    <div className="h-2.5 w-2.5 rounded-full bg-red-500/60" />
                    <div className="h-2.5 w-2.5 rounded-full bg-amber-500/60" />
                    <div className="h-2.5 w-2.5 rounded-full bg-emerald-500/60" />
                    <span className="ml-2 text-xs text-muted-foreground">routing_decision.json</span>
                  </div>
                  <pre className="p-4 text-xs leading-relaxed text-muted-foreground overflow-x-auto">
{`{
  "strategy": "auto",
  "selected": "openai/gpt-4o-mini",
  "reason": "Best composite score",
  "candidates": [
    {
      "provider": "openai",
      "model": "gpt-4o-mini",
      "cost_per_1k": 0.00015,
      "avg_latency_ms": 820,
      "quality_score": 0.78,
      "score": 0.91
    },
    {
      "provider": "gemini",
      "model": "gemini-2.0-flash",
      "cost_per_1k": 0.0001,
      "score": 0.87
    }
  ]
}`}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Tech stack */}
        <section className="mx-auto max-w-7xl px-4 py-16">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight">Production tech stack</h2>
            <p className="mt-3 text-muted-foreground">
              Every choice justified. No magic, no shortcuts.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-3">
            {techStack.map((layer) => (
              <div key={layer.layer} className="rounded-xl border border-border/50 bg-card/50 p-6">
                <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                  {layer.layer}
                </h3>
                <ul className="space-y-2">
                  {layer.items.map((item) => (
                    <li key={item} className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="h-3.5 w-3.5 text-velora-400 shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="mx-auto max-w-7xl px-4 py-16 text-center">
          <h2 className="text-3xl font-bold tracking-tight">Ready to explore?</h2>
          <p className="mt-3 text-muted-foreground">
            Create a free account and start routing AI requests in minutes.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Button asChild variant="gradient" size="lg" className="gap-2">
              <Link href="/register">
                Get started free
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/login">Sign in</Link>
            </Button>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border/50 bg-card/30">
        <div className="mx-auto max-w-7xl px-4 py-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Cpu className="h-4 w-4 text-velora-400" />
              <span>
                Designed &amp; Engineered by{" "}
                <span className="font-semibold text-foreground">Hardik Gupta</span>
              </span>
            </div>
            <div className="flex items-center gap-4">
              <Link
                href="https://github.com/hardik2004gupta"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <Github className="h-4 w-4" />
                GitHub
              </Link>
              <Link
                href="https://www.linkedin.com/in/hardikgupta2004/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <Linkedin className="h-4 w-4" />
                LinkedIn
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
