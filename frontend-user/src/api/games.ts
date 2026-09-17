import { httpClient, unwrap } from "./client";
import type { Game } from "@/types";

export interface GameCategory {
  id: string;
  key: string;
  name: string;
  sort_order: number;
  status: string;
}

export interface GameFilters {
  category?: string;
  featured?: boolean;
  search?: string;
}

export function fetchGames(filters: GameFilters = {}) {
  return unwrap<Game[]>(httpClient.get("/games", { params: filters }));
}

export function fetchCategories() {
  return unwrap<GameCategory[]>(httpClient.get("/games/categories"));
}

export function fetchGameBySlug(slug: string) {
  return unwrap<Game>(httpClient.get(`/games/${slug}`));
}
