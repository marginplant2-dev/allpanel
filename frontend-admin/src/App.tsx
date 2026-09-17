import { Suspense, lazy } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { queryClient } from "@/lib/queryClient";
import { Spinner } from "@/components/ui/spinner";
import { AdminLayout } from "@/components/layout/AdminLayout";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { Toaster } from "@/components/common/Toaster";

const AdminLoginPage = lazy(() => import("@/features/auth/AdminLoginPage"));
const DashboardPage = lazy(() => import("@/features/dashboard/DashboardPage"));
const UsersListPage = lazy(() => import("@/features/users/UsersListPage"));
const CreateUserPage = lazy(() => import("@/features/users/CreateUserPage"));
const UserDetailPage = lazy(() => import("@/features/users/UserDetailPage"));
const HierarchyTreePage = lazy(() => import("@/features/hierarchy/HierarchyTreePage"));
const CreditTransferPage = lazy(() => import("@/features/credits/CreditTransferPage"));
const CreditRequestsPage = lazy(() => import("@/features/credits/CreditRequestsPage"));
const LedgerPage = lazy(() => import("@/features/credits/LedgerPage"));
const GamesPage = lazy(() => import("@/features/content/GamesPage"));
const ReportsPage = lazy(() => import("@/features/reports/ReportsPage"));
const SettingsPage = lazy(() => import("@/features/system/SettingsPage"));
const AuditLogsPage = lazy(() => import("@/features/security/AuditLogsPage"));

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
            <Route path="/login" element={<AdminLoginPage />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<AdminLayout />}>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/users" element={<UsersListPage />} />
                <Route path="/users/create" element={<CreateUserPage />} />
                <Route path="/users/:id" element={<UserDetailPage />} />
                <Route path="/hierarchy" element={<HierarchyTreePage />} />
                <Route path="/hierarchy/super-admins" element={<UsersListPage fixedRole="SUPER_ADMIN" title="Super Admins" />} />
                <Route path="/hierarchy/masters" element={<UsersListPage fixedRole="MASTER" title="Masters" />} />
                <Route path="/hierarchy/admins" element={<UsersListPage fixedRole="ADMIN" title="Admins" />} />
                <Route path="/hierarchy/agents" element={<UsersListPage fixedRole="AGENT" title="Agents" />} />
                <Route path="/hierarchy/players" element={<UsersListPage fixedRole="USER" title="Players" />} />
                <Route path="/credits/transfer" element={<CreditTransferPage />} />
                <Route path="/credits/requests" element={<CreditRequestsPage />} />
                <Route path="/credits/ledger" element={<LedgerPage />} />
                <Route path="/content/games" element={<GamesPage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/system/settings" element={<SettingsPage />} />
                <Route path="/security/audit" element={<AuditLogsPage />} />
                <Route path="/security/activity" element={<AuditLogsPage />} />
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
        <Toaster />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
