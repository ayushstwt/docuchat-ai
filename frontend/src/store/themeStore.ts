import { create } from "zustand";

export type Theme = "light" | "dark";

interface ThemeState {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const getInitialTheme = (): Theme => {
  if (typeof window === "undefined") return "light";
  const saved = localStorage.getItem("docuchat_theme") as Theme | null;
  if (saved === "light" || saved === "dark") {
    return saved;
  }
  if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "light";
};

const applyThemeToDocument = (theme: Theme) => {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  if (theme === "dark") {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
  localStorage.setItem("docuchat_theme", theme);
};

// Apply theme immediately on script load
if (typeof window !== "undefined") {
  const initial = getInitialTheme();
  applyThemeToDocument(initial);
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: typeof window !== "undefined" ? getInitialTheme() : "light",
  toggleTheme: () =>
    set((state) => {
      const nextTheme = state.theme === "light" ? "dark" : "light";
      applyThemeToDocument(nextTheme);
      return { theme: nextTheme };
    }),
  setTheme: (theme: Theme) => {
    applyThemeToDocument(theme);
    set({ theme });
  },
}));
