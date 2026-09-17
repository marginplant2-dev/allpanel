import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getAccessToken } from "@/api/client";
import { useAuthStore } from "@/store/auth";

export function ProtectedRoute() {
  const location = useLocation();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hasToken = !!getAccessToken();

  if (!isAuthenticated && !hasToken) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  return <Outlet />;
}
