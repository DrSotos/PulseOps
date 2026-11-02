import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  Globe,
  Plus,
  Search,
  Play,
  Pause,
  Trash2,
  ExternalLink,
  RefreshCw,
  Send,
  AlertCircle,
} from "lucide-react";
import { api } from "../services/api";
import { MonitoredEndpoint } from "../types";
import { StatusBadge } from "../components/ui/StatusBadge";
import { Modal } from "../components/ui/Modal";
import { useToast } from "../contexts/ToastContext";

export const EndpointsPage: React.FC = () => {
  const { showToast } = useToast();
  const [endpoints, setEndpoints] = useState<MonitoredEndpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // New endpoint form state
  const [formData, setFormData] = useState({
    name: "",
    url: "",
    http_method: "GET",
    monitoring_interval: 60,
    timeout: 10,
    expected_status_codes: "200",
    performance_threshold_ms: "",
    expected_content: "",
  });

  const loadEndpoints = useCallback(async () => {
    try {
      const res = await api.listEndpoints({ search });
      setEndpoints(res.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    loadEndpoints();
  }, [loadEndpoints]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);

    const statuses = formData.expected_status_codes
      .split(",")
      .map((s) => parseInt(s.trim()))
      .filter((n) => !isNaN(n));

    try {
      await api.createEndpoint({
        name: formData.name,
        url: formData.url,
        http_method: formData.http_method as any,
        monitoring_interval: Number(formData.monitoring_interval),
        timeout: Number(formData.timeout),
        expected_status_codes: statuses.length > 0 ? statuses : [200],
        performance_threshold_ms: formData.performance_threshold_ms
          ? Number(formData.performance_threshold_ms)
          : null,
        expected_content: formData.expected_content || null,
        is_active: true,
      });

      setModalOpen(false);
      setFormData({
        name: "",
        url: "",
        http_method: "GET",
        monitoring_interval: 60,
        timeout: 10,
        expected_status_codes: "200",
        performance_threshold_ms: "",
        expected_content: "",
      });
      showToast("Endpoint created successfully", "success");
      loadEndpoints();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to create endpoint.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleTriggerCheck = async (id: string) => {
    try {
      await api.triggerCheck(id);
      showToast("Check initiated", "info");
      loadEndpoints();
    } catch (err: any) {
      showToast(`Check failed: ${err.message}`, "error");
    }
  };

  const handleToggleActive = async (ep: MonitoredEndpoint) => {
    try {
      if (ep.is_active) {
        await api.pauseEndpoint(ep.id);
        showToast(`Paused ${ep.name}`, "info");
      } else {
        await api.resumeEndpoint(ep.id);
        showToast(`Resumed ${ep.name}`, "success");
      }
      loadEndpoints();
    } catch (err: any) {
      showToast(`Action failed: ${err.message}`, "error");
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete ${name}? All monitoring history and incidents will be removed.`)) {
      return;
    }
    try {
      await api.deleteEndpoint(id);
      showToast(`Deleted ${name}`, "success");
      loadEndpoints();
    } catch (err: any) {
      showToast(`Deletion failed: ${err.message}`, "error");
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Monitored Endpoints</h1>
          <p className="text-sm text-slate-400 mt-1">
            Configure periodic HTTP health checks, timeouts, and response assertions.
          </p>
        </div>

        <button
          onClick={() => {
            setErrorMessage(null);
            setModalOpen(true);
          }}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition-colors shadow-sm self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Add Monitored API</span>
        </button>
      </div>

      {/* Filter / Search Bar */}
      <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 px-4 py-2.5 rounded-xl">
        <Search className="w-4 h-4 text-slate-400 shrink-0" />
        <input
          type="text"
          placeholder="Filter endpoints by name or target URL..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-transparent border-none text-sm text-white placeholder-slate-500 focus:outline-none w-full"
        />
      </div>

      {/* Endpoints Table */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 flex items-center justify-center gap-3">
            <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />
            <span>Loading endpoints...</span>
          </div>
        ) : endpoints.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/60 text-slate-400 text-xs font-mono border-b border-slate-800/80">
                <tr>
                  <th className="px-6 py-3.5">Method & Service</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Interval</th>
                  <th className="px-4 py-3.5">24h Uptime</th>
                  <th className="px-4 py-3.5">Latest Latency</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {endpoints.map((ep) => (
                  <tr key={ep.id} className="hover:bg-slate-800/20 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-blue-400 border border-slate-700">
                          {ep.http_method}
                        </span>
                        <Link
                          to={`/endpoints/${ep.id}`}
                          className="font-medium text-slate-200 hover:text-blue-400 transition-colors"
                        >
                          {ep.name}
                        </Link>
                      </div>
                      <span className="block text-xs font-mono text-slate-500 mt-1 truncate max-w-sm">
                        {ep.url}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <StatusBadge status={ep.current_status} size="sm" />
                    </td>
                    <td className="px-4 py-4 font-mono text-xs text-slate-300">
                      {ep.monitoring_interval}s
                    </td>
                    <td className="px-4 py-4 font-mono text-xs text-slate-300">
                      {ep.uptime_percentage !== null && ep.uptime_percentage !== undefined
                        ? `${ep.uptime_percentage}%`
                        : "—"}
                    </td>
                    <td className="px-4 py-4 font-mono text-xs text-slate-300">
                      {ep.latest_response_time_ms ? `${ep.latest_response_time_ms} ms` : "—"}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleTriggerCheck(ep.id)}
                          title="Trigger Immediate Health Check"
                          className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-blue-600/20 hover:text-blue-400 text-slate-400 transition-colors"
                        >
                          <Send className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleToggleActive(ep)}
                          title={ep.is_active ? "Pause Monitoring" : "Resume Monitoring"}
                          className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-amber-600/20 hover:text-amber-400 text-slate-400 transition-colors"
                        >
                          {ep.is_active ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                        </button>
                        <Link
                          to={`/endpoints/${ep.id}`}
                          title="View Analytics & History"
                          className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </Link>
                        <button
                          onClick={() => handleDelete(ep.id, ep.name)}
                          title="Delete Monitored Endpoint"
                          className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-rose-600/20 hover:text-rose-400 text-slate-400 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-16 text-center text-slate-500">
            <Globe className="w-10 h-10 mx-auto text-slate-600 mb-3" />
            <h3 className="text-sm font-semibold text-slate-300">No endpoints found</h3>
            <p className="text-xs text-slate-500 mt-1">
              Add your web service, microservice, or public API to begin monitoring availability.
            </p>
          </div>
        )}
      </div>

      {/* Add Endpoint Modal */}
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Register Monitored Endpoint" maxWidth="lg">
        {errorMessage && (
          <div className="mb-4 p-3 rounded-lg bg-rose-950/40 border border-rose-800/50 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleCreate} className="space-y-4 text-sm">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Friendly Name</label>
            <input
              type="text"
              required
              placeholder="e.g., Stripe Webhook Receiver"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Target Endpoint URL</label>
            <input
              type="url"
              required
              placeholder="https://api.example.com/v1/health"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white font-mono text-sm focus:border-blue-500 focus:outline-none"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              SSRF Protected: Localhost and internal network addresses are rejected.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Method</label>
              <select
                value={formData.http_method}
                onChange={(e) => setFormData({ ...formData, http_method: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value="GET">GET</option>
                <option value="HEAD">HEAD</option>
                <option value="POST">POST</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Check Interval</label>
              <select
                value={formData.monitoring_interval}
                onChange={(e) => setFormData({ ...formData, monitoring_interval: Number(e.target.value) })}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value={30}>Every 30s</option>
                <option value={60}>Every 1 min</option>
                <option value={120}>Every 2 min</option>
                <option value={300}>Every 5 min</option>
                <option value={600}>Every 10 min</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Timeout (s)</label>
              <input
                type="number"
                min={1}
                max={30}
                value={formData.timeout}
                onChange={(e) => setFormData({ ...formData, timeout: Number(e.target.value) })}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Expected Status Codes</label>
              <input
                type="text"
                placeholder="200, 204"
                value={formData.expected_status_codes}
                onChange={(e) => setFormData({ ...formData, expected_status_codes: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white font-mono text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Latency Alert Threshold (ms)</label>
              <input
                type="number"
                placeholder="e.g. 1500 (optional)"
                value={formData.performance_threshold_ms}
                onChange={(e) => setFormData({ ...formData, performance_threshold_ms: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white font-mono text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Expected Content In Body (Optional)</label>
            <input
              type="text"
              placeholder="e.g., status: ok"
              value={formData.expected_content}
              onChange={(e) => setFormData({ ...formData, expected_content: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="px-4 py-2 text-xs font-medium rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 text-xs font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition-colors disabled:opacity-50"
            >
              {submitting ? "Registering..." : "Start Monitoring"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

