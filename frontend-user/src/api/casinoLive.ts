import { httpClient, unwrap } from "./client";
import type { Paginated } from "@/types";

export interface CasinoGame {
  code: string;
  name: string;
  category: string;
}

export interface CasinoOption {
  sid: string | number;
  name: string;
  price: number;
  size: number;
  status: string;
  open: boolean;
  min_stake: number;
  max_stake: number;
  group: string;
  sort: number;
}

export interface CasinoResult {
  round_id: string;
  winners: string[];
  /** The winning selection's name, when the table has told us what that sid is. */
  winner_names: string[];
}

export interface CasinoTable {
  code: string;
  name: string;
  category: string;
  gtype: string | null;
  round_id: string;
  /** Seconds left to bet on this round; 0 means the cards are being dealt. */
  timer: number;
  betting_open: boolean;
  cards: string[];
  remark: string | null;
  options: CasinoOption[];
  live: boolean;
  results: CasinoResult[];
  /** sid -> selection name for this table. */
  labels: Record<string, string>;
}

export interface CasinoBet {
  id: string;
  code: string;
  game_name: string;
  round_id: string;
  sid: string;
  selection: string;
  price: number;
  stake: number;
  potential_payout: number;
  status: "PENDING" | "WON" | "LOST" | "VOID";
  payout: number | null;
  placed_at: string;
}

export function fetchCasinoGames() {
  return unwrap<CasinoGame[]>(httpClient.get("/casino/live/games"));
}

export function fetchCasinoTable(code: string) {
  return unwrap<CasinoTable>(httpClient.get(`/casino/live/${code}`));
}

/** The round id travels with the bet: a stale round is refused, never re-aimed. */
export function placeCasinoBet(payload: {
  code: string;
  round_id: string;
  sid: string;
  stake: number;
}) {
  return unwrap<CasinoBet>(httpClient.post("/casino/live/bet", payload));
}

export function fetchMyCasinoBets(code?: string) {
  return unwrap<Paginated<CasinoBet>>(
    httpClient.get("/casino/live/bets/mine", { params: { code, page_size: 20 } }),
  );
}
