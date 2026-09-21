import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Play, X } from "lucide-react";
import { fetchGameBySlug, fetchGames } from "@/api/games";
import { launchGame } from "@/api/casino";
import type { ApiError } from "@/api/client";
import { GameTile } from "@/components/game/GameCard";
import { ErrorState } from "@/components/common/States";
import { LazyImage } from "@/components/common/LazyImage";
import { useAuthStore } from "@/store/auth";

export default function GameDetailPage() {
  const { slug = "" } = useParams();
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [url, setUrl] = useState<string | null>(null);

  const game = useQuery({ queryKey: ["game", slug], queryFn: () => fetchGameBySlug(slug) });
  const related = useQuery({
    queryKey: ["games", { category: game.data?.category }],
    queryFn: () => fetchGames({ category: game.data?.category }),
    enabled: !!game.data,
  });

  // The session URL is issued per player and per launch — it is never cached.
  const launch = useMutation({
    mutationFn: () => launchGame(slug),
    onSuccess: (data) => setUrl(data.game_url),
  });
  const launchError = launch.error as ApiError | null;

  if (game.isError || (!game.isLoading && !game.data)) {
    return <ErrorState title="Game not found" onRetry={() => game.refetch()} />;
  }
  if (game.isLoading || !game.data) {
    return <div className="h-64 animate-pulse border border-ex-line bg-white" />;
  }
  const g = game.data;

  function play() {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    launch.mutate();
  }

  return (
    <div className="space-y-2">
      <Link to="/casino" className="inline-flex items-center gap-1 text-[13px] text-slate-600 hover:text-ex-brand">
        <ArrowLeft className="h-4 w-4" /> Back to casino
      </Link>

      <div className="border border-ex-line bg-white">
        <div className="ex-sec">
          <h1 className="truncate text-[15px] font-bold uppercase">{g.name}</h1>
          <span className="shrink-0 text-[12px] capitalize text-white/80">{g.provider.replace(/_/g, " ")}</span>
        </div>

        {url ? (
          <div className="relative">
            <button
              type="button"
              onClick={() => setUrl(null)}
              className="absolute right-2 top-2 z-10 grid h-8 w-8 place-items-center rounded-full bg-black/70 text-white"
              aria-label="Close game"
            >
              <X className="h-4 w-4" />
            </button>
            <iframe
              src={url}
              title={g.name}
              allow="autoplay; fullscreen; payment"
              className="h-[70vh] w-full border-0 bg-black"
            />
          </div>
        ) : (
          <div className="grid gap-3 p-3 sm:grid-cols-[260px_1fr]">
            <LazyImage src={g.thumbnail_url} alt={g.name} aspect="aspect-[4/3]" />
            <div className="flex flex-col items-start gap-3">
              <button
                type="button"
                onClick={play}
                disabled={launch.isPending}
                className="flex items-center gap-2 bg-emerald-600 px-5 py-2.5 text-[14px] font-bold text-white hover:bg-emerald-700 disabled:bg-slate-300"
              >
                <Play className="h-4 w-4 fill-current" />
                {launch.isPending ? "Starting…" : "Play Now"}
              </button>
              {launchError && <p className="text-[13px] text-red-600">{launchError.message}</p>}
              <p className="text-[12px] text-slate-500">
                Stakes and winnings settle straight to your main balance — the game reports every round
                back to this account.
              </p>
            </div>
          </div>
        )}
      </div>

      {related.data && related.data.length > 1 && (
        <section className="border border-ex-line bg-white">
          <h2 className="ex-sec">More {g.category} games</h2>
          <div className="grid grid-cols-3 gap-1 p-1 sm:grid-cols-5 lg:grid-cols-8">
            {related.data.filter((r) => r.slug !== g.slug).slice(0, 16).map((r) => (
              <GameTile key={r.id} game={r} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
