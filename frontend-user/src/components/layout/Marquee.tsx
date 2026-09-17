import { Link } from "react-router-dom";
import { Radio } from "lucide-react";
import { useEvents } from "@/hooks/useEvents";

export function Marquee() {
  const { data } = useEvents();
  const items = (data ?? []).filter((e) => e.status === "live").slice(0, 12);
  const strip = items.length > 0 ? items : (data ?? []).slice(0, 12);
  if (strip.length === 0) return null;

  return (
    <div className="flex items-stretch overflow-hidden border-b border-ex-line bg-white">
      <span className="flex shrink-0 items-center gap-1.5 bg-ex-nav px-3 text-[12px] font-bold text-white">
        <Radio className="h-3.5 w-3.5" /> {items.length > 0 ? "IN-PLAY" : "UPCOMING"}
      </span>
      <div className="group flex-1 overflow-hidden">
        {/* duplicated once so the -50% translate loops seamlessly */}
        <div className="flex w-max animate-marquee group-hover:[animation-play-state:paused]">
          {[0, 1].map((copy) => (
            <div key={copy} className="flex" aria-hidden={copy === 1}>
              {strip.map((e) => (
                <Link
                  key={`${copy}-${e.id}`}
                  to={`/events/${e.id}`}
                  className="whitespace-nowrap px-4 py-1.5 text-[13px] text-slate-700 hover:text-ex-brand"
                >
                  <span className="mr-1.5 inline-block h-2 w-2 rounded-full bg-green-500 align-middle" />
                  {e.name}
                </Link>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
