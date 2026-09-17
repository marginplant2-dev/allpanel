import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { LogOut, Menu, Moon, PanelLeftClose, PanelLeftOpen, Sun, User } from "lucide-react";
import { logout as apiLogout } from "@/api/auth";
import { fetchMyWallet } from "@/api/misc";
import { formatCredits } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import { useThemeStore } from "@/store/theme";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { RoleBadge } from "@/components/common/StatusBadge";

export function Topbar({
  onToggleSidebar,
  onToggleMobile,
  collapsed,
}: {
  onToggleSidebar: () => void;
  onToggleMobile: () => void;
  collapsed: boolean;
}) {
  const { user, logout } = useAuthStore();
  const { theme, toggle } = useThemeStore();
  // coins in the header: you cannot fund anyone below you without them
  const { data: wallet } = useQuery({ queryKey: ["my-wallet"], queryFn: fetchMyWallet, refetchInterval: 60_000 });
  const navigate = useNavigate();

  async function handleLogout() {
    const refresh = localStorage.getItem("sportx.refreshToken");
    if (refresh) await apiLogout(refresh).catch(() => undefined);
    logout();
    navigate("/login");
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur-xl">
      <button onClick={onToggleMobile} className="grid h-9 w-9 place-items-center rounded-md hover:bg-secondary lg:hidden">
        <Menu className="h-5 w-5" />
      </button>
      <button
        onClick={onToggleSidebar}
        className="hidden h-9 w-9 place-items-center rounded-md text-muted-foreground hover:bg-secondary lg:grid"
      >
        {collapsed ? <PanelLeftOpen className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}
      </button>

      <div className="ml-auto flex items-center gap-2 sm:gap-3">
        <span className="rounded-md border border-border bg-secondary/40 px-2.5 py-1.5 text-sm font-semibold">
          <span className="text-muted-foreground">Coins </span>
          {formatCredits(wallet?.available_balance ?? 0)}
        </span>
        <button
          onClick={toggle}
          aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
          className="grid h-9 w-9 place-items-center rounded-md text-muted-foreground hover:bg-secondary"
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>
        {user && <span className="hidden sm:inline"><RoleBadge role={user.role} /></span>}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-secondary">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-accent/20 text-accent">
                <User className="h-4 w-4" />
              </span>
              <span className="hidden sm:inline">{user?.full_name ?? user?.username}</span>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>{user?.username}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate("/system/settings")}>Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-destructive">
              <LogOut className="h-4 w-4" /> Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
