import Link from "next/link";
import {
  Cpu,
  Zap,
  DollarSign,
  Search,
  Shield,
  Github,
  ArrowRight,
  CheckCircle2,
  Linkedin,
  Activity,
  Database,
  ChevronRight,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const features = [
  {
    icon: Zap,
    title: "Intelligent Routing",
    description:
      "Deterministic, rule-based routing across OpenAI, Anthropic, and Gemini. Four strategies: Auto, Cheapest, Fastest, and Highest Quality.",
    iconBg: "bg-velora-500/10",
    iconColor: "text-velora-400",
  },
  {
    icon: Search,
    title: "Routing Decision Inspector",
    description:
      "Every request exposes a full RoutingDecision object: all candidates, per-dimension scores, and the exact reason the winning provider was chosen.",
    iconBg: "bg-purple-500/10",
    iconColor: "text-purple-400",
  },
  {
    icon: DollarSign,
    title: "Cost Analytics",
    description:
      "Per-request cost tracking with USD-accurate pricing tables. Daily spend trends, provider cost comparison, and cache savings reports.",
    iconBg: "bg-emerald-500/10",
    iconColor: "text-emerald-400",
  },
  {
    icon: Activity,
    title: "Latency Monitoring",
    description:
      "Rolling average latency per provider stored in Redis. Health checks every 60 seconds with automatic degraded-provider penalty scoring.",
    iconBg: "bg-amber-500/10",
    iconColor: "text-amber-400",
  },
  {
    icon: Shield,
    title: "Enterprise Auth",
    description:
      "JWT access tokens plus personal API keys. bcrypt-hashed credentials, prefix-based key lookup, and role-based access control.",
    iconBg: "bg-blue-500/10",
    iconColor: "text-blue-400",
  },
  {
    icon: Database,
    title: "Redis Caching",
    description:
      "SHA-256 prompt hashing with 1-hour TTL. Identical prompts return cached completions, eliminating redundant provider calls.",
    iconBg: "bg-rose-500/10",
    iconColor: "text-rose-400",
  },
];

const stats = [
  { label: "LLM Providers", value: "3" },
  { label: "Models supported", value: "6" },
  { label: "Routing strategies", value: "4" },
  { label: "Deterministic", value: "100%" },
];

const techStack = [
  {
    layer: "Frontend",
    color: "border-velora-500/25 bg-velora-500/5",
    items: ["Next.js 15", "TypeScript", "Tailwind CSS", "shadcn/ui", "TanStack Query", "Recharts"],
  },
  {
    layer: "Backend",
    color: "border-purple-500/25 bg-purple-500/5",
    items: ["FastAPI", "SQLAlchemy 2.0", "Alembic", "Pydantic v2", "httpx", "APScheduler"],
  },
  {
    layer: "Infrastructure",
    color: "border-emerald-500/25 bg-emerald-500/5",
    items: ["PostgreSQL (Neon)", "Redis (Upstash)", "Docker", "Railway", "Vercel", "GitHub Actions"],
  },
];

const providers = [
  { name: "OpenAI", model: "gpt-4o-mini", textColor: "text-green-400", dot: "bg-green-400" },
  { name: "Anthropic", model: "claude-haiku-4-5", textColor: "text-orange-400", dot: "bg-orange-400" },
  { name: "Google Gemini", model: "gemini-2.0-flash", textColor: "text-blue-400", dot: "bg-blue-400" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Layered radial backgrounds */}
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(99,102,241,0.12),transparent)]" />
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_60%_40%_at_80%_80%,rgba(139,92,246,0.07),transparent)]" />

      {/* Sticky nav */}
      <nav className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-velora-500 to-purple-600 shadow-md shadow-velora-500/20">
              <Cpu className="h-3.5 w-3.5 text-white" />
            </div>
            <span className="text-sm font-bold tracking-tight">Velora</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Button asChild variant="ghost" size="sm" className="h-8 text-sm text-muted-foreground hover:text-foreground">
              <Link href="/login">Sign in</Link>
            </Button>
            <Button asChild size="sm" className="h-8 bg-velora-600 text-white hover:bg-velora-500 text-sm">
              <Link href="/register">Get started</Link>
            </Button>
          </div>
        </div>
      </nav>

      <main>
        {/* Hero */}
        <section className="mx-auto max-w-6xl px-6 pb-16 pt-20 text-center">
          <Badge
            variant="outline"
            className="mb-8 inline-flex items-center gap-2 border-velora-500/25 bg-velora-500/8 px-3 py-1 text-velora-400"
          >
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-velora-400 opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-velora-400" />
            </span>
            Production-Inspired AI Infrastructure
          </Badge>

          <h1 className="mx-auto max-w-3xl text-5xl font-extrabold tracking-tight sm:text-6xl">
            The intelligent gateway{" "}
            <span className="bg-gradient-to-r from-velora-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              for multi-provider AI
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-xl text-base text-muted-foreground leading-relaxed">
            Route requests across OpenAI, Anthropic, and Gemini with deterministic scoring.
            Every decision is fully explainable via the{" "}
            <span className="font-medium text-foreground">Routing Decision Inspector</span>.
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            <Button
              asChild
              size="lg"
              className="h-11 gap-2 bg-velora-600 px-7 text-sm font-semibold text-white hover:bg-velora-500 shadow-lg shadow-velora-600/20"
            >
              <Link href="/register">
                Start for free
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              size="lg"
              className="h-11 gap-2 px-6 text-sm border-border/60 hover:border-border"
            >
              <Link href="https://github.com/hardik2004gupta" target="_blank" rel="noopener noreferrer">
                <Github className="h-4 w-4" />
                View source
              </Link>
            </Button>
          </div>

          {/* Provider pills */}
          <div className="mt-10 flex flex-wrap items-center justify-center gap-2">
            {providers.map((p) => (
              <div
                key={p.name}
                className="flex items-center gap-2 rounded-full border border-border/50 bg-card/50 px-3 py-1.5"
              >
                <span className={`h-1.5 w-1.5 rounded-full ${p.dot}`} />
                <span className={`text-xs font-medium ${p.textColor}`}>{p.name}</span>
                <span className="text-[11px] text-muted-foreground font-mono">{p.model}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Stats bar */}
        <section className="border-y border-border/50 bg-card/30">
          <div className="mx-auto max-w-6xl px-6 py-10">
            <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
              {stats.map((s) => (
                <div key={s.label} className="text-center">
                  <div className="text-3xl font-extrabold tracking-tight">{s.value}</div>
                  <div className="mt-1 text-xs text-muted-foreground">{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="mx-auto max-w-6xl px-6 py-20">
          <div className="mb-12 text-center">
            <h2 className="text-2xl font-bold tracking-tight">Everything you need</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Built for engineers who care about cost, reliability, and explainability.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="rounded-xl border border-border/50 bg-card/50 p-6 transition-all duration-150 hover:border-border hover:bg-card/80"
                >
                  <div className={`mb-4 inline-flex rounded-lg p-2 ${feature.iconBg}`}>
                    <Icon className={`h-4 w-4 ${feature.iconColor}`} />
                  </div>
                  <h3 className="mb-2 text-sm font-semibold">{feature.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* Inspector showcase */}
        <section className="mx-auto max-w-6xl px-6 py-12">
          <div className="overflow-hidden rounded-2xl border border-velora-500/20 bg-gradient-to-br from-velora-500/5 via-transparent to-purple-500/5">
            <div className="p-8 md:p-12">
              <div className="md:grid md:grid-cols-[1fr_1.1fr] md:gap-12 md:items-center">
                <div>
                  <Badge className="mb-4 border-velora-500/30 bg-velora-500/15 text-velora-400 text-[11px]">
                    Signature Feature
                  </Badge>
                  <h2 className="text-2xl font-bold tracking-tight">
                    Routing Decision Inspector
                  </h2>
                  <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
                    Every request exposes the full scoring matrix. See exactly why one provider was chosen
                    — cost delta, latency, quality score, and composite total. No black boxes.
                  </p>
                  <ul className="mt-5 space-y-2">
                    {[
                      "All candidate providers ranked by score",
                      "Per-dimension breakdown: quality, cost, latency, health",
                      "Plain-English reason for selection",
                      "Cache hit and fallback indicators",
                    ].map((item) => (
                      <li key={item} className="flex items-start gap-2 text-xs text-muted-foreground">
                        <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-velora-400" />
                        {item}
                      </li>
                    ))}
                  </ul>
                  <div className="mt-7 flex gap-3">
                    <Button asChild size="sm" className="h-8 bg-velora-600 text-white hover:bg-velora-500 text-xs">
                      <Link href="/register">Try it now</Link>
                    </Button>
                    <Button asChild variant="outline" size="sm" className="h-8 text-xs border-border/60">
                      <Link href="/inspector" className="flex items-center gap-1">
                        See demo <ChevronRight className="h-3 w-3" />
                      </Link>
                    </Button>
                  </div>
                </div>

                {/* Code preview */}
                <div className="mt-8 md:mt-0">
                  <div className="overflow-hidden rounded-xl border border-white/[0.08] bg-[#0d1117] shadow-2xl shadow-black/30">
                    <div className="flex items-center gap-1.5 border-b border-white/[0.06] px-4 py-2.5">
                      <span className="h-2.5 w-2.5 rounded-full bg-red-500/60" />
                      <span className="h-2.5 w-2.5 rounded-full bg-amber-500/60" />
                      <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/60" />
                      <span className="ml-3 text-[11px] text-white/25 font-mono">routing_decision.json</span>
                    </div>
                    <div className="p-5 font-mono text-[11px] leading-relaxed">
                      <span className="text-white/40">{"{"}</span>
                      <br />
                      <span className="text-white/40">{"  "}</span><span className="text-blue-400">&quot;strategy&quot;</span><span className="text-white/40">: </span><span className="text-amber-300">&quot;auto&quot;</span><span className="text-white/40">,</span>
                      <br />
                      <span className="text-white/40">{"  "}</span><span className="text-blue-400">&quot;selected&quot;</span><span className="text-white/40">: </span><span className="text-green-400">&quot;openai/gpt-4o-mini&quot;</span><span className="text-white/40">,</span>
                      <br />
                      <span className="text-white/40">{"  "}</span><span className="text-blue-400">&quot;score&quot;</span><span className="text-white/40">: </span><span className="text-purple-400">0.851</span><span className="text-white/40">,</span>
                      <br />
                      <span className="text-white/40">{"  "}</span><span className="text-blue-400">&quot;score_breakdown&quot;</span><span className="text-white/40">{": {"}</span>
                      <br />
                      <span className="text-white/40">{"    "}</span><span className="text-blue-300">&quot;quality&quot;</span><span className="text-white/40">: </span><span className="text-purple-400">0.78</span><span className="text-white/40">,</span>
                      <br />
                      <span className="text-white/40">{"    "}</span><span className="text-blue-300">&quot;cost&quot;</span><span className="text-white/40">: </span><span className="text-emerald-400">0.91</span><span className="text-white/40">,</span>
                      <br />
                      <span className="text-white/40">{"    "}</span><span className="text-blue-300">&quot;latency&quot;</span><span className="text-white/40">: </span><span className="text-blue-400">0.79</span><span className="text-white/40">,</span>
                      <br />
                      <span className="text-white/40">{"    "}</span><span className="text-blue-300">&quot;health&quot;</span><span className="text-white/40">: </span><span className="text-amber-300">1.00</span>
                      <br />
                      <span className="text-white/40">{"  }"}</span>
                      <br />
                      <span className="text-white/40">{"}"}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Tech stack */}
        <section className="mx-auto max-w-6xl px-6 py-16">
          <div className="mb-10 text-center">
            <div className="mb-3 flex items-center justify-center gap-2">
              <Layers className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                Production tech stack
              </span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight">Every choice justified</h2>
            <p className="mt-2 text-sm text-muted-foreground">No magic, no shortcuts.</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {techStack.map((layer) => (
              <div key={layer.layer} className={`rounded-xl border p-6 ${layer.color}`}>
                <h3 className="mb-4 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                  {layer.layer}
                </h3>
                <ul className="space-y-2">
                  {layer.items.map((item) => (
                    <li key={item} className="flex items-center gap-2 text-xs">
                      <CheckCircle2 className="h-3 w-3 shrink-0 text-velora-400" />
                      <span className="text-foreground/80">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="mx-auto max-w-6xl px-6 py-16 text-center">
          <div className="rounded-2xl border border-border/60 bg-card/50 px-8 py-14">
            <h2 className="text-2xl font-bold tracking-tight">Ready to explore?</h2>
            <p className="mt-3 text-sm text-muted-foreground">
              Create a free account and start routing AI requests in minutes.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Button
                asChild
                size="lg"
                className="h-11 gap-2 bg-velora-600 px-7 text-sm font-semibold text-white hover:bg-velora-500"
              >
                <Link href="/register">
                  Get started free
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="h-11 text-sm border-border/60">
                <Link href="/login">Sign in</Link>
              </Button>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/50">
        <div className="mx-auto max-w-6xl px-6 py-6">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <div className="flex h-5 w-5 items-center justify-center rounded-md bg-gradient-to-br from-velora-500 to-purple-600">
                <Cpu className="h-2.5 w-2.5 text-white" />
              </div>
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
                className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                <Github className="h-3.5 w-3.5" />
                hardik2004gupta
              </Link>
              <Link
                href="https://www.linkedin.com/in/hardikgupta2004/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                <Linkedin className="h-3.5 w-3.5" />
                hardikgupta2004
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
