import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { MonitoringCheck } from "../../types";

interface LatencyChartProps {
  checks: MonitoringCheck[];
  height?: number;
}

export const LatencyChart: React.FC<LatencyChartProps> = ({ checks, height = 220 }) => {
  // Sort chronologically ascending for chart rendering
  const data = [...checks]
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    .map((c) => ({
      time: new Date(c.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
      latency: c.response_time_ms ?? 0,
      status: c.status_code ?? 0,
      success: c.is_successful,
    }));

  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center border border-dashed border-slate-800 rounded-lg text-slate-500 text-sm"
        style={{ height }}
      >
        No latency data recorded yet for this timeframe.
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey="time"
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            axisLine={{ stroke: "#334155" }}
          />
          <YAxis
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            axisLine={{ stroke: "#334155" }}
            unit="ms"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              borderColor: "#334155",
              borderRadius: "6px",
              fontSize: "12px",
              color: "#f8fafc",
            }}
            formatter={(value: any) => [`${value} ms`, "Response Time"]}
            labelFormatter={(label) => `Time: ${label}`}
          />
          <Area
            type="monotone"
            dataKey="latency"
            stroke="#3b82f6"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#latencyGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

