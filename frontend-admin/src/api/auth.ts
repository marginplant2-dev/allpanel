import { httpClient, unwrap } from "./client";
import type { AuthTokens, AuthUser } from "@/types";

export function login(payload: { username: string; password: string }) {
  return unwrap<AuthTokens>(httpClient.post("/auth/login", payload));
}

export function getMe() {
  return unwrap<AuthUser>(httpClient.get("/auth/me"));
}

export function logout(refreshToken: string) {
  return unwrap<null>(httpClient.post("/auth/logout", { refresh_token: refreshToken }));
}
