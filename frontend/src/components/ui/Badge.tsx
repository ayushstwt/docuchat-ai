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
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 border border-slate-200 text-slate-600 ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
          Uploaded
        </span>
      );
    case "PROCESSING":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 border border-blue-200 text-blue-700 ${className}`}
        >
          <Loader2 className="w-3 h-3 animate-spin text-blue-600" />
          Processing
        </span>
      );
    case "READY":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 border border-emerald-200 text-emerald-700 ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          Ready
        </span>
      );
    case "FAILED":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 border border-rose-200 text-rose-700 ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
          Failed
        </span>
      );
    default:
      return (
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 border border-slate-200 text-slate-700 ${className}`}
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
  neutral: "bg-slate-100 border-slate-200 text-slate-700",
  primary: "bg-indigo-50 border-indigo-200 text-indigo-700",
  success: "bg-emerald-50 border-emerald-200 text-emerald-700",
  warning: "bg-amber-50 border-amber-200 text-amber-700",
  error: "bg-rose-50 border-rose-200 text-rose-700",
  info: "bg-blue-50 border-blue-200 text-blue-700",
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
