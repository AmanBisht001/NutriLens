import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/context/AuthContext";
import { RootLayout } from "@/layouts/RootLayout";
import { AppLayout } from "@/layouts/AppLayout";
import { ProtectedRoute } from "@/components/common/ProtectedRoute";
import { AdminRoute } from "@/components/common/AdminRoute";

import { HomePage } from "@/pages/HomePage";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { ScanFoodPage } from "@/pages/ScanFoodPage";
import { FoodCataloguePage } from "@/pages/FoodCataloguePage";
import { ProductDetailPage } from "@/pages/ProductDetailPage";
import { CompareProductsPage } from "@/pages/CompareProductsPage";
import { FoodJournalPage } from "@/pages/FoodJournalPage";
import { NutritionAnalyticsPage } from "@/pages/NutritionAnalyticsPage";
import { AdminDashboardPage } from "@/pages/AdminDashboardPage";
import { AdminProductsPage } from "@/pages/AdminProductsPage";
import { AdminIngredientsPage } from "@/pages/AdminIngredientsPage";
import { AdminScoringRulesPage } from "@/pages/AdminScoringRulesPage";
import { AdminIssuesPage } from "@/pages/AdminIssuesPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public Landing & Informational Layout */}
            <Route path="/" element={<RootLayout />}>
              <Route index element={<HomePage />} />
            </Route>

            {/* Authentication Pages */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Authenticated Application Shell */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/scan" element={<ScanFoodPage />} />
                <Route path="/catalogue" element={<FoodCataloguePage />} />
                <Route path="/catalogue/:id" element={<ProductDetailPage />} />
                <Route path="/compare" element={<CompareProductsPage />} />
                <Route path="/journal" element={<FoodJournalPage />} />
                <Route path="/analytics" element={<NutritionAnalyticsPage />} />

                {/* Day 9 Role-Protected Admin Routes */}
                <Route element={<AdminRoute />}>
                  <Route path="/admin" element={<AdminDashboardPage />} />
                  <Route path="/admin/products" element={<AdminProductsPage />} />
                  <Route path="/admin/ingredients" element={<AdminIngredientsPage />} />
                  <Route path="/admin/scoring-rules" element={<AdminScoringRulesPage />} />
                  <Route path="/admin/issues" element={<AdminIssuesPage />} />
                </Route>
              </Route>
            </Route>

            {/* Catch-all 404 Route */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
