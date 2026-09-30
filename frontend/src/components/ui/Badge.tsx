import React from "react";
import { Loader2 } from "lucide-react";
import { DocumentStatus } from "../../api/types";

export interface StatusBadgeProps {
  status: DocumentStatus | string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = "" }) => {
  switch (status) {
    case "UPLOADED":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500"></span>
          Uploaded
        </span>
      );
    case "PROCESSING":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300 ${className}`}
        >
          <Loader2 className="w-3 h-3 animate-spin text-blue-600 dark:text-blue-400" />
          Processing
        </span>
      );
    case "READY":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          Ready
        </span>
      );
    case "FAILED":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
          Failed
        </span>
      );
    default:
      return (
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 ${className}`}
        >
          {status}
        </span>
      );
  }
};

export interface BadgeProps {
  children: React.ReactNode;
  variant?: "neutral" | "primary" | "success" | "warning" | "error" | "info";
  className?: string;
}

const variantMap: Record<string, string> = {
  neutral: "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300",
  primary: "bg-indigo-50 dark:bg-indigo-950/50 border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300",
  success: "bg-emerald-50 dark:bg-emerald-950/50 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300",
  warning: "bg-amber-50 dark:bg-amber-950/50 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300",
  error: "bg-rose-50 dark:bg-rose-950/50 border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300",
  info: "bg-blue-50 dark:bg-blue-950/50 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300",
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "neutral",
  className = "",
}) => {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variantMap[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
