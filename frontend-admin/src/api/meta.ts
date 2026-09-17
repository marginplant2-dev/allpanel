import { httpClient, unwrap } from "./client";

export interface MetaInfo {
  app: string;
  environment: string;
  version: string;
}

export function getMeta() {
  return unwrap<MetaInfo>(httpClient.get("/meta"));
}
