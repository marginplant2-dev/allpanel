import { create } from "zustand";
import { persist } from "zustand/middleware";

type Theme = "dark" | "light";

interface ThemeState {
  theme: Theme;
  toggle: () => void;
}

function apply(theme: Theme) {
  // index.html ships class="dark"; both classes are toggled so Tailwind's dark:
  // variants and the .light CSS variables never disagree.
  const root = document.documentElement;
  root.classList.toggle("light", theme === "light");
  root.classList.toggle("dark", theme === "dark");
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: "dark",
      toggle: () => {
        const next = get().theme === "dark" ? "light" : "dark";
        apply(next);
        set({ theme: next });
      },
    }),
    {
      name: "sportx.admin.theme",
      onRehydrateStorage: () => (state) => apply(state?.theme ?? "dark"),
    },
  ),
);

apply(useThemeStore.getState().theme);
