import { useQuery } from "@tanstack/react-query";
import { fetchEvents } from "@/api/sports";

/**
 * Shared events query — every caller that passes the same params reuses one
 * request, which matters because each provider call burns an odds-API credit.
 */
export function useEvents(params: { sport_id?: string; status?: string } = {}) {
  return useQuery({
    queryKey: ["events", params],
    queryFn: () => fetchEvents(params),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}
