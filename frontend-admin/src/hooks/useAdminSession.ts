import { useEffect } from "react";
import { getMe } from "@/api/auth";
import { getAccessToken } from "@/api/client";
import { useAuthStore } from "@/store/auth";

/** Re-hydrate the admin session from the backend when a token is present. */
export function useAdminSession() {
  const setUser = useAuthStore((s) => s.setUser);
  const logout = useAuthStore((s) => s.logout);
  const impersonating = useAuthStore((s) => !!s.impersonation);

  useEffect(() => {
    if (!getAccessToken() || impersonating) return;
    let active = true;
    getMe()
      .then((user) => active && setUser(user))
      .catch(() => active && logout());
    return () => {
      active = false;
    };
  }, [setUser, logout, impersonating]);
}
