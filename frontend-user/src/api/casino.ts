import { httpClient, unwrap } from "./client";

export interface LaunchedGame {
  game_url: string;
  transfer_id?: string | null;
}

/** Ask the provider for a one-off session URL for this player. */
export function launchGame(slug: string) {
  return unwrap<LaunchedGame>(httpClient.post(`/casino/launch/${slug}`));
}
