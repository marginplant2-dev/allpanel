import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchSports } from "@/api/sports";
import { fetchGames } from "@/api/games";
import { useEvents } from "@/hooks/useEvents";
import { OddsGrid } from "@/components/exchange/OddsGrid";
import { SportTabs } from "@/components/exchange/SportTabs";
import { GameTile } from "@/components/game/GameCard";
import { BetSlip, type BetSelection } from "@/components/bets/BetSlip";
import { ErrorState } from "@/components/common/States";
import { useAuthStore } from "@/store/auth";

export default function HomePage() {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [selection, setSelection] = useState<BetSelection | null>(null);
  const [tab, setTab] = useState<string | null>(null);

  const events = useEvents();
  const sports = useQuery({ queryKey: ["sports"], queryFn: fetchSports });
  const games = useQuery({ queryKey: ["games", { featured: true }], queryFn: () => fetchGames({ featured: true }) });

  // The feed spans every sport; tabs come from the sport groups actually present.
  const groupOf = useMemo(() => {
    const map = new Map<string, string>();
    for (const s of sports.data ?? []) map.set(s.id, s.group ?? "Sports");
    return map;
  }, [sports.data]);

  // Cricket leads the board here the way it does on every exchange in this market;
  // anything else the feed sends follows, busiest first.
  const PRIORITY = ["Cricket", "Soccer", "Tennis"];
  const tabs = useMemo(() => {
    const counts = new Map<string, number>();
    for (const e of events.data ?? []) {
      const group = groupOf.get(e.sport_id) ?? e.league ?? "Sports";
      counts.set(group, (counts.get(group) ?? 0) + 1);
    }
    return [...counts.entries()]
      .sort((a, b) => {
        const pa = PRIORITY.indexOf(a[0]);
        const pb = PRIORITY.indexOf(b[0]);
        if (pa !== pb) return (pa < 0 ? 99 : pa) - (pb < 0 ? 99 : pb);
        return b[1] - a[1];
      })
      .map(([g]) => g);
  }, [events.data, groupOf]);

  const activeTab = tab ?? tabs[0] ?? "";
  const rows = (events.data ?? []).filter(
    (e) => (groupOf.get(e.sport_id) ?? e.league ?? "Sports") === activeTab,
  );

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
      <div>
        <SportTabs tabs={tabs} active={activeTab} onSelect={setTab} />
        <OddsGrid
          events={rows}
          isLoading={events.isLoading}
          title={activeTab || "Game"}
          onSelect={onSelect}
          emptyLabel="No open markets in this sport right now."
        />
      </div>

      <section className="border border-ex-line bg-white">
        <h2 className="bg-ex-nav px-3 py-2 text-[13px] font-bold text-white">Our Casino</h2>
        <div className="grid grid-cols-3 gap-1 p-1 sm:grid-cols-5 lg:grid-cols-8">
          {games.data?.slice(0, 16).map((g) => (
            <GameTile key={g.id} game={g} />
          ))}
        </div>
      </section>

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
