import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  BarChart3,
  Calendar,
  BookMarked,
  ArrowLeft,
  Loader2,
  AlertCircle,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiService } from "@/services/api";
import {
  WeeklyAnalyticsResponse,
  MonthlyAnalyticsResponse,
  FrequentProductItem,
} from "@/types";
import { WeeklyTrendChart } from "@/components/analytics/WeeklyTrendChart";
import { MonthlyTrendChart } from "@/components/analytics/MonthlyTrendChart";
import { FrequentProductsCard } from "@/components/analytics/FrequentProductsCard";
import { LogMealModal } from "@/components/journal/LogMealModal";

export const NutritionAnalyticsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"weekly" | "monthly">("weekly");

  const [weeklyData, setWeeklyData] = useState<WeeklyAnalyticsResponse | null>(null);
  const [monthlyData, setMonthlyData] = useState<MonthlyAnalyticsResponse | null>(null);
  const [frequentProducts, setFrequentProducts] = useState<FrequentProductItem[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Log Modal
  const [isLogModalOpen, setIsLogModalOpen] = useState(false);
  const [prefilledProduct, setPrefilledProduct] = useState<any | null>(null);

  const fetchAnalytics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [weeklyRes, monthlyRes, freqRes] = await Promise.all([
        apiService.getWeeklyAnalytics(),
        apiService.getMonthlyAnalytics(),
        apiService.getFrequentProducts(8),
      ]);
      setWeeklyData(weeklyRes);
      setMonthlyData(monthlyRes);
      setFrequentProducts(freqRes.items);
    } catch (err: any) {
      console.error("Failed to load nutrition analytics:", err);
      setError("Unable to load analytics data. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const handleLogAgain = (prod: any) => {
    setPrefilledProduct(prod);
    setIsLogModalOpen(true);
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-sm text-slate-500 mb-1">
            <Link to="/journal" className="hover:text-emerald-600 flex items-center gap-1">
              <ArrowLeft className="h-4 w-4" /> Back to Food Journal
            </Link>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
            Nutrition Analytics
          </h1>
          <p className="text-sm text-slate-600 mt-0.5">
            Longitudinal intake trends in energy, sugar, sodium, fibre, and macro distributions.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button asChild variant="outline" className="border-slate-200 text-slate-700 hover:bg-slate-50">
            <Link to="/journal" className="flex items-center gap-1.5">
              <BookMarked className="h-4 w-4 text-emerald-600" />
              <span>Food Journal</span>
            </Link>
          </Button>

          <Button
            onClick={() => {
              setPrefilledProduct(null);
              setIsLogModalOpen(true);
            }}
            className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs flex items-center gap-1.5"
          >
            <Plus className="h-4 w-4" />
            <span>Log Meal</span>
          </Button>
        </div>
      </div>

      {/* View Selector Tabs */}
      <div className="flex items-center bg-slate-100 p-1 rounded-xl w-fit text-xs font-semibold">
        <button
          onClick={() => setActiveTab("weekly")}
          className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${
            activeTab === "weekly"
              ? "bg-white text-emerald-900 shadow-xs"
              : "text-slate-600 hover:text-slate-900"
          }`}
        >
          <BarChart3 className="h-4 w-4 text-emerald-600" />
          <span>7-Day Weekly Trends</span>
        </button>

        <button
          onClick={() => setActiveTab("monthly")}
          className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${
            activeTab === "monthly"
              ? "bg-white text-emerald-900 shadow-xs"
              : "text-slate-600 hover:text-slate-900"
          }`}
        >
          <Calendar className="h-4 w-4 text-indigo-600" />
          <span>30-Day Monthly Overview</span>
        </button>
      </div>

      {/* Content Area */}
      {isLoading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-400">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
          <p className="text-sm">Compiling nutritional trends and longitudinal aggregations...</p>
        </div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 flex items-center space-x-3">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <div>
            <div className="font-semibold text-sm">Failed to load analytics</div>
            <div className="text-xs mt-0.5">{error}</div>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Main Chart Section */}
          {activeTab === "weekly" && weeklyData && (
            <WeeklyTrendChart analytics={weeklyData} />
          )}

          {activeTab === "monthly" && monthlyData && (
            <MonthlyTrendChart analytics={monthlyData} />
          )}

          {/* Frequently Consumed Products Card */}
          <FrequentProductsCard
            products={frequentProducts}
            onLogAgain={handleLogAgain}
          />
        </div>
      )}

      {/* Log Modal */}
      <LogMealModal
        isOpen={isLogModalOpen}
        onClose={() => {
          setIsLogModalOpen(false);
          setPrefilledProduct(null);
        }}
        onSuccess={() => fetchAnalytics()}
        initialProduct={prefilledProduct}
      />
    </div>
  );
};
