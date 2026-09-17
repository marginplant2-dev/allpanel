import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { Marquee } from "./Marquee";
import { MobileNav } from "./MobileNav";
import { useSessionHydration } from "@/hooks/useSession";
import { useRealtime } from "@/hooks/useRealtime";

export function AppLayout() {
  useSessionHydration();
  useRealtime();
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <Marquee />
      <div className="mx-auto flex w-full max-w-[1600px] flex-1 gap-2 px-2 py-2">
        <div className="hidden lg:block">
          <Sidebar />
        </div>
        <main className="min-w-0 flex-1 pb-20 lg:pb-2">
          <Outlet />
        </main>
      </div>
      <MobileNav />
      <footer className="border-t border-ex-line bg-white py-4">
        <div className="mx-auto flex max-w-[1600px] flex-col items-center justify-between gap-2 px-3 text-[12px] text-slate-500 sm:flex-row">
          <p>© {new Date().getFullYear()} SportX · Virtual credits only · Entertainment simulation.</p>
          <div className="flex gap-4">
            <a href="/help" className="hover:text-ex-brand">Rules</a>
            <a href="/help" className="hover:text-ex-brand">Responsible Play</a>
            <a href="/help" className="hover:text-ex-brand">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
