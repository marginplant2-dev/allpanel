import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { fetchCategories, fetchGames } from "@/api/games";
import { fetchCasinoGames } from "@/api/casinoLive";
import { casinoTileArt } from "@/components/game/casinoArt";
import { Link } from "react-router-dom";
import { GameTile, GameTileSkeleton } from "@/components/game/GameCard";
import { ErrorState } from "@/components/common/States";
import { cn } from "@/lib/utils";
import { useDebounce } from "@/hooks/useDebounce";

export default function CasinoPage() {
  const [params, setParams] = useSearchParams();
  const category = params.get("category") ?? undefined;
  const [search, setSearch] = useState(params.get("search") ?? "");
  const debouncedSearch = useDebounce(search, 300);

  const categories = useQuery({ queryKey: ["categories"], queryFn: fetchCategories });
  // The live tables come straight off the feed, not from our own catalogue.
  const live = useQuery({ queryKey: ["casino-live-games"], queryFn: fetchCasinoGames });
  const liveGames = (live.data ?? []).filter(
    (g) =>
      (!category || g.category === category) &&
      (!debouncedSearch || g.name.toLowerCase().includes(debouncedSearch.toLowerCase())),
  );
  const games = useQuery({
    queryKey: ["games", { category, search: debouncedSearch }],
    queryFn: () => fetchGames({ category, search: debouncedSearch || undefined }),
  });

  function selectCategory(key?: string) {
    const next = new URLSearchParams(params);
    if (key) next.set("category", key);
    else next.delete("category");
    setParams(next);
  }

  const tabs = [{ key: undefined, name: "All" }, ...(categories.data ?? []).map((c) => ({ key: c.key, name: c.name }))];

  return (
    <div className="border border-ex-line bg-white">
      <div className="flex flex-wrap items-center justify-between gap-2 bg-ex-nav px-3 py-2">
        <h1 className="text-[13px] font-bold text-white">Our Casino</h1>
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
          <input
            placeholder="Search games"
            aria-label="Search games"
            className="w-full rounded-sm border border-ex-line py-1 pl-7 pr-2 text-[13px] text-slate-900 focus:outline-none focus:ring-1 focus:ring-ex-brand"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="flex overflow-x-auto border-b border-ex-line bg-ex-head">
        {tabs.map((c) => (
          <button
            key={c.key ?? "all"}
            onClick={() => selectCategory(c.key)}
            className={cn(
              "whitespace-nowrap border-r border-ex-line px-4 py-2 text-[13px] font-semibold capitalize text-slate-600 hover:bg-white",
              (category === c.key || (!category && !c.key)) && "bg-white text-ex-brand shadow-[inset_0_-3px_0_0_#1e5799]",
            )}
          >
            {c.name}
          </button>
        ))}
      </div>

      {liveGames.length > 0 && (
        <section>
          <h2 className="border-b border-ex-line bg-ex-head px-3 py-1.5 text-[12px] font-bold uppercase text-slate-600">
            Live Tables
          </h2>
          <div className="grid grid-cols-2 gap-1 p-1 sm:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8">
            {liveGames.map((g) => (
              <Link
                key={g.code}
                to={`/casino/live/${g.code}`}
                className="group block overflow-hidden border border-ex-line bg-white transition-shadow hover:shadow-md"
              >
                <img
                  src={casinoTileArt(g.name, g.category)}
                  alt={g.name}
                  loading="lazy"
                  className="aspect-[3/2] w-full object-cover"
                />
                <p className="truncate bg-ex-brand px-1.5 py-1 text-center text-[11px] font-bold uppercase text-white group-hover:bg-ex-nav">
                  {g.name}
                </p>
              </Link>
            ))}
          </div>
        </section>
      )}

      {games.isError ? (
        <ErrorState onRetry={() => games.refetch()} />
      ) : (
        <div className="grid grid-cols-3 gap-1 p-1 sm:grid-cols-5 lg:grid-cols-8 xl:grid-cols-10">
          {games.isLoading
            ? Array.from({ length: 20 }).map((_, i) => <GameTileSkeleton key={i} />)
            : games.data?.map((g) => <GameTile key={g.id} game={g} />)}
        </div>
      )}

      {!games.isLoading && games.data?.length === 0 && (
        <p className="px-3 py-10 text-center text-sm text-slate-500">
          {search || category
            ? "No games match that search."
            : "The casino catalogue has not been loaded yet."}
        </p>
      )}
    </div>
  );
}
