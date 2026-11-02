import React, { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Send,
  Play,
  Pause,
  CheckCircle2,
  XCircle,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { api } from "../services/api";
import {
  MonitoredEndpoint,
  MonitoringCheck,
  Incident,
  LatencyStatistics,
  UptimeStatistics,
} from "../types";
import { StatusBadge } from "../components/ui/StatusBadge";
import { LatencyChart } from "../components/ui/LatencyChart";
import { useRealtime } from "../services/sse";
import { useToast } from "../contexts/ToastContext";

export const EndpointDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { showToast } = useToast();
  const [endpoint, setEndpoint] = useState<MonitoredEndpoint | null>(null);
  const [checks, setChecks] = useState<MonitoringCheck[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [uptimeStats, setUptimeStats] = useState<UptimeStatistics | null>(null);
  const [latencyStats, setLatencyStats] = useState<LatencyStatistics | null>(null);
  const [period, setPeriod] = useState<string>("24h");
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);

  const loadData = useCallback(async () => {
    if (!id) return;
    try {
      const [ep, chk, inc, stats] = await Promise.all([
        api.getEndpoint(id),
        api.getEndpointChecks(id, 1, 35),
        api.listIncidents({ endpoint_id: id }),
        api.getEndpointStatistics(id, period),
      ]);
      setEndpoint(ep);
      setChecks(chk.items);
      setIncidents(inc.items);
      setUptimeStats(stats.uptime);
      setLatencyStats(stats.latency);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [id, period]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Live real-time updates
  useRealtime(
    useCallback(
      (event) => {
        if (event.data?.endpoint_id === id) {
          loadData();
        }
      },
      [id, loadData]
    )
  );

  const handleManualCheck = async () => {
    if (!id) return;
    setChecking(true);
    try {
      await api.triggerCheck(id);
      showToast("Diagnostic probe completed successfully", "success");
      await loadData();
    } catch (err: any) {
      showToast(`Check error: ${err.message}`, "error");
    } finally {
      setChecking(false);
    }
  };

  const handleToggleActive = async () => {
    if (!endpoint) return;
    try {
      if (endpoint.is_active) {
        await api.pauseEndpoint(endpoint.id);
        showToast("Endpoint monitoring paused", "info");
      } else {
        await api.resumeEndpoint(endpoint.id);
        showToast("Endpoint monitoring resumed", "success");
      }
      loadData();
    } catch (err: any) {
      showToast(`Action failed: ${err.message}`, "error");
    }
  };

  if (loading || !endpoint) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <RefreshCw className="w-5 h-5 animate-spin text-blue-500 mr-2" />
        <span>Loading endpoint telemetry...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Back button & Title header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link
            to="/endpoints"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Endpoints</span>
          </Link>
          <div className="flex items-center gap-3">
            <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-slate-800 text-blue-400 border border-slate-700">
              {endpoint.http_method}
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white">{endpoint.name}</h1>
            <StatusBadge status={endpoint.current_status} />
          </div>
          <a
            href={endpoint.url}
            target="_blank"
            rel="noreferrer"
            className="text-xs font-mono text-slate-400 hover:text-blue-400 mt-1 inline-flex items-center gap-1"
          >
            <span>{endpoint.url}</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleManualCheck}
            disabled={checking}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition-colors shadow-sm disabled:opacity-50"
          >
            <Send className={`w-3.5 h-3.5 ${checking ? "animate-spin" : ""}`} />
            <span>Test Now</span>
          </button>
          <button
            onClick={handleToggleActive}
            className="flex items-center gap-2 px-3 py-2 text-xs font-medium rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
          >
            {endpoint.is_active ? <Pause className="w-3.5 h-3.5 text-amber-400" /> : <Play className="w-3.5 h-3.5 text-emerald-400" />}
            <span>{endpoint.is_active ? "Pause" : "Resume"}</span>
          </button>
        </div>
      </div>

      {/* Latency Chart & Timeframe Filter */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white">Response Time History</h3>
            <p className="text-xs text-slate-400 mt-0.5">High-precision latency telemetry in milliseconds</p>
          </div>
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-0.5 text-xs font-mono">
            {["1h", "24h", "7d", "30d"].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1 rounded-md transition-colors ${
                  period === p ? "bg-blue-600 text-white font-medium" : "text-slate-400 hover:text-white"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <LatencyChart checks={checks} height={240} />
      </div>

      {/* Statistics Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <span className="text-[10px] text-slate-400 uppercase font-mono">Uptime</span>
          <div className="text-lg font-bold font-mono text-emerald-400 mt-1">
            {uptimeStats?.uptime_percentage ?? 100}%
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            {uptimeStats?.successful_checks ?? 0}/{uptimeStats?.total_checks ?? 0} checks
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <span className="text-[10px] text-slate-400 uppercase font-mono">Avg Latency</span>
          <div className="text-lg font-bold font-mono text-white mt-1">
            {latencyStats?.avg_ms ? `${latencyStats.avg_ms} ms` : "—"}
          </div>
          <span className="text-[10px] text-slate-500 font-mono">{latencyStats?.sample_count ?? 0} samples</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <span className="text-[10px] text-slate-400 uppercase font-mono">P50 (Median)</span>
          <div className="text-lg font-bold font-mono text-indigo-400 mt-1">
            {latencyStats?.p50_ms ? `${latencyStats.p50_ms} ms` : "—"}
          </div>
          <span className="text-[10px] text-slate-500">50th percentile</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <span className="text-[10px] text-slate-400 uppercase font-mono">P90</span>
          <div className="text-lg font-bold font-mono text-blue-400 mt-1">
            {latencyStats?.p90_ms ? `${latencyStats.p90_ms} ms` : "—"}
          </div>
          <span className="text-[10px] text-slate-500">90th percentile</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <span className="text-[10px] text-slate-400 uppercase font-mono">P95</span>
          <div className="text-lg font-bold font-mono text-amber-400 mt-1">
            {latencyStats?.p95_ms ? `${latencyStats.p95_ms} ms` : "—"}
          </div>
          <span className="text-[10px] text-slate-500">95th percentile</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <span className="text-[10px] text-slate-400 uppercase font-mono">P99 (Tail)</span>
          <div className="text-lg font-bold font-mono text-rose-400 mt-1">
            {latencyStats?.p99_ms ? `${latencyStats.p99_ms} ms` : "—"}
          </div>
          <span className="text-[10px] text-slate-500">99th percentile</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <span className="text-[10px] text-slate-400 uppercase font-mono">Check Frequency</span>
          <div className="text-lg font-bold font-mono text-slate-200 mt-1">
            {endpoint.monitoring_interval}s
          </div>
          <span className="text-[10px] text-slate-500">Timeout {endpoint.timeout}s</span>
        </div>
      </div>

      {/* Two columns: Recent Probes & Associated Incidents */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Checks (2 cols) */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800/80">
            <h3 className="text-sm font-semibold text-white">Recent Health Probes</h3>
          </div>
          <div className="overflow-x-auto max-h-[400px]">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 font-mono border-b border-slate-800/80 sticky top-0">
                <tr>
                  <th className="px-6 py-3">Timestamp</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">HTTP Code</th>
                  <th className="px-4 py-3">Duration</th>
                  <th className="px-6 py-3">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {checks.map((chk) => (
                  <tr key={chk.id} className="hover:bg-slate-800/20 font-mono">
                    <td className="px-6 py-3 text-slate-400">
                      {new Date(chk.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      {chk.is_successful ? (
                        <span className="text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> OK
                        </span>
                      ) : (
                        <span className="text-rose-400 flex items-center gap-1">
                          <XCircle className="w-3.5 h-3.5" /> FAIL
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-200">{chk.status_code || "—"}</td>
                    <td className="px-4 py-3 text-slate-300">
                      {chk.response_time_ms ? `${chk.response_time_ms} ms` : "—"}
                    </td>
                    <td className="px-6 py-3 text-slate-400 truncate max-w-xs font-sans">
                      {chk.error_message || "Probe passed successfully"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Associated Incidents (1 col) */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden flex flex-col">
          <div className="px-6 py-4 border-b border-slate-800/80">
            <h3 className="text-sm font-semibold text-white">Incidents History</h3>
          </div>
          <div className="p-4 flex-1 space-y-3 overflow-y-auto max-h-[400px]">
            {incidents.length > 0 ? (
              incidents.map((inc) => (
                <Link
                  key={inc.id}
                  to={`/incidents/${inc.id}`}
                  className="block p-3 rounded-lg bg-slate-950/60 border border-slate-800/60 hover:border-slate-700 transition-colors text-xs"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-slate-200 capitalize">{inc.incident_type.replace("_", " ")}</span>
                    <span
                      className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded ${
                        inc.status === "resolved" ? "text-emerald-400 bg-emerald-950/50" : "text-rose-400 bg-rose-950/50"
                      }`}
                    >
                      {inc.status}
                    </span>
                  </div>
                  <p className="text-slate-400 line-clamp-2">{inc.description}</p>
                  <div className="text-[10px] font-mono text-slate-500 mt-2">
                    Started: {new Date(inc.started_at).toLocaleString()}
                  </div>
                </Link>
              ))
            ) : (
              <div className="py-12 text-center text-slate-500 text-xs">No incidents recorded for this endpoint.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
