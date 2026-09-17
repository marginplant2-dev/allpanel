import { httpClient, unwrap } from "./client";

export interface MetaInfo {
  app: string;
  environment: string;
  version: string;
  sports_provider: string;
  /** "live" = prices from the odds provider, "seeded" = demo board (provider down/out of credits). */
  sports_data_source: "live" | "seeded";
}

export function getMeta() {
  return unwrap<MetaInfo>(httpClient.get("/meta"));
}
