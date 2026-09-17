import { Link } from "react-router-dom";
import type { Game } from "@/types";
import { LazyImage } from "@/components/common/LazyImage";
import { Skeleton } from "@/components/ui/skeleton";

/** Casino lobby tile: artwork with a solid caption bar, laid out edge-to-edge in a dense grid. */
export function GameTile({ game }: { game: Game }) {
  return (
    <Link
      to={`/casino/${game.slug}`}
      className="group block overflow-hidden border border-ex-line bg-white transition-shadow hover:shadow-md"
    >
      <div className="relative">
        <LazyImage src={game.thumbnail_url} alt={game.name} aspect="aspect-[4/3]" />
        {game.category === "live" && (
          <span className="absolute left-1 top-1 rounded-sm bg-red-600 px-1 text-[10px] font-bold text-white">
            LIVE
          </span>
        )}
      </div>
      <p className="truncate bg-ex-brand px-1.5 py-1 text-center text-[11px] font-bold uppercase text-white group-hover:bg-ex-nav">
        {game.name}
      </p>
    </Link>
  );
}

export function GameTileSkeleton() {
  return (
    <div className="border border-ex-line">
      <Skeleton className="aspect-[4/3] w-full rounded-none" />
      <Skeleton className="h-5 w-full rounded-none" />
    </div>
  );
}
