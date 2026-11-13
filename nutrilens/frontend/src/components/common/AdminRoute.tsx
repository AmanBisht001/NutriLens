import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Loader2, ShieldAlert } from "lucide-react";

export const AdminRoute: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-9 w-9 text-purple-600 animate-spin" />
          <div className="text-sm font-medium text-muted-foreground">
            Verifying administrative privileges...
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const isAdmin = Boolean(
    user?.is_admin || user?.role === "admin" || user?.role === "superadmin"
  );

  if (!isAdmin) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center p-6 text-center">
        <div className="p-4 bg-red-50 text-red-700 rounded-full mb-4 dark:bg-red-950/30 dark:text-red-400">
          <ShieldAlert className="h-12 w-12" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Access Restricted</h2>
        <p className="text-muted-foreground max-w-md mt-2 mb-6">
          You do not have administrative authorization to view this section. Administrative controls are enforced at both API and frontend levels.
        </p>
        <Navigate to="/dashboard" replace />
      </div>
    );
  }

  return <Outlet />;
};
