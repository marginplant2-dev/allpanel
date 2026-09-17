import { httpClient, unwrap } from "./client";
import type { Paginated } from "@/types";

export type CreditRequestType = "DEPOSIT" | "WITHDRAW";
export type CreditRequestStatus = "PENDING" | "PROCESSING" | "APPROVED" | "REJECTED";

export interface CreditRequest {
  id: string;
  user_id: string;
  username: string;
  parent_id: string;
  type: CreditRequestType;
  amount: number;
  status: CreditRequestStatus;
  note: string | null;
  decision_note: string | null;
  transaction_id: string | null;
  created_at: string;
  decided_at: string | null;
}

export function createCreditRequest(payload: { type: CreditRequestType; amount: number; note?: string }) {
  return unwrap<CreditRequest>(httpClient.post("/credit-requests", payload));
}

export function fetchMyCreditRequests(query: { page?: number; page_size?: number } = {}) {
  return unwrap<Paginated<CreditRequest>>(httpClient.get("/credit-requests/mine", { params: query }));
}
