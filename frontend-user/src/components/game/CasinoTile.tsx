import { useState } from "react";
import { Link } from "react-router-dom";
import { casinoTileArt } from "@/components/game/casinoArt";

/**
 * A live-casino lobby tile.
 *
 * The artwork ships as `public/casino-art/<CODE>.webp` (the supplied PNGs live in
 * art-src/casino; WebP is ~86% smaller, which is the difference between a lobby
 * that paints at once and one that trickles in) —
 * not `/casino/`, which is an SPA route: a real directory there makes nginx
 * answer 403 instead of serving the app. If a file is missing the drawn tile stands in,
 * so a new game code never leaves a hole.
 */
export function CasinoTile({
  code,
  name,
  category,
}: {
  code: string;
  name: string;
  category: string;
}) {
  const [src, setSrc] = useState(`/casino-art/${code}.webp`);

  return (
    <Link
      to={`/casino/live/${code}`}
      className="group block overflow-hidden rounded-md border border-ex-line bg-slate-900 shadow-sm ring-ex-brand transition hover:shadow-lg hover:ring-2"
    >
      <img
        src={src}
        alt={name}
        loading="lazy"
        onError={() => setSrc(casinoTileArt(name, category))}
        className="aspect-[169/281] w-full bg-slate-900 object-cover"
      />
      {/* The supplied artwork has the name printed on it; only the drawn stand-in,
          which is a different shape and gets cropped, needs a caption. */}
      {src.startsWith("data:") && (
        <p className="truncate bg-ex-brand px-1.5 py-1 text-center text-[11px] font-bold uppercase text-white">
          {name}
        </p>
      )}
    </Link>
  );
}
