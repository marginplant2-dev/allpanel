import { httpClient, unwrap } from "./client";
import type {
  AuditLog,
  CreditRequest,
  DashboardStats,
  Game,
  Paginated,
  Transaction,
  TreeNode,
} from "@/types";

// --- Reports ---
export function fetchDashboard() {
  return unwrap<DashboardStats>(httpClient.get("/reports/dashboard"));
}

export function fetchUserGrowth(days = 14) {
  return unwrap<{ date: string; users: number }[]>(
    httpClient.get("/reports/user-growth", { params: { days } }),
  );
}

export function fetchCreditMovement(days = 14) {
  return unwrap<{ date: string; amount: number }[]>(
    httpClient.get("/reports/credit-movement", { params: { days } }),
  );
}

// --- Hierarchy ---
export function fetchTree() {
  return unwrap<{ nodes: number; root?: TreeNode; roots?: TreeNode[] }>(
    httpClient.get("/hierarchy/tree"),
  );
}

// --- Credits ---
export interface TransferPayload {
  to_user_id: string;
  amount: number;
  note?: string;
  idempotency_key?: string;
}

export function transferCredits(payload: TransferPayload) {
  return unwrap<Transaction>(
    httpClient.post("/credits/transfer", payload, {
      headers: payload.idempotency_key ? { "Idempotency-Key": payload.idempotency_key } : undefined,
    }),
  );
}

export function fetchLedger(params: { page?: number; page_size?: number } = {}) {
  return unwrap<Paginated<Transaction>>(httpClient.get("/credits/ledger", { params }));
}

export function fetchCreditRequests(params: { page?: number; page_size?: number; status?: string } = {}) {
  return unwrap<Paginated<CreditRequest>>(httpClient.get("/credit-requests/inbox", { params }));
}

export function decideCreditRequest(id: string, action: "approve" | "reject", note?: string) {
  return unwrap<CreditRequest>(httpClient.post(`/credit-requests/${id}/${action}`, { note: note || undefined }));
}

// --- Audit ---
export function fetchAuditLogs(params: { page?: number; page_size?: number; action?: string } = {}) {
  return unwrap<Paginated<AuditLog>>(httpClient.get("/audit", { params }));
}

// --- Games (admin) ---
export interface GamePayload {
  name: string;
  slug: string;
  provider: string;
  category: string;
  thumbnail_url: string;
  banner_url?: string;
  status?: string;
  featured?: boolean;
  sort_order?: number;
  tags?: string[];
}

export function fetchGamesAdmin(params: { page?: number; page_size?: number; category?: string; status?: string; search?: string } = {}) {
  return unwrap<Paginated<Game>>(httpClient.get("/games/admin/list", { params }));
}

export function createGame(payload: GamePayload) {
  return unwrap<Game>(httpClient.post("/games", payload));
}

export function updateGame(id: string, payload: Partial<GamePayload>) {
  return unwrap<Game>(httpClient.patch(`/games/${id}`, payload));
}

export function deleteGame(id: string) {
  return unwrap<null>(httpClient.delete(`/games/${id}`));
}

export function fetchGameCategories() {
  return unwrap<{ id: string; key: string; name: string }[]>(httpClient.get("/games/categories"));
}

// --- Impersonation ---
export function startImpersonation(targetId: string) {
  return unwrap<{ access_token: string; user: import("@/types").AuthUser; impersonator_id: string }>(
    httpClient.post("/impersonation/start", { target_id: targetId }),
  );
}

export function endImpersonation() {
  return unwrap<{ access_token: string; user: import("@/types").AuthUser }>(
    httpClient.post("/impersonation/end"),
  );
}

export interface MyWallet {
  user_id: string;
  available_balance: number;
  locked_balance: number;
  updated_at: string;
}

/** Coins this account holds — what it can hand down to the level below. */
export function fetchMyWallet() {
  return unwrap<MyWallet>(httpClient.get("/wallet"));
}
