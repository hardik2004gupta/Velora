"use client";

/**
 * Reusable Recharts chart components for the Velora analytics dashboard.
 * All charts are dark-mode aware via CSS variables.
 */

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { CostDataPoint, LatencyDataPoint, ProviderStat } from "@/types";

// ---------------------------------------------------------------------------
// Shared palette
// ---------------------------------------------------------------------------

const COLORS = {
  openai: "#34d399",     // emerald-400
  anthropic: "#fb923c",  // orange-400
  gemini: "#60a5fa",     // blue-400
  success: "#34d399",
  error: "#f87171",
  timeout: "#facc15",
  auto: "#a78bfa",
  cheapest: "#34d399",
  fastest: "#60a5fa",
  quality: "#fb923c",
  manual: "#94a3b8",
};

const GRID_COLOR = "rgba(255,255,255,0.06)";
const TICK_COLOR = "#64748b"; // slate-500
const TOOLTIP_STYLE = {
  backgroundColor: "hsl(var(--card))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "8px",
  color: "hsl(var(--foreground))",
  fontSize: "12px",
};

function formatDate(d: string) {
  return new Date(d).toLocaleDateString([], { month: "short", day: "numeric" });
}

function formatCost(v: number) {
  if (v === 0) return "$0";
  if (v < 0.001) return `$${v.toExponential(1)}`;
  return `$${v.toFixed(4)}`;
}

function formatMs(v: number) {
  return v >= 1000 ? `${(v / 1000).toFixed(1)}s` : `${Math.round(v)}ms`;
}

// ---------------------------------------------------------------------------
// No-data placeholder
// ---------------------------------------------------------------------------

export function NoDataState({ label = "No data for this period" }: { label?: string }) {
  return (
    <div className="flex h-full items-center justify-center">
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Cost area chart (stacked by provider)
// ---------------------------------------------------------------------------

export function CostAreaChart({ data }: { data: CostDataPoint[] }) {
  if (!data.length) return <NoDataState />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
        <defs>
          {(["openai", "anthropic", "gemini"] as const).map((p) => (
            <linearGradient key={p} id={`grad-${p}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={COLORS[p]} stopOpacity={0.3} />
              <stop offset="95%" stopColor={COLORS[p]} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="date" tickFormatter={formatDate} tick={{ fill: TICK_COLOR, fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={formatCost} tick={{ fill: TICK_COLOR, fontSize: 11 }} tickLine={false} axisLine={false} width={60} />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(v: number, name: string) => [formatCost(v), name]}
          labelFormatter={formatDate}
        />
        <Legend
          wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
          iconType="circle"
          iconSize={8}
        />
        {(["openai", "anthropic", "gemini"] as const).map((p) => (
          <Area
            key={p}
            type="monotone"
            dataKey={p}
            stackId="1"
            stroke={COLORS[p]}
            fill={`url(#grad-${p})`}
            strokeWidth={1.5}
            dot={false}
            name={p.charAt(0).toUpperCase() + p.slice(1)}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ---------------------------------------------------------------------------
// Latency line chart
// ---------------------------------------------------------------------------

export function LatencyLineChart({ data }: { data: LatencyDataPoint[] }) {
  if (!data.length) return <NoDataState />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="date" tickFormatter={formatDate} tick={{ fill: TICK_COLOR, fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={formatMs} tick={{ fill: TICK_COLOR, fontSize: 11 }} tickLine={false} axisLine={false} width={56} />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(v: number) => [formatMs(v), "Avg latency"]}
          labelFormatter={formatDate}
        />
        <Line
          type="monotone"
          dataKey="avg_ms"
          stroke="#a78bfa"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: "#a78bfa" }}
          name="Avg latency"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ---------------------------------------------------------------------------
// Provider pie chart
// ---------------------------------------------------------------------------

export function ProviderPieChart({ data }: { data: ProviderStat[] }) {
  if (!data.length) return <NoDataState />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          dataKey="requests"
          nameKey="provider"
          cx="50%"
          cy="50%"
          outerRadius={80}
          innerRadius={48}
          paddingAngle={3}
          label={({ provider, percentage }: { provider: string; percentage: number }) =>
            `${provider} ${percentage}%`
          }
          labelLine={false}
        >
          {data.map((entry) => (
            <Cell
              key={entry.provider}
              fill={COLORS[entry.provider as keyof typeof COLORS] ?? "#94a3b8"}
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(v: number, name: string) => [v.toLocaleString(), name]}
        />
        <Legend
          wrapperStyle={{ fontSize: "11px" }}
          iconType="circle"
          iconSize={8}
          formatter={(value: string) =>
            value.charAt(0).toUpperCase() + value.slice(1)
          }
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

// ---------------------------------------------------------------------------
// Token bar chart (prompt vs completion)
// ---------------------------------------------------------------------------

interface TokenBarData {
  name: string;
  prompt: number;
  completion: number;
}

export function TokenBarChart({ data }: { data: TokenBarData[] }) {
  if (!data.length) return <NoDataState />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: TICK_COLOR, fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fill: TICK_COLOR, fontSize: 11 }} tickLine={false} axisLine={false} width={56} tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)} />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(v: number, name: string) => [v.toLocaleString(), name]}
        />
        <Legend wrapperStyle={{ fontSize: "11px" }} iconType="square" iconSize={8} />
        <Bar dataKey="prompt" stackId="a" fill="#60a5fa" name="Prompt" radius={[0, 0, 0, 0]} />
        <Bar dataKey="completion" stackId="a" fill="#a78bfa" name="Completion" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// ---------------------------------------------------------------------------
// Request status donut chart
// ---------------------------------------------------------------------------

interface StatusData {
  name: string;
  value: number;
}

export function StatusDonutChart({ data }: { data: StatusData[] }) {
  if (!data.length || data.every((d) => d.value === 0)) return <NoDataState />;
  const STATUS_COLORS: Record<string, string> = {
    success: COLORS.success,
    error: COLORS.error,
    timeout: COLORS.timeout,
  };
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={75}
          innerRadius={46}
          paddingAngle={3}
        >
          {data.map((entry) => (
            <Cell
              key={entry.name}
              fill={STATUS_COLORS[entry.name] ?? "#94a3b8"}
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(v: number, name: string) => [v.toLocaleString(), name]}
        />
        <Legend wrapperStyle={{ fontSize: "11px" }} iconType="circle" iconSize={8} />
      </PieChart>
    </ResponsiveContainer>
  );
}

// ---------------------------------------------------------------------------
// Routing strategy bar chart
// ---------------------------------------------------------------------------

export function RoutingBarChart({ data }: { data: { strategy: string; count: number }[] }) {
  if (!data.length) return <NoDataState />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} horizontal={false} />
        <XAxis type="number" tick={{ fill: TICK_COLOR, fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis
          type="category"
          dataKey="strategy"
          tick={{ fill: TICK_COLOR, fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={64}
        />
        <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: number) => [v.toLocaleString(), "requests"]} />
        <Bar dataKey="count" radius={[0, 3, 3, 0]} name="Requests">
          {data.map((entry) => (
            <Cell
              key={entry.strategy}
              fill={COLORS[entry.strategy as keyof typeof COLORS] ?? "#94a3b8"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
