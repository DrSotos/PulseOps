import React, { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Bell,
  Activity,
  RefreshCw,
} from "lucide-react";
import { api } from "../services/api";
import { Incident, NotificationDelivery } from "../types";
import { useToast } from "../contexts/ToastContext";

export const IncidentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { showToast } = useToast();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [deliveries, setDeliveries] = useState<NotificationDelivery[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!id) return;
    try {
      const [inc, notifs] = await Promise.all([
        api.getIncident(id),
        api.getIncidentNotifications(id),
      ]);
      setIncident(inc);
      setDeliveries(notifs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAcknowledge = async () => {
    if (!id) return;
    try {
      await api.acknowledgeIncident(id);
      showToast("Incident acknowledged", "info");
      loadData();
    } catch (err: any) {
      showToast(err.message, "error");
    }
  };

  if (loading || !incident) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <RefreshCw className="w-5 h-5 animate-spin text-blue-500 mr-2" />
        <span>Loading incident audit...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <Link
          to="/incidents"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white mb-2"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Incidents</span>
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-rose-950/50 text-rose-400 border border-rose-800/60 font-bold">
                {incident.severity}
              </span>
              <h1 className="text-2xl font-bold tracking-tight text-white capitalize">
                {incident.incident_type.replace("_", " ")} Incident
              </h1>
            </div>
            <p className="text-sm text-slate-400 mt-1">{incident.description}</p>
          </div>

          {incident.status === "open" && (
            <button
              onClick={handleAcknowledge}
              className="px-4 py-2 rounded-lg bg-amber-600 text-white font-medium text-xs hover:bg-amber-500 transition-colors shadow-sm self-start sm:self-auto"
            >
              Acknowledge Incident
            </button>
          )}
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <span className="text-[11px] font-medium text-slate-400 uppercase">Status</span>
          <div className="text-lg font-bold font-mono text-white mt-1 uppercase">
            {incident.status}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <span className="text-[11px] font-medium text-slate-400 uppercase">Target Service</span>
          <div className="text-sm font-semibold text-blue-400 mt-1 truncate">
            <Link to={`/endpoints/${incident.endpoint_id}`} className="hover:underline">
              {incident.endpoint_name || "Endpoint"}
            </Link>
          </div>
          <span className="block text-[11px] font-mono text-slate-500 truncate mt-0.5">
            {incident.endpoint_url}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <span className="text-[11px] font-medium text-slate-400 uppercase">Detection Time</span>
          <div className="text-xs font-mono text-slate-200 mt-1">
            {new Date(incident.started_at).toLocaleString()}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <span className="text-[11px] font-medium text-slate-400 uppercase">Resolution Time</span>
          <div className="text-xs font-mono text-slate-200 mt-1">
            {incident.resolved_at ? new Date(incident.resolved_at).toLocaleString() : "Ongoing"}
          </div>
        </div>
      </div>

      {/* Incident Event Timeline */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6">
        <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-blue-400" />
          <span>Incident Event Timeline</span>
        </h3>

        <div className="space-y-4">
          {incident.events && incident.events.length > 0 ? (
            incident.events.map((evt, idx) => (
              <div key={evt.id} className="flex items-start gap-4 text-xs">
                <div className="flex flex-col items-center">
                  <div
                    className={`w-3 h-3 rounded-full mt-1 ${
                      evt.event_type === "resolved"
                        ? "bg-emerald-400"
                        : evt.event_type === "acknowledged"
                        ? "bg-amber-400"
                        : "bg-rose-400"
                    }`}
                  />
                  {idx < (incident.events?.length ?? 0) - 1 && (
                    <div className="w-0.5 h-8 bg-slate-800 my-1" />
                  )}
                </div>
                <div className="flex-1 pb-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200 uppercase font-mono tracking-wider">
                      {evt.event_type}
                    </span>
                    <span className="text-slate-500 font-mono">
                      {new Date(evt.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-slate-400 mt-1">{evt.description}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-slate-500 text-xs">No timeline events recorded.</div>
          )}
        </div>
      </div>

      {/* Notification Deliveries */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6">
        <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <Bell className="w-4 h-4 text-indigo-400" />
          <span>Notification Deliveries</span>
        </h3>

        {deliveries.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="text-slate-400 border-b border-slate-800 pb-2">
                <tr>
                  <th className="py-2">Event</th>
                  <th className="py-2">Status</th>
                  <th className="py-2">Attempts</th>
                  <th className="py-2">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {deliveries.map((d) => (
                  <tr key={d.id}>
                    <td className="py-3 text-slate-300">{d.event_type}</td>
                    <td className="py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                          d.delivery_status === "delivered"
                            ? "text-emerald-400 bg-emerald-950/40"
                            : "text-rose-400 bg-rose-950/40"
                        }`}
                      >
                        {d.delivery_status}
                      </span>
                    </td>
                    <td className="py-3 text-slate-400">{d.attempts}</td>
                    <td className="py-3 text-slate-500">{new Date(d.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-slate-500 text-xs">No notifications were dispatched for this event.</div>
        )}
      </div>
    </div>
  );
};
