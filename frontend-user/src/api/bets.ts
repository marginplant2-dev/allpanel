import { httpClient, unwrap } from "./client";
import type { Bet, BetStatus, Paginated } from "@/types";

export function placeBet(payload: {
  event_id: string;
  bookmaker_key: string;
  outcome_name: string;
  stake: number;
}) {
  return unwrap<Bet>(httpClient.post("/bets", payload));
}

export function fetchMyBets(query: { page?: number; page_size?: number; status?: BetStatus } = {}) {
  return unwrap<Paginated<Bet>>(httpClient.get("/bets/mine", { params: query }));
}
