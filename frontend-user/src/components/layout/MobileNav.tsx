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
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-ex-line bg-ex-nav lg:hidden">
      <div className="flex items-center justify-around">
        {ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                "flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-medium transition-colors",
                isActive ? "text-yellow-400" : "text-white/75",
              )
            }
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
