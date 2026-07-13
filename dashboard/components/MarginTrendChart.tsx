"use client";

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { MonthlyAccountMarginSummary } from "@/lib/types";

export default function MarginTrendChart({ rows }: { rows: MonthlyAccountMarginSummary[] }) {
  const data = [...rows]
    .sort((a, b) => a.month.localeCompare(b.month))
    .map((r) => ({
      month: r.month.slice(0, 7),
      realized: r.realized_margin_pct,
      target: r.target_margin_pct,
      flag: r.margin_flag,
    }));

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
          <CartesianGrid stroke="#D8DCD2" vertical={false} />
          <XAxis
            dataKey="month"
            tick={{ fontSize: 10, fontFamily: "var(--font-plex-mono)", fill: "#6B7A8F" }}
            tickLine={false}
            axisLine={{ stroke: "#D8DCD2" }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 10, fontFamily: "var(--font-plex-mono)", fill: "#6B7A8F" }}
            tickLine={false}
            axisLine={false}
            unit="%"
            width={38}
          />
          <Tooltip
            contentStyle={{
              fontFamily: "var(--font-plex-mono)",
              fontSize: 12,
              border: "1px solid #D8DCD2",
              borderRadius: 2,
            }}
            formatter={(value: number, name: string) => [`${value.toFixed(1)}%`, name === "realized" ? "Realized" : "Target"]}
          />
          <Line type="monotone" dataKey="target" stroke="#6B7A8F" strokeDasharray="4 3" dot={false} strokeWidth={1.5} />
          <Line
            type="monotone"
            dataKey="realized"
            stroke="#1F6E8C"
            strokeWidth={2}
            dot={{ r: 2.5, fill: "#1F6E8C" }}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
