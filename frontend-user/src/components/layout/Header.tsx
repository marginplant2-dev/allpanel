import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Bell, ChevronDown, LogOut, Search } from "lucide-react";
import { fetchWallet } from "@/api/wallet";
import { fetchNotifications } from "@/api/notifications";
import { getMeta } from "@/api/meta";
import { logout as apiLogout } from "@/api/auth";
import { useAuthStore } from "@/store/auth";
import { cn, formatCredits } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

/** Sport tabs map to The Odds API `group` values; casino tabs map to game categories. */
const NAV = [
  { label: "HOME", to: "/" },
  { label: "IN-PLAY", to: "/live" },
  { label: "CRICKET", to: "/sports?group=Cricket" },
  { label: "FOOTBALL", to: "/sports?group=Soccer" },
  { label: "TENNIS", to: "/sports?group=Tennis" },
  { label: "BASKETBALL", to: "/sports?group=Basketball" },
  { label: "BASEBALL", to: "/sports?group=Baseball" },
  { label: "ICE HOCKEY", to: "/sports?group=Ice Hockey" },
  { label: "CASINO", to: "/casino" },
  { label: "SLOTS", to: "/casino?category=slots" },
  { label: "LIVE CASINO", to: "/casino?category=live" },
];

export function Header() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [search, setSearch] = useState("");
  // NavLink matches on pathname only, so every /sports?group=… tab would light up
  // at once — compare the full path+query instead.
  const current = decodeURIComponent(location.pathname + location.search);

  const { data: wallet } = useQuery({
    queryKey: ["wallet"],
    queryFn: fetchWallet,
    enabled: isAuthenticated,
    refetchInterval: 60_000,
  });

  const { data: notifications } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => fetchNotifications({ page_size: 1 }),
    enabled: isAuthenticated,
  });
  const unread = notifications?.unread ?? 0;

  const { data: meta } = useQuery({ queryKey: ["meta"], queryFn: getMeta, staleTime: 60_000, refetchInterval: 60_000 });
  const demoPrices = meta?.sports_data_source === "seeded";

  async function handleLogout() {
    const refresh = localStorage.getItem("sportx.refreshToken");
    if (refresh) await apiLogout(refresh).catch(() => undefined);
    logout();
    navigate("/login");
  }

  return (
    <header className="sticky top-0 z-40 shadow-md">
      {/* Brand bar */}
      <div className="bg-ex-brand text-white">
        <div className="mx-auto flex h-14 max-w-[1600px] items-center gap-2 px-2 sm:gap-3 sm:px-3">
          <Link to="/" className="shrink-0 text-lg font-black tracking-[0.15em] sm:text-3xl sm:tracking-[0.2em]">
            SPORTX
          </Link>

          <form
            className="ml-auto hidden items-center rounded-sm bg-white/15 px-2 sm:flex"
            onSubmit={(e) => {
              e.preventDefault();
              navigate(`/casino?search=${encodeURIComponent(search.trim())}`);
            }}
          >
            <Search className="h-4 w-4 text-white/80" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search games"
              aria-label="Search games"
              className="w-36 bg-transparent px-2 py-1.5 text-sm text-white placeholder:text-white/60 focus:outline-none lg:w-52"
            />
          </form>

          {demoPrices && (
            <span
              title="The live odds feed is unavailable (bad key or no credits) — the board is showing seeded demo prices."
              className="hidden rounded-sm bg-yellow-400 px-2 py-0.5 text-[11px] font-bold text-slate-900 sm:inline"
            >
              DEMO ODDS
            </span>
          )}

          <Link to="/help" className="ml-auto hidden shrink-0 text-sm font-semibold hover:underline sm:inline sm:ml-0">
            Rules
          </Link>

          {isAuthenticated ? (
            <>
              <Link to="/wallet" className="ml-auto shrink-0 whitespace-nowrap text-right text-[11px] font-bold leading-tight sm:ml-0 sm:text-[13px]">
                <div>Balance: {formatCredits(wallet?.available_balance ?? 0)}</div>
                <div className="font-normal text-white/80">Exp: {formatCredits(wallet?.locked_balance ?? 0)}</div>
              </Link>

              <Link to="/notifications" className="relative hidden h-8 w-8 shrink-0 place-items-center rounded hover:bg-white/10 sm:grid">
                <Bell className="h-4 w-4" />
                {unread > 0 && (
                  <span className="absolute right-0 top-0 grid h-4 min-w-4 place-items-center rounded-full bg-red-600 px-1 text-[10px] font-bold">
                    {unread > 9 ? "9+" : unread}
                  </span>
                )}
              </Link>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="flex min-w-0 shrink items-center gap-1 text-sm font-semibold hover:underline">
                    <span className="max-w-[70px] truncate sm:max-w-none">{user?.username ?? "Account"}</span>
                    <ChevronDown className="h-4 w-4 shrink-0" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuLabel>{user?.full_name ?? user?.username}</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate("/profile")}>Profile</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/wallet")}>Wallet</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/activity")}>My Bets</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/wallet/history")}>Account Statement</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/security")}>Change Password</DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-destructive">
                    <LogOut className="h-4 w-4" /> Log out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <>
              <Button size="sm" variant="ghost" className="ml-auto shrink-0 text-white hover:bg-white/10 sm:ml-0" onClick={() => navigate("/login")}>
                Login
              </Button>
              <Button size="sm" className="shrink-0 bg-yellow-400 text-slate-900 hover:bg-yellow-300" onClick={() => navigate("/register")}>
                Sign up
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Sport / game strip */}
      <nav className="bg-ex-nav">
        <div className="mx-auto flex max-w-[1600px] items-stretch overflow-x-auto px-1">
          {NAV.map((item) => (
            <Link
              key={item.label}
              to={item.to}
              className={cn(
                "whitespace-nowrap px-3 py-2.5 text-[13px] font-bold tracking-wide text-white/85 transition-colors hover:bg-ex-navhover hover:text-white",
                current === item.to && "border-b-2 border-yellow-400 text-white",
              )}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
