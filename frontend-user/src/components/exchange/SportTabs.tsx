import { cn } from "@/lib/utils";

export function SportTabs({
  tabs,
  active,
  onSelect,
}: {
  tabs: string[];
  active: string;
  onSelect: (tab: string) => void;
}) {
  if (tabs.length === 0) return null;
  return (
    <div className="flex overflow-x-auto border border-b-0 border-ex-line bg-ex-head">
      {tabs.map((tab) => (
        <button
          key={tab}
          type="button"
          onClick={() => onSelect(tab)}
          className={cn(
            "whitespace-nowrap border-r border-ex-line px-4 py-2 text-[13px] font-semibold text-slate-600 hover:bg-white",
            active === tab && "bg-white text-ex-brand shadow-[inset_0_-3px_0_0_#1e5799]",
          )}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}
