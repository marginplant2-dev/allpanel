import { httpClient, unwrap } from "./client";
import type { AuditLog, ManagedUser, Paginated, Role } from "@/types";

export interface UserListParams {
  page?: number;
  page_size?: number;
  search?: string;
  role?: Role;
  status?: string;
  sort_by?: string;
  order?: "asc" | "desc";
}

export interface CreateUserPayload {
  username: string;
  password: string;
  full_name: string;
  role: Role;
  parent_id?: string | null;
  status?: string;
  credit_limit?: number;
  notes?: string | null;
}

export interface UpdateUserPayload {
  full_name?: string;
  password?: string;
  credit_limit?: number;
  notes?: string | null;
  status?: string;
}

export function fetchUsers(params: UserListParams = {}) {
  return unwrap<Paginated<ManagedUser>>(httpClient.get("/users", { params }));
}

export function fetchUser(id: string) {
  return unwrap<ManagedUser>(httpClient.get(`/users/${id}`));
}

export function createUser(payload: CreateUserPayload) {
  return unwrap<ManagedUser>(httpClient.post("/users", payload));
}

export function updateUser(id: string, payload: UpdateUserPayload) {
  return unwrap<ManagedUser>(httpClient.patch(`/users/${id}`, payload));
}

export function suspendUser(id: string) {
  return unwrap<ManagedUser>(httpClient.post(`/users/${id}/suspend`));
}

export function activateUser(id: string) {
  return unwrap<ManagedUser>(httpClient.post(`/users/${id}/activate`));
}

export function fetchUserActivity(id: string, params: { page?: number; page_size?: number } = {}) {
  return unwrap<Paginated<AuditLog>>(httpClient.get(`/users/${id}/activity`, { params }));
}
