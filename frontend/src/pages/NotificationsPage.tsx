import React, { useEffect, useState, useCallback } from "react";
import {
  Bell,
  Plus,
  Mail,
  Webhook,
  Send,
  Trash2,
  AlertCircle,
} from "lucide-react";
import { api } from "../services/api";
import { NotificationChannel, NotificationDelivery } from "../types";
import { Modal } from "../components/ui/Modal";
import { useToast } from "../contexts/ToastContext";

export const NotificationsPage: React.FC = () => {
  const { showToast } = useToast();
  const [channels, setChannels] = useState<NotificationChannel[]>([]);
  const [history, setHistory] = useState<NotificationDelivery[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: "",
    channel_type: "email",
    destination: "",
  });

  const loadData = useCallback(async () => {
    try {
      const [ch, hist] = await Promise.all([
        api.listChannels(),
        api.getNotificationHistory(1, 20),
      ]);
      setChannels(ch);
      setHistory(hist.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);
    try {
      await api.createChannel({
        name: form.name,
        channel_type: form.channel_type as any,
        destination: form.destination,
        is_enabled: true,
      });
      setModalOpen(false);
      setForm({ name: "", channel_type: "email", destination: "" });
      showToast("Notification channel created", "success");
      loadData();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to create channel.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleTest = async (id: string) => {
    setTestingId(id);
    try {
      const res = await api.testChannel(id);
      showToast(res.message, "success");
    } catch (err: any) {
      showToast(`Test failed: ${err.message}`, "error");
    } finally {
      setTestingId(null);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Delete channel "${name}"?`)) return;
    try {
      await api.deleteChannel(id);
      showToast(`Deleted channel "${name}"`, "success");
      loadData();
    } catch (err: any) {
      showToast(err.message, "error");
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Alert Channels & Deliveries</h1>
          <p className="text-sm text-slate-400 mt-1">
            Configure SMTP email alerts and custom webhook dispatch destinations for incident notices.
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
          <span>Add Channel</span>
        </button>
      </div>

      {/* Channels Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {channels.map((ch) => (
          <div
            key={ch.id}
            className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono uppercase bg-slate-800 text-slate-300">
                  {ch.channel_type === "email" ? (
                    <Mail className="w-3 h-3 text-blue-400" />
                  ) : (
                    <Webhook className="w-3 h-3 text-indigo-400" />
                  )}
                  <span>{ch.channel_type}</span>
                </span>
                <span
                  className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded ${
                    ch.is_enabled ? "text-emerald-400 bg-emerald-950/40" : "text-slate-500 bg-slate-800"
                  }`}
                >
                  {ch.is_enabled ? "Active" : "Disabled"}
                </span>
              </div>
              <h3 className="font-semibold text-white text-base">{ch.name}</h3>
              <p className="text-xs font-mono text-slate-400 mt-1 truncate">{ch.destination}</p>
            </div>

            <div className="flex items-center justify-between pt-4 mt-4 border-t border-slate-800/60">
              <button
                onClick={() => handleTest(ch.id)}
                disabled={testingId === ch.id}
                className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 font-medium disabled:opacity-50"
              >
                <Send className={`w-3.5 h-3.5 ${testingId === ch.id ? "animate-spin" : ""}`} />
                <span>Test Dispatch</span>
              </button>
              <button
                onClick={() => handleDelete(ch.id, ch.name)}
                className="p-1.5 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
        {channels.length === 0 && !loading && (
          <div className="col-span-full p-12 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
            <Bell className="w-8 h-8 mx-auto text-slate-600 mb-2" />
            <p className="text-sm">No notification channels registered.</p>
            <p className="text-xs text-slate-600 mt-1">
              Add your email or webhook endpoint to get pinged on service degradation.
            </p>
          </div>
        )}
      </div>

      {/* Delivery Audit History */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800/80">
          <h2 className="text-base font-semibold text-white">Delivery Log History</h2>
        </div>
        {history.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800/80">
                <tr>
                  <th className="px-6 py-3.5">Channel Name</th>
                  <th className="px-4 py-3.5">Type</th>
                  <th className="px-4 py-3.5">Event</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Attempts</th>
                  <th className="px-6 py-3.5">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {history.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/20">
                    <td className="px-6 py-3.5 font-sans font-medium text-slate-200">
                      {item.channel_name || "Channel"}
                    </td>
                    <td className="px-4 py-3.5 text-slate-400 uppercase">{item.channel_type}</td>
                    <td className="px-4 py-3.5 text-slate-300">{item.event_type}</td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                          item.delivery_status === "delivered"
                            ? "text-emerald-400 bg-emerald-950/40"
                            : "text-rose-400 bg-rose-950/40"
                        }`}
                      >
                        {item.delivery_status}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-slate-400">{item.attempts}</td>
                    <td className="px-6 py-3.5 text-slate-500 font-sans">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-slate-500 text-xs">No delivery attempts recorded yet.</div>
        )}
      </div>

      {/* Channel Creation Modal */}
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Add Alert Channel">
        {errorMessage && (
          <div className="mb-4 p-3 rounded-lg bg-rose-950/40 border border-rose-800/50 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleCreate} className="space-y-4 text-sm">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Channel Label</label>
            <input
              type="text"
              required
              placeholder="e.g. SRE Escalation Email"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Channel Protocol</label>
            <select
              value={form.channel_type}
              onChange={(e) => setForm({ ...form, channel_type: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="email">Email (SMTP)</option>
              <option value="webhook">Webhook (HTTP POST)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              {form.channel_type === "email" ? "Recipient Email Address" : "Webhook URL"}
            </label>
            <input
              type={form.channel_type === "email" ? "email" : "url"}
              required
              placeholder={form.channel_type === "email" ? "alerts@company.com" : "https://hooks.slack.com/services/..."}
              value={form.destination}
              onChange={(e) => setForm({ ...form, destination: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white font-mono text-sm focus:border-blue-500 focus:outline-none"
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
              {submitting ? "Saving..." : "Save Channel"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
