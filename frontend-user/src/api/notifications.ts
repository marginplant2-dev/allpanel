import { httpClient, unwrap } from "./client";
import type { Paginated } from "@/types";

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  body: string;
  read: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
}

export type NotificationPage = Paginated<Notification> & { unread: number };

export function fetchNotifications(params: { page?: number; page_size?: number } = {}) {
  return unwrap<NotificationPage>(httpClient.get("/notifications", { params }));
}

export function markNotificationRead(id: string) {
  return unwrap<null>(httpClient.post(`/notifications/${id}/read`));
}

export function markAllNotificationsRead() {
  return unwrap<{ updated: number }>(httpClient.post("/notifications/read-all"));
}
