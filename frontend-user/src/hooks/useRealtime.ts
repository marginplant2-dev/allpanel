import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getAccessToken } from "@/api/client";
import { useAuthStore } from "@/store/auth";
import type { Wallet } from "@/types";

function wsBaseUrl(): string {
  const configured = import.meta.env.VITE_WS_BASE_URL;
  if (configured) return configured;
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}`;
}

/** Connect to the realtime WebSocket and reflect pushed events into the query cache. */
export function useRealtime() {
  const queryClient = useQueryClient();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!isAuthenticated || !token) return;

    let pingTimer: ReturnType<typeof setInterval> | undefined;
    let closed = false;

    const ws = new WebSocket(`${wsBaseUrl()}/ws?token=${encodeURIComponent(token)}`);
    wsRef.current = ws;

    ws.onopen = () => {
      pingTimer = setInterval(() => ws.readyState === WebSocket.OPEN && ws.send("ping"), 25_000);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as { type: string; data: unknown };
        switch (msg.type) {
          case "wallet_update":
            queryClient.setQueryData<Wallet>(["wallet"], (prev) =>
              prev ? { ...prev, ...(msg.data as Partial<Wallet>) } : (msg.data as Wallet),
            );
            break;
          case "notification":
            queryClient.invalidateQueries({ queryKey: ["notifications"] });
            break;
          case "live_event":
            queryClient.invalidateQueries({ queryKey: ["events"] });
            queryClient.invalidateQueries({ queryKey: ["event-live"] });
            break;
        }
      } catch {
        /* ignore malformed frames */
      }
    };

    return () => {
      closed = true;
      if (pingTimer) clearInterval(pingTimer);
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) ws.close();
      wsRef.current = null;
      void closed;
    };
  }, [isAuthenticated, queryClient]);
}
