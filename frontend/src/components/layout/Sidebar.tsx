import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  FileText,
  MessageSquarePlus,
  History,
  LogOut,
  Bot,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { useSidebarStore } from "../../store/sidebarStore";

export const Sidebar: React.FC = () => {
  const { user, clearAuth } = useAuthStore();
  const { isCollapsed, toggleSidebar } = useSidebarStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    clearAuth();
    navigate("/login");
  };

  const navLinks = [
    {
      to: "/documents",
      label: "Documents",
      icon: <FileText className="w-5 h-5 shrink-0" />,
    },
    {
      to: "/chat",
      label: "Chat & RAG",
      icon: <MessageSquarePlus className="w-5 h-5 shrink-0" />,
    },
    {
      to: "/activity",
      label: "Activity Logs",
      icon: <History className="w-5 h-5 shrink-0" />,
    },
  ];

  return (
    <aside
      className={`${
        isCollapsed ? "w-20" : "w-64"
      } bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between shrink-0 h-screen sticky top-0 transition-all duration-300 ease-in-out z-20`}
    >
      {/* Top Brand Header */}
      <div className="flex flex-col">
        <div
          className={`h-16 flex items-center border-b border-slate-100 dark:border-slate-800 ${
            isCollapsed ? "justify-center px-2" : "justify-between px-4"
          }`}
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center text-white shadow-sm shadow-primary/25 shrink-0">
              <Bot className="w-5 h-5" />
            </div>
            {!isCollapsed && (
              <div className="flex flex-col min-w-0">
                <span className="font-semibold text-sm text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-1.5">
                  DocuChat AI
                  <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.2 rounded bg-indigo-50 dark:bg-indigo-950/60 text-primary dark:text-indigo-400 border border-indigo-100 dark:border-indigo-900">
                    v2.4
                  </span>
                </span>
                <span className="text-xs text-slate-400 dark:text-slate-500 font-mono truncate">
                  Enterprise RAG
                </span>
              </div>
            )}
          </div>

          {/* Collapse / Expand Toggle Button */}
          <button
            onClick={toggleSidebar}
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            className={`p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors ${
              isCollapsed ? "mt-2" : ""
            }`}
          >
            {isCollapsed ? (
              <PanelLeftOpen className="w-4 h-4" />
            ) : (
              <PanelLeftClose className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Navigation Section */}
        <nav className={`p-3 space-y-1.5 ${isCollapsed ? "flex flex-col items-center" : ""}`}>
          {!isCollapsed && (
            <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              Workspace
            </div>
          )}
          {navLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              title={isCollapsed ? link.label : undefined}
              className={({ isActive }) =>
                `flex items-center rounded-lg transition-colors group relative ${
                  isCollapsed
                    ? "w-11 h-11 justify-center"
                    : "gap-3 px-3 py-2.5 text-sm font-medium w-full"
                } ${
                  isActive
                    ? "bg-primary text-white shadow-xs"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100"
                }`
              }
            >
              {link.icon}
              {!isCollapsed && <span>{link.label}</span>}

              {/* Floating tooltip when collapsed */}
              {isCollapsed && (
                <span className="absolute left-full ml-3 px-2 py-1 bg-slate-900 dark:bg-slate-800 text-white text-xs font-medium rounded-md shadow-lg opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50 whitespace-nowrap">
                  {link.label}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Footer / User Profile */}
      <div
        className={`p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/60 ${
          isCollapsed ? "flex flex-col items-center gap-3" : ""
        }`}
      >
        <div
          className={`flex items-center ${
            isCollapsed ? "flex-col gap-2.5" : "justify-between"
          }`}
        >
          <div
            className={`flex items-center gap-2.5 min-w-0 ${
              isCollapsed ? "justify-center" : ""
            }`}
            title={isCollapsed ? `${user?.fullName} (${user?.email})` : undefined}
          >
            <div className="w-9 h-9 rounded-full bg-indigo-100 dark:bg-indigo-950/80 text-primary dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 flex items-center justify-center text-xs font-bold shrink-0">
              {user?.fullName ? user.fullName.charAt(0).toUpperCase() : "U"}
            </div>
            {!isCollapsed && (
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-semibold text-slate-900 dark:text-slate-200 truncate">
                  {user?.fullName || "DocuChat User"}
                </span>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                  {user?.email || "user@docuchat.ai"}
                </span>
              </div>
            )}
          </div>

          <button
            onClick={handleLogout}
            title="Sign out"
            className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};

