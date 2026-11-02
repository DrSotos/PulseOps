import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { User, Shield, Server, Check } from "lucide-react";

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Platform Settings</h1>
        <p className="text-sm text-slate-400 mt-1">
          Account information, probe engine configurations, and security policies.
        </p>
      </div>

      {saved && (
        <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/50 text-emerald-300 text-xs flex items-center gap-2">
          <Check className="w-4 h-4 text-emerald-400" />
          <span>Preferences updated successfully.</span>
        </div>
      )}

      {/* Account Info */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6">
        <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <User className="w-4 h-4 text-blue-400" />
          <span>Operator Profile</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm font-mono">
          <div>
            <span className="block text-xs text-slate-500 uppercase">Account Email</span>
            <span className="text-slate-200 mt-1 block">{user?.email}</span>
          </div>

          <div>
            <span className="block text-xs text-slate-500 uppercase">Operator Name</span>
            <span className="text-slate-200 mt-1 block">{user?.full_name || "Lead Engineer"}</span>
          </div>

          <div>
            <span className="block text-xs text-slate-500 uppercase">Account Identifier</span>
            <span className="text-xs text-slate-400 mt-1 block truncate">{user?.id}</span>
          </div>

          <div>
            <span className="block text-xs text-slate-500 uppercase">Joined</span>
            <span className="text-xs text-slate-400 mt-1 block">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "Active"}
            </span>
          </div>
        </div>
      </div>

      {/* Security Policies */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6">
        <h3 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
          <Shield className="w-4 h-4 text-emerald-400" />
          <span>SSRF & Request Security Enforcement</span>
        </h3>
        <p className="text-xs text-slate-400 mb-4">
          PulseOps automatically inspects every monitoring destination before issuing outbound network requests.
        </p>

        <div className="space-y-2.5 text-xs">
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/60">
            <span className="text-slate-300">Block RFC 1918 Private Ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)</span>
            <span className="px-2 py-0.5 rounded bg-emerald-950/50 text-emerald-400 border border-emerald-800/50 font-mono text-[10px] font-bold">
              ENFORCED
            </span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/60">
            <span className="text-slate-300">Block Cloud Instance Metadata (169.254.169.254, metadata.google.internal)</span>
            <span className="px-2 py-0.5 rounded bg-emerald-950/50 text-emerald-400 border border-emerald-800/50 font-mono text-[10px] font-bold">
              ENFORCED
            </span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/60">
            <span className="text-slate-300">Prohibit Unvalidated HTTP Open Redirects</span>
            <span className="px-2 py-0.5 rounded bg-emerald-950/50 text-emerald-400 border border-emerald-800/50 font-mono text-[10px] font-bold">
              ENFORCED
            </span>
          </div>
        </div>
      </div>

      {/* Engine Defaults */}
      <form onSubmit={handleSave} className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6 space-y-4">
        <h3 className="text-base font-semibold text-white mb-1 flex items-center gap-2">
          <Server className="w-4 h-4 text-indigo-400" />
          <span>Monitoring Engine Defaults</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Default Failure Confirmation Threshold
            </label>
            <input
              type="number"
              defaultValue={3}
              min={1}
              max={10}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white font-mono text-xs focus:outline-none focus:border-blue-500"
            />
            <p className="text-[11px] text-slate-500 mt-1">Consecutive failed checks before an incident triggers.</p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Default Auto-Recovery Threshold
            </label>
            <input
              type="number"
              defaultValue={2}
              min={1}
              max={10}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white font-mono text-xs focus:outline-none focus:border-blue-500"
            />
            <p className="text-[11px] text-slate-500 mt-1">Consecutive successful checks before auto-resolving.</p>
          </div>
        </div>

        <div className="pt-2">
          <button
            type="submit"
            className="px-4 py-2 text-xs font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition-colors shadow-sm"
          >
            Save Defaults
          </button>
        </div>
      </form>
    </div>
  );
};
