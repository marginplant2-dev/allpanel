import { NavLink } from "react-router-dom";
import { Gamepad2, Home, Radio, Trophy, Wallet } from "lucide-react";
import { cn } from "@/lib/utils";

const ITEMS = [
  { to: "/", label: "Home", icon: Home, end: true },
  { to: "/sports", label: "Sports", icon: Trophy },
  { to: "/live", label: "Live", icon: Radio },
  { to: "/casino", label: "Casino", icon: Gamepad2 },
  { to: "/wallet", label: "Wallet", icon: Wallet },
];

export function MobileNav() {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-ex-line bg-gradient-to-r from-ex-nav via-ex-navhover to-ex-nav pb-[env(safe-area-inset-bottom)] shadow-[0_-2px_10px_rgba(0,0,0,0.25)] lg:hidden">
      <div className="flex items-stretch justify-around">
        {ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                // height stays ~56px: the bet slip docks at bottom-14 above it
                "flex flex-1 flex-col items-center gap-0.5 py-1.5 text-[11px] font-semibold transition-colors",
                isActive ? "text-yellow-400" : "text-white/75",
              )
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className={cn(
                    "grid h-7 w-12 place-items-center rounded-full transition-colors",
                    isActive && "bg-yellow-400/15",
                  )}
                >
                  <item.icon className="h-5 w-5" />
                </span>
                {item.label}
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
