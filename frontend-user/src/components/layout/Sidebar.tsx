import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, Minus, Plus } from "lucide-react";
import { fetchSports } from "@/api/sports";
import { cn } from "@/lib/utils";

function Panel({
  title,
  children,
  defaultOpen = true,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="mb-1 border border-ex-line bg-white">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="ex-sec w-full px-2.5 py-2"
      >
        {title}
        {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
      </button>
      {open && <div className="py-1">{children}</div>}
    </section>
  );
}

function Item({ to, label, active }: { to: string; label: string; active?: boolean }) {
  return (
    <Link
      to={to}
      className={cn(
        "block truncate px-3 py-1.5 text-[13px] text-slate-700 hover:bg-ex-back3 hover:text-ex-brand",
        active && "bg-ex-back3 font-semibold text-ex-brand",
      )}
    >
      {label}
    </Link>
  );
}

/** `collapsed` starts every panel shut — the mobile copy, where the sports tree
 *  would otherwise push the board off the screen. */
export function Sidebar({ collapsed = false }: { collapsed?: boolean }) {
  const [params] = useSearchParams();
  const activeSport = params.get("sport");
  const activeGroup = params.get("group");
  const sports = useQuery({ queryKey: ["sports"], queryFn: fetchSports });
  const [expanded, setExpanded] = useState<string[]>([]);

  const groups = useMemo(() => {
    const map = new Map<string, { id: string; name: string }[]>();
    for (const s of sports.data ?? []) {
      const group = s.group ?? "Sports";
      const list = map.get(group) ?? [];
      list.push({ id: s.id, name: s.name });
      map.set(group, list);
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [sports.data]);

  function toggle(group: string) {
    setExpanded((prev) => (prev.includes(group) ? prev.filter((g) => g !== group) : [...prev, group]));
  }

  return (
    <aside className="w-full shrink-0 lg:w-[230px]">
      <Panel title="Racing Sports" defaultOpen={!collapsed}>
        <Item to="/sports?group=Horse Racing" label="Horse Racing" active={activeGroup === "Horse Racing"} />
        <Item to="/sports?group=Greyhound Racing" label="Greyhound Racing" active={activeGroup === "Greyhound Racing"} />
      </Panel>

      <Panel title="Others" defaultOpen={!collapsed}>
        <Item to="/casino" label="Our Casino" />
        <Item to="/casino?category=live" label="Live Casino" />
        <Item to="/casino?category=slots" label="Slot Game" />
        <Item to="/casino?category=table" label="Table Games" />
      </Panel>

      <Panel title="All Sports" defaultOpen={!collapsed}>
        {sports.isLoading && <p className="px-3 py-2 text-[13px] text-slate-500">Loading…</p>}
        {groups.map(([group, list]) => {
          const open = expanded.includes(group);
          return (
            <div key={group}>
              <div className="flex items-center gap-1 px-2 py-1.5 hover:bg-ex-back3">
                <button type="button" onClick={() => toggle(group)} aria-label={`Toggle ${group}`}>
                  {open ? (
                    <Minus className="h-3.5 w-3.5 text-slate-600" />
                  ) : (
                    <Plus className="h-3.5 w-3.5 text-slate-600" />
                  )}
                </button>
                <Link
                  to={`/sports?group=${encodeURIComponent(group)}`}
                  className={cn(
                    "truncate text-[13px] text-slate-800 hover:text-ex-brand",
                    activeGroup === group && "font-semibold text-ex-brand",
                  )}
                >
                  {group}
                </Link>
              </div>
              {open &&
                list.map((s) => (
                  <Item
                    key={s.id}
                    to={`/sports?sport=${encodeURIComponent(s.id)}`}
                    label={s.name}
                    active={activeSport === s.id}
                  />
                ))}
            </div>
          );
        })}
      </Panel>
    </aside>
  );
}
