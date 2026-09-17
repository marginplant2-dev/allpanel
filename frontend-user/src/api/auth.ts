import { httpClient, unwrap } from "./client";
import type { AuthTokens, AuthUser } from "@/types";

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  password: string;
  full_name: string;
}

export function login(payload: LoginPayload) {
  return unwrap<AuthTokens>(httpClient.post("/auth/login", payload));
}

export function register(payload: RegisterPayload) {
  return unwrap<AuthTokens>(httpClient.post("/auth/register", payload));
}

export function getMe() {
  return unwrap<AuthUser>(httpClient.get("/auth/me"));
}

export function logout(refreshToken: string) {
  return unwrap<null>(httpClient.post("/auth/logout", { refresh_token: refreshToken }));
}
