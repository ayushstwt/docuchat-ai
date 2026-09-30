import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  FileText,
  MessageSquarePlus,
  History,
  LogOut,
  Bot,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";

export const Sidebar: React.FC = () => {
  const { user, clearAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    clearAuth();
    navigate("/login");
  };

  const navLinks = [
    {
      to: "/documents",
      label: "Documents",
      icon: <FileText className="w-4 h-4 shrink-0" />,
    },
    {
      to: "/chat",
      label: "Chat & RAG",
      icon: <MessageSquarePlus className="w-4 h-4 shrink-0" />,
    },
    {
      to: "/activity",
      label: "Activity Logs",
      icon: <History className="w-4 h-4 shrink-0" />,
    },
  ];

  return (
    <aside className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between shrink-0 h-screen sticky top-0 transition-colors">
      {/* Top Brand Header */}
      <div className="flex flex-col">
        <div className="h-16 flex items-center gap-3 px-5 border-b border-slate-100 dark:border-slate-850">
          <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center text-white shadow-sm shadow-primary/25">
            <Bot className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-sm text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-1.5">
              DocuChat AI
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.2 rounded bg-indigo-50 dark:bg-indigo-950/60 text-primary dark:text-indigo-400 border border-indigo-100 dark:border-indigo-900">
                v2.4
              </span>
            </span>
            <span className="text-xs text-slate-400 dark:text-slate-500 font-mono">Enterprise RAG</span>
          </div>
        </div>

        {/* Navigation Section */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            Workspace
          </div>
          {navLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary text-white shadow-xs"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100"
                }`
              }
            >
              {link.icon}
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Footer / User Profile */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 flex items-center justify-center text-xs font-semibold shrink-0">
              {user?.fullName ? user.fullName.charAt(0).toUpperCase() : "U"}
            </div>
            <div className="flex flex-col min-w-0">
              <span className="text-xs font-semibold text-slate-900 dark:text-slate-200 truncate">
                {user?.fullName || "DocuChat User"}
              </span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                {user?.email || "user@docuchat.ai"}
              </span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            title="Sign out"
            className="p-1.5 text-slate-400 hover:text-error hover:bg-red-50 dark:hover:bg-rose-950/40 rounded-md transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
