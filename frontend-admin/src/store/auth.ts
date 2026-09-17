import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthUser } from "@/types";
import { setTokens } from "@/api/client";

interface ImpersonationInfo {
  targetUser: AuthUser;
  adminUser: AuthUser;
  adminAccessToken: string;
}

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  impersonation: ImpersonationInfo | null;
  setSession: (user: AuthUser, access: string, refresh: string) => void;
  setUser: (user: AuthUser | null) => void;
  startImpersonation: (targetUser: AuthUser, targetAccess: string, adminAccess: string) => void;
  stopImpersonation: (adminUser: AuthUser, adminAccess: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      impersonation: null,
      setSession: (user, access, refresh) => {
        setTokens(access, refresh);
        set({ user, isAuthenticated: true });
      },
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      startImpersonation: (targetUser, targetAccess, adminAccess) => {
        const admin = get().user;
        if (!admin) return;
        // Keep the admin's refresh token; only the access token is swapped.
        setTokens(targetAccess);
        set({
          user: targetUser,
          impersonation: { targetUser, adminUser: admin, adminAccessToken: adminAccess },
        });
      },
      stopImpersonation: (adminUser, adminAccess) => {
        setTokens(adminAccess);
        set({ user: adminUser, impersonation: null });
      },
      logout: () => {
        setTokens(null, null);
        set({ user: null, isAuthenticated: false, impersonation: null });
      },
    }),
    {
      name: "sportx.admin.auth",
      partialize: (s) => ({ user: s.user, isAuthenticated: s.isAuthenticated, impersonation: s.impersonation }),
    },
  ),
);

window.addEventListener("sportx:logout", () => {
  useAuthStore.getState().logout();
});
