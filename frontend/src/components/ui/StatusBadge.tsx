import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, PauseCircle, HelpCircle } from "lucide-react";

interface StatusBadgeProps {
  status: "operational" | "degraded" | "down" | "paused" | "unknown" | string;
  size?: "sm" | "md";
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = "md",
  showIcon = true,
}) => {
  const norm = status.toLowerCase();

  const configs: Record<string, { label: string; bg: string; text: string; border: string; icon: any; dot?: string }> = {
    operational: {
      label: "Operational",
      bg: "bg-emerald-950/40",
      text: "text-emerald-400",
      border: "border-emerald-800/50",
      icon: CheckCircle2,
      dot: "bg-emerald-400",
    },
    degraded: {
      label: "Degraded",
      bg: "bg-amber-950/40",
      text: "text-amber-400",
      border: "border-amber-800/50",
      icon: AlertTriangle,
      dot: "bg-amber-400",
    },
    down: {
      label: "Outage",
      bg: "bg-rose-950/50",
      text: "text-rose-400",
      border: "border-rose-800/60",
      icon: XCircle,
      dot: "bg-rose-500",
    },
    paused: {
      label: "Paused",
      bg: "bg-slate-900/60",
      text: "text-slate-400",
      border: "border-slate-800",
      icon: PauseCircle,
    },
    unknown: {
      label: "Pending",
      bg: "bg-slate-900/40",
      text: "text-slate-500",
      border: "border-slate-800",
      icon: HelpCircle,
    },
  };

  const cfg = configs[norm] || configs.unknown;
  const Icon = cfg.icon;

  const sizeClasses =
    size === "sm" ? "text-[11px] px-2 py-0.5 gap-1.5" : "text-xs px-2.5 py-1 gap-1.5 font-medium";

  return (
    <span
      className={`inline-flex items-center rounded-full border shadow-sm ${cfg.bg} ${cfg.text} ${cfg.border} ${sizeClasses} backdrop-blur-sm transition-colors`}
    >
      {showIcon && (
        <span className="relative flex items-center justify-center">
          <Icon className={size === "sm" ? "w-3 h-3" : "w-3.5 h-3.5"} />
        </span>
      )}
      <span>{cfg.label}</span>
    </span>
  );
};

