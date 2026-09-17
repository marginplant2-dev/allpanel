import { httpClient, unwrap } from "./client";
import type { EventDetail, SportEvent } from "@/types";

export interface Sport {
  id: string;
  key: string;
  name: string;
  group?: string;
  icon?: string;
  sort_order: number;
  status: string;
}

export interface LiveData {
  event_id: string;
  status: string;
  score: Record<string, number>;
}

export function fetchSports() {
  return unwrap<Sport[]>(httpClient.get("/sports"));
}

export function fetchEvents(params: { sport_id?: string; status?: string } = {}) {
  return unwrap<SportEvent[]>(httpClient.get("/events", { params }));
}

export function fetchEvent(eventId: string) {
  return unwrap<EventDetail>(httpClient.get(`/events/${eventId}`));
}

export function fetchLiveData(eventId: string) {
  return unwrap<LiveData>(httpClient.get(`/events/${eventId}/live`));
}
