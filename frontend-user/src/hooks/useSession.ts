import { useEffect } from "react";
import { getMe } from "@/api/auth";
import { getAccessToken } from "@/api/client";
import { useAuthStore } from "@/store/auth";

/** Hydrate the auth store from the backend when an access token is present. */
export function useSessionHydration() {
  const setUser = useAuthStore((s) => s.setUser);
  const logout = useAuthStore((s) => s.logout);

  useEffect(() => {
    if (!getAccessToken()) return;
    let active = true;
    getMe()
      .then((user) => {
        if (active) setUser(user);
      })
      .catch(() => {
        if (active) logout();
      });
    return () => {
      active = false;
    };
  }, [setUser, logout]);
}
