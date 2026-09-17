import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthUser } from "@/types";
import { setTokens } from "@/api/client";

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  setSession: (user: AuthUser, access: string, refresh: string) => void;
  setUser: (user: AuthUser | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setSession: (user, access, refresh) => {
        setTokens(access, refresh);
        set({ user, isAuthenticated: true });
      },
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      logout: () => {
        setTokens(null, null);
        set({ user: null, isAuthenticated: false });
      },
    }),
    { name: "sportx.auth", partialize: (s) => ({ user: s.user, isAuthenticated: s.isAuthenticated }) },
  ),
);

// Force logout when the API client signals an unrecoverable auth failure.
window.addEventListener("sportx:logout", () => {
  useAuthStore.getState().logout();
});
