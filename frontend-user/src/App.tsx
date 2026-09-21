import { Suspense, lazy } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { queryClient } from "@/lib/queryClient";
import { Spinner } from "@/components/ui/spinner";
import { AppLayout } from "@/components/layout/AppLayout";
import { ProtectedRoute } from "@/routes/ProtectedRoute";

const LoginPage = lazy(() => import("@/features/auth/LoginPage"));
const RegisterPage = lazy(() => import("@/features/auth/RegisterPage"));
const ForgotPasswordPage = lazy(() => import("@/features/auth/ForgotPasswordPage"));
const HomePage = lazy(() => import("@/features/home/HomePage"));
const SportsPage = lazy(() => import("@/features/sports/SportsPage"));
const EventDetailPage = lazy(() => import("@/features/events/EventDetailPage"));
const CasinoPage = lazy(() => import("@/features/casino/CasinoPage"));
const GameDetailPage = lazy(() => import("@/features/casino/GameDetailPage"));
const LiveGamePage = lazy(() => import("@/features/casino/LiveGamePage"));
const WalletPage = lazy(() => import("@/features/wallet/WalletPage"));
const CreditHistoryPage = lazy(() => import("@/features/wallet/CreditHistoryPage"));
const ActivityHistoryPage = lazy(() => import("@/features/wallet/ActivityHistoryPage"));
const ProfilePage = lazy(() => import("@/features/profile/ProfilePage"));
const SecurityPage = lazy(() => import("@/features/profile/SecurityPage"));
const NotificationsPage = lazy(() => import("@/features/notifications/NotificationsPage"));
const HelpPage = lazy(() => import("@/features/help/HelpPage"));

function PageFallback() {
  return (
    <div className="grid min-h-[60vh] place-items-center">
      <Spinner className="h-8 w-8" />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />

            <Route element={<AppLayout />}>
              <Route path="/" element={<HomePage />} />
              <Route path="/sports" element={<SportsPage />} />
              <Route path="/live" element={<SportsPage liveOnly />} />
              <Route path="/events/:eventId" element={<EventDetailPage />} />
              <Route path="/casino" element={<CasinoPage />} />
              <Route path="/casino/live/:code" element={<LiveGamePage />} />
              <Route path="/casino/:slug" element={<GameDetailPage />} />
              <Route path="/help" element={<HelpPage />} />

              <Route element={<ProtectedRoute />}>
                <Route path="/wallet" element={<WalletPage />} />
                <Route path="/wallet/history" element={<CreditHistoryPage />} />
                <Route path="/activity" element={<ActivityHistoryPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/security" element={<SecurityPage />} />
                <Route path="/notifications" element={<NotificationsPage />} />
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
