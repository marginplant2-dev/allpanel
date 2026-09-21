import { useState } from "react";
import { Link } from "react-router-dom";
import { casinoTileArt } from "@/components/game/casinoArt";

/**
 * A live-casino lobby tile.
 *
 * The artwork ships in `public/casino/<CODE>.png` (portrait, as supplied). If one
 * is missing the drawn tile stands in, so a new game code never leaves a hole.
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
  const [src, setSrc] = useState(`/casino/${code}.png`);

  return (
    <Link
      to={`/casino/live/${code}`}
      className="group block overflow-hidden border border-ex-line bg-white transition-shadow hover:shadow-md"
    >
      <img
        src={src}
        alt={name}
        loading="lazy"
        onError={() => setSrc(casinoTileArt(name, category))}
        className="aspect-[169/281] w-full bg-slate-900 object-cover"
      />
      <p className="truncate bg-ex-brand px-1.5 py-1 text-center text-[11px] font-bold uppercase text-white group-hover:bg-ex-nav">
        {name}
      </p>
    </Link>
  );
}
