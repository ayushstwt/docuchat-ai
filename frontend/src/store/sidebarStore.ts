import { create } from "zustand";

interface SidebarState {
  isCollapsed: boolean;
  toggleSidebar: () => void;
  setCollapsed: (collapsed: boolean) => void;
}

const getInitialCollapsed = (): boolean => {
  if (typeof window === "undefined") return false;
  return localStorage.getItem("docuchat_sidebar_collapsed") === "true";
};

export const useSidebarStore = create<SidebarState>((set) => ({
  isCollapsed: getInitialCollapsed(),
  toggleSidebar: () =>
    set((state) => {
      const next = !state.isCollapsed;
      if (typeof window !== "undefined") {
        localStorage.setItem("docuchat_sidebar_collapsed", String(next));
      }
      return { isCollapsed: next };
    }),
  setCollapsed: (collapsed: boolean) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("docuchat_sidebar_collapsed", String(collapsed));
    }
    set({ isCollapsed: collapsed });
  },
}));
