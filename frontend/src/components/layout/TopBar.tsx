import React from "react";
import { Moon, Sun, PanelLeft } from "lucide-react";
import { useThemeStore } from "../../store/themeStore";
import { useAuthStore } from "../../store/authStore";
import { useSidebarStore } from "../../store/sidebarStore";

export const TopBar: React.FC = () => {
  const { theme, toggleTheme } = useThemeStore();
  const { user } = useAuthStore();
  const { toggleSidebar, isCollapsed } = useSidebarStore();

  return (
    <header className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 transition-colors">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={toggleSidebar}
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="p-1.5 rounded-lg text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          <PanelLeft className="w-4 h-4" />
        </button>
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          RAG Pipeline Active
        </span>
      </div>

      <div className="flex items-center gap-3">
        {/* Dark Mode Toggle */}
        <button
          type="button"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 bg-slate-100/70 hover:bg-slate-200/70 dark:bg-slate-800 dark:hover:bg-slate-700 transition-colors cursor-pointer"
          title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
        >
          {theme === "light" ? (
            <Moon className="w-4 h-4 text-slate-700 dark:text-slate-300" />
          ) : (
            <Sun className="w-4 h-4 text-amber-400" />
          )}
        </button>

        {/* User Badge */}
        {user && (
          <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-slate-200 dark:border-slate-800 text-xs">
            <span className="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-primary font-bold flex items-center justify-center text-[10px]">
              {user.fullName ? user.fullName.charAt(0).toUpperCase() : "U"}
            </span>
            <span className="font-medium text-slate-700 dark:text-slate-300 truncate max-w-[120px]">
              {user.fullName || user.email}
            </span>
          </div>
        )}
      </div>
    </header>
  );
};
