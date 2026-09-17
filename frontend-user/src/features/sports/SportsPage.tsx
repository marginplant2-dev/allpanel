import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchSports } from "@/api/sports";
import { useEvents } from "@/hooks/useEvents";
import { OddsGrid } from "@/components/exchange/OddsGrid";
import { BetSlip, type BetSelection } from "@/components/bets/BetSlip";
import { ErrorState } from "@/components/common/States";
import { Sidebar } from "@/components/layout/Sidebar";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";

export default function SportsPage({ liveOnly = false }: { liveOnly?: boolean }) {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [selection, setSelection] = useState<BetSelection | null>(null);
  const [tab, setTab] = useState<"all" | "live" | "upcoming">(liveOnly ? "live" : "all");

  // ?sport= narrows the provider call; ?group= is a client-side cut of the
  // all-sports feed (the provider takes one sport key, not a group).
  const sportId = params.get("sport") ?? undefined;
  const group = params.get("group") ?? undefined;
  const status = liveOnly ? "live" : tab === "all" ? undefined : tab;

  const events = useEvents({ sport_id: sportId, status });
  const sports = useQuery({ queryKey: ["sports"], queryFn: fetchSports });

  const title = useMemo(() => {
    if (sportId) return sports.data?.find((s) => s.id === sportId)?.name ?? sportId;
    return group ?? (liveOnly ? "In-Play" : "All Sports");
  }, [sportId, group, liveOnly, sports.data]);

  const rows = useMemo(() => {
    const list = events.data ?? [];
    if (!group) return list;
    const inGroup = new Set((sports.data ?? []).filter((s) => (s.group ?? "Sports") === group).map((s) => s.id));
    return list.filter((e) => inGroup.has(e.sport_id));
  }, [events.data, group, sports.data]);

  function onSelect(next: BetSelection) {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    setSelection(next);
  }

  if (events.isError) return <ErrorState onRetry={() => events.refetch()} />;

  return (
    <div className="space-y-3">
      {/* the sidebar tree is the primary sport picker on mobile, where it is hidden from the shell */}
      <div className="lg:hidden">
        <Sidebar />
      </div>

      <div>
        <div className="flex items-center justify-between border border-b-0 border-ex-line bg-ex-nav px-3 py-2">
          <h1 className="text-[13px] font-bold text-white">{title}</h1>
          {!liveOnly && (
            <div className="flex gap-1">
              {(["all", "live", "upcoming"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={cn(
                    "rounded-sm px-2 py-0.5 text-[12px] font-semibold capitalize text-white/75 hover:bg-white/10",
                    tab === t && "bg-yellow-400 text-slate-900",
                  )}
                >
                  {t}
                </button>
              ))}
            </div>
          )}
        </div>
        <OddsGrid
          events={rows}
          isLoading={events.isLoading}
          title="Game"
          onSelect={onSelect}
          emptyLabel="No events for this selection."
        />
      </div>

      {selection && (
        <BetSlip
          selection={selection}
          onClose={() => setSelection(null)}
          className="fixed inset-x-0 bottom-14 z-50 lg:inset-x-auto lg:bottom-3 lg:right-3 lg:w-[340px]"
        />
      )}
    </div>
  );
}
