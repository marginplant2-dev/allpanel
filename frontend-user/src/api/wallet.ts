import { httpClient, unwrap } from "./client";
import type { Paginated, Wallet } from "@/types";

export interface Transaction {
  transaction_id: string;
  from_user_id: string | null;
  to_user_id: string | null;
  amount: number;
  transaction_type: string;
  status: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface TransactionQuery {
  page?: number;
  page_size?: number;
  direction?: "in" | "out";
  transaction_type?: string;
}

export function fetchWallet() {
  return unwrap<Wallet>(httpClient.get("/wallet"));
}

export function fetchTransactions(query: TransactionQuery = {}) {
  return unwrap<Paginated<Transaction>>(httpClient.get("/wallet/transactions", { params: query }));
}

export interface ActivityItem {
  id: string;
  actor_id: string | null;
  action: string;
  target_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}
