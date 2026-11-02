import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  CheckCircle,
  Filter,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { api } from "../services/api";
import { Incident } from "../types";
import { useRealtime } from "../services/sse";
import { useToast } from "../contexts/ToastContext";

export const IncidentsPage: React.FC = () => {
  const { showToast } = useToast();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("");

  const loadIncidents = useCallback(async () => {
    try {
      const res = await api.listIncidents({
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
      });
      setIncidents(res.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, severityFilter]);

  useEffect(() => {
    loadIncidents();
  }, [loadIncidents]);

  useRealtime(
    useCallback(
      (event) => {
        if (event.type === "incident_created" || event.type === "incident_resolved") {
          loadIncidents();
        }
      },
      [loadIncidents]
    )
  );

  const handleAcknowledge = async (id: string) => {
    try {
      await api.acknowledgeIncident(id);
      showToast("Incident acknowledged", "info");
      loadIncidents();
    } catch (err: any) {
      showToast(err.message, "error");
    }
  };

  const getSeverityBadge = (sev: string) => {
    const map: Record<string, { bg: string; text: string; border: string }> = {
      critical: { bg: "bg-rose-950/50", text: "text-rose-400", border: "border-rose-800/60" },
      high: { bg: "bg-orange-950/50", text: "text-orange-400", border: "border-orange-800/60" },
      medium: { bg: "bg-amber-950/50", text: "text-amber-400", border: "border-amber-800/60" },
      low: { bg: "bg-blue-950/50", text: "text-blue-400", border: "border-blue-800/60" },
    };
    const c = map[sev.toLowerCase()] || map.medium;
    return (
      <span
        className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-semibold border ${c.bg} ${c.text} ${c.border}`}
      >
        {sev}
      </span>
    );
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Incidents & Outages</h1>
        <p className="text-sm text-slate-400 mt-1">
          Automated incident detection, acknowledgement workflow, and audit timeline.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 p-3.5 rounded-xl">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
            <Filter className="w-3.5 h-3.5" />
            <span>Filters:</span>
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        <button
          onClick={loadIncidents}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Incidents Table */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 flex items-center justify-center gap-3">
            <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />
            <span>Loading incidents...</span>
          </div>
        ) : incidents.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/60 text-slate-400 text-xs font-mono border-b border-slate-800/80">
                <tr>
                  <th className="px-6 py-3.5">Severity</th>
                  <th className="px-4 py-3.5">Affected Service</th>
                  <th className="px-4 py-3.5">Incident Type</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Started At</th>
                  <th className="px-4 py-3.5">Duration</th>
                  <th className="px-6 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {incidents.map((inc) => (
                  <tr key={inc.id} className="hover:bg-slate-800/20 transition-colors">
                    <td className="px-6 py-4">{getSeverityBadge(inc.severity)}</td>
                    <td className="px-4 py-4">
                      <Link
                        to={`/endpoints/${inc.endpoint_id}`}
                        className="font-medium text-slate-200 hover:text-blue-400 block"
                      >
                        {inc.endpoint_name || "Endpoint"}
                      </Link>
                      <span className="block text-xs font-mono text-slate-500 truncate max-w-xs">
                        {inc.endpoint_url}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-xs font-mono text-slate-300 capitalize">
                      {inc.incident_type.replace("_", " ")}
                    </td>
                    <td className="px-4 py-4">
                      <span
                        className={`text-xs font-semibold uppercase ${
                          inc.status === "resolved"
                            ? "text-emerald-400"
                            : inc.status === "acknowledged"
                            ? "text-amber-400"
                            : "text-rose-400 font-bold"
                        }`}
                      >
                        {inc.status}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-xs font-mono text-slate-400">
                      {new Date(inc.started_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-4 text-xs font-mono text-slate-300">
                      {inc.duration_seconds !== null && inc.duration_seconds !== undefined
                        ? `${Math.round(inc.duration_seconds / 60)} min`
                        : "—"}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {inc.status === "open" && (
                          <button
                            onClick={() => handleAcknowledge(inc.id)}
                            className="px-2.5 py-1 rounded bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-600/30 text-xs transition-colors"
                          >
                            Acknowledge
                          </button>
                        )}
                        <Link
                          to={`/incidents/${inc.id}`}
                          className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                          title="View Incident Timeline"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-16 text-center text-slate-500">
            <CheckCircle className="w-10 h-10 mx-auto text-emerald-500 mb-3" />
            <h3 className="text-sm font-semibold text-slate-300">All systems operational</h3>
            <p className="text-xs text-slate-500 mt-1">No incidents match your current filter criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
};
