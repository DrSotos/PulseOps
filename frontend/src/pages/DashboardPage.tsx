import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  Globe,
  Plus,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { api } from "../services/api";
import { useRealtime } from "../services/sse";
import { DashboardOverview } from "../types";
import { StatusBadge } from "../components/ui/StatusBadge";

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchOverview = useCallback(async () => {
    try {
      const overview = await api.getDashboardOverview();
      setData(overview);
    } catch (err) {
      console.error("Failed to load dashboard overview:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  // Handle live incoming events
  useRealtime(
    useCallback(
      (event) => {
        if (
          event.type === "check_completed" ||
          event.type === "incident_created" ||
          event.type === "incident_resolved"
        ) {
          fetchOverview();
        }
      },
      [fetchOverview]
    )
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500 mr-3" />
        <span>Loading operational telemetry...</span>
      </div>
    );
  }

  const statCards = [
    {
      title: "Total Monitored APIs",
      value: data?.total_endpoints ?? 0,
      icon: Globe,
      color: "text-blue-400",
      bg: "bg-blue-950/20",
    },
    {
      title: "Operational Services",
      value: data?.operational_count ?? 0,
      icon: CheckCircle2,
      color: "text-emerald-400",
      bg: "bg-emerald-950/20",
    },
    {
      title: "Active Outages",
      value: data?.down_count ?? 0,
      icon: XCircle,
      color: "text-rose-400",
      bg: "bg-rose-950/20",
    },
    {
      title: "Degraded Endpoints",
      value: data?.degraded_count ?? 0,
      icon: AlertTriangle,
      color: "text-amber-400",
      bg: "bg-amber-950/20",
    },
    {
      title: "24h Platform Uptime",
      value: `${data?.overall_uptime_percentage ?? 100}%`,
      icon: Activity,
      color: "text-emerald-400",
      bg: "bg-emerald-950/20",
    },
    {
      title: "Average Latency",
      value: data?.average_response_time_ms ? `${data.average_response_time_ms} ms` : "—",
      icon: Clock,
      color: "text-indigo-400",
      bg: "bg-indigo-950/20",
    },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">System Overview</h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time API availability, latency metrics, and incident detection.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setRefreshing(true);
              fetchOverview();
            }}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-2 text-xs font-medium rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800/80 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>

          <Link
            to="/endpoints"
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>New Endpoint</span>
          </Link>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700/80 transition-colors"
            >
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-[11px] font-medium uppercase tracking-wider">{card.title}</span>
                <div className={`p-1.5 rounded-lg ${card.bg}`}>
                  <Icon className={`w-4 h-4 ${card.color}`} />
                </div>
              </div>
              <div className="text-xl font-bold font-mono text-white tracking-tight">{card.value}</div>
            </div>
          );
        })}
      </div>

      {/* Main Grid: Endpoints Table & Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Endpoints Table (2 cols) */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80">
            <h2 className="text-base font-semibold text-white">Monitored Services</h2>
            <Link
              to="/endpoints"
              className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1"
            >
              <span>View all</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {data?.endpoint_health && data.endpoint_health.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-950/50 text-slate-400 text-xs font-mono border-b border-slate-800/60">
                  <tr>
                    <th className="px-6 py-3">Service</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Uptime</th>
                    <th className="px-4 py-3">Latency</th>
                    <th className="px-6 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {data.endpoint_health.map((ep) => (
                    <tr key={ep.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4">
                        <Link to={`/endpoints/${ep.id}`} className="font-medium text-slate-200 hover:text-blue-400">
                          {ep.name}
                        </Link>
                        <span className="block text-xs font-mono text-slate-500 truncate max-w-xs">{ep.url}</span>
                      </td>
                      <td className="px-4 py-4">
                        <StatusBadge status={ep.status} size="sm" />
                      </td>
                      <td className="px-4 py-4 font-mono text-xs text-slate-300">{ep.uptime_percentage}%</td>
                      <td className="px-4 py-4 font-mono text-xs text-slate-300">
                        {ep.latest_response_time_ms ? `${ep.latest_response_time_ms} ms` : "—"}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          to={`/endpoints/${ep.id}`}
                          className="text-xs text-slate-400 hover:text-white px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 transition-colors"
                        >
                          Details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-sm">
              <Globe className="w-8 h-8 mx-auto text-slate-600 mb-2" />
              <p>No endpoints monitored yet.</p>
              <Link to="/endpoints" className="text-blue-400 text-xs underline mt-2 inline-block">
                Add your first API endpoint →
              </Link>
            </div>
          )}
        </div>

        {/* Activity & Incident Timeline (1 col) */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80">
            <h2 className="text-base font-semibold text-white">Recent Activity</h2>
            <Link
              to="/incidents"
              className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1"
            >
              <span>Incidents</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="p-4 flex-1 space-y-3 overflow-y-auto max-h-[460px]">
            {data?.recent_activity && data.recent_activity.length > 0 ? (
              data.recent_activity.map((act) => (
                <div
                  key={act.id}
                  className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/60 flex items-start gap-3 text-xs"
                >
                  <div
                    className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                      act.type.includes("resolved")
                        ? "bg-emerald-400"
                        : act.severity === "critical"
                        ? "bg-rose-500 animate-ping"
                        : "bg-amber-400"
                    }`}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200 truncate">{act.title}</span>
                      <span className="text-[10px] font-mono text-slate-500 shrink-0 ml-2">
                        {new Date(act.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <p className="text-slate-400 mt-1 line-clamp-2">{act.description}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-12 text-center text-slate-500 text-xs">No recent alert events logged.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

