import React from "react";
import { useAuth } from "../../contexts/AuthContext";
import { LogOut, User as UserIcon } from "lucide-react";

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 bg-slate-950/70 backdrop-blur-md border-b border-slate-800/80 px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Left status indicator */}
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/50 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-medium shadow-sm shadow-emerald-950/40">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span>LIVE ENGINE</span>
        </span>
      </div>

      {/* Right User menu */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5 text-sm text-slate-300">
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
            <UserIcon className="w-4 h-4" />
          </div>
          <div className="hidden sm:block text-left">
            <span className="block text-xs font-medium text-slate-200">
              {user?.full_name || user?.email.split("@")[0]}
            </span>
            <span className="block text-[11px] text-slate-500 font-mono">{user?.email}</span>
          </div>
        </div>

        <button
          onClick={logout}
          title="Sign out"
          className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-900 rounded-lg transition-colors border border-transparent hover:border-slate-800"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
