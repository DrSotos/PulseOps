import React from "react";
import { NavLink } from "react-router-dom";
import {
  Activity,
  Globe,
  AlertOctagon,
  Bell,
  Settings,
  ShieldCheck,
} from "lucide-react";

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: "/", label: "Dashboard", icon: Activity },
    { to: "/endpoints", label: "Monitored APIs", icon: Globe },
    { to: "/incidents", label: "Incidents", icon: AlertOctagon },
    { to: "/notifications", label: "Alerts & Channels", icon: Bell },
    { to: "/settings", label: "Settings", icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800/80 flex flex-col justify-between shrink-0 select-none">
      <div>
        {/* Brand */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800/80 gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Activity className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <span className="font-bold tracking-tight text-white text-base">PulseOps</span>
            <span className="block text-[10px] text-slate-500 font-mono tracking-widest uppercase">
              SRE Platform
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-blue-600/15 text-blue-400 border border-blue-500/20 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800/80">
        <div className="flex items-center gap-2 px-2 py-1.5 rounded-md bg-slate-900/50 border border-slate-800 text-[11px] text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>SSRF Shield Active</span>
        </div>
      </div>
    </aside>
  );
};

