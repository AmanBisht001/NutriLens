import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  BookMarked,
  Plus,
  ChevronLeft,
  ChevronRight,
  Calendar,
  BarChart3,
  Loader2,
  AlertCircle,
  Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiService } from "@/services/api";
import { DailyJournalSummaryResponse, JournalEntryItem } from "@/types";
import { DailyNutritionSummaryCard } from "@/components/journal/DailyNutritionSummaryCard";
import { DailyMealSection } from "@/components/journal/DailyMealSection";
import { LogMealModal } from "@/components/journal/LogMealModal";

export const FoodJournalPage: React.FC = () => {
  const location = useLocation();

  // Selected date state (default: today YYYY-MM-DD)
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );

  const [summary, setSummary] = useState<DailyJournalSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [isLogModalOpen, setIsLogModalOpen] = useState<boolean>(false);
  const [editEntry, setEditEntry] = useState<JournalEntryItem | null>(null);
  const [prefilledProduct, setPrefilledProduct] = useState<any | null>(null);

  // Check if directed from product page with product pre-filled in location state
  useEffect(() => {
    if (location.state?.logProduct) {
      setPrefilledProduct(location.state.logProduct);
      setIsLogModalOpen(true);
    }
  }, [location.state]);

  const fetchDailySummary = async (dateStr: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiService.getDailyJournalSummary(dateStr);
      setSummary(data);
    } catch (err: any) {
      console.error("Failed to fetch daily journal summary:", err);
      setError("Unable to load daily journal. Please check your connection.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDailySummary(selectedDate);
  }, [selectedDate]);

  // Date navigation handlers
  const handlePrevDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() - 1);
    setSelectedDate(d.toISOString().split("T")[0]);
  };

  const handleNextDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() + 1);
    setSelectedDate(d.toISOString().split("T")[0]);
  };

  const handleToday = () => {
    setSelectedDate(new Date().toISOString().split("T")[0]);
  };

  const isToday = selectedDate === new Date().toISOString().split("T")[0];

  const formatHeaderDate = (dateStr: string) => {
    try {
      const d = new Date(`${dateStr}T00:00:00`);
      return d.toLocaleDateString(undefined, {
        weekday: "long",
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  // Entry Actions
  const handleOpenAddModal = () => {
    setEditEntry(null);
    setPrefilledProduct(null);
    setIsLogModalOpen(true);
  };

  const handleEditEntry = (entry: JournalEntryItem) => {
    setEditEntry(entry);
    setPrefilledProduct(null);
    setIsLogModalOpen(true);
  };

  const handleDeleteEntry = async (entryId: string) => {
    try {
      await apiService.deleteJournalEntry(entryId);
      fetchDailySummary(selectedDate);
    } catch (err) {
      console.error("Failed to delete entry:", err);
    }
  };

  const handleModalSuccess = () => {
    fetchDailySummary(selectedDate);
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
      {/* Top Header & Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-emerald-700 font-semibold text-xs tracking-wider uppercase mb-1">
            <BookMarked className="h-4 w-4" />
            <span>Actual Consumption Tracking</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
            My Food Journal
          </h1>
          <p className="text-sm text-slate-600 mt-0.5">
            Log consumed food products with proportional nutrient scaling.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button asChild variant="outline" className="border-slate-200 text-slate-700 hover:bg-slate-50">
            <Link to="/analytics" className="flex items-center gap-1.5">
              <BarChart3 className="h-4 w-4 text-emerald-600" />
              <span>Nutrition Analytics</span>
            </Link>
          </Button>

          <Button
            onClick={() => handleOpenAddModal()}
            className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs flex items-center gap-1.5"
          >
            <Plus className="h-4 w-4" />
            <span>Log Food</span>
          </Button>
        </div>
      </div>

      {/* Date Navigation Bar */}
      <div className="bg-white p-3 rounded-2xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-1.5">
          <Button
            variant="ghost"
            size="sm"
            onClick={handlePrevDay}
            className="h-8 w-8 p-0 text-slate-600 hover:bg-slate-100 rounded-lg"
            title="Previous Day"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>

          <div className="flex items-center space-x-2 px-2">
            <Calendar className="h-4 w-4 text-emerald-600" />
            <span className="font-bold text-sm text-slate-900">
              {formatHeaderDate(selectedDate)}
            </span>
            {isToday && (
              <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
                Today
              </span>
            )}
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleNextDay}
            className="h-8 w-8 p-0 text-slate-600 hover:bg-slate-100 rounded-lg"
            title="Next Day"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex items-center space-x-2">
          {!isToday && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleToday}
              className="h-8 text-xs text-slate-700 hover:bg-slate-50"
            >
              Jump to Today
            </Button>
          )}

          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
        </div>
      </div>

      {/* Content Area */}
      {isLoading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-400">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
          <p className="text-sm">Calculating daily consumption and nutrients...</p>
        </div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 flex items-center space-x-3">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <div>
            <div className="font-semibold text-sm">Failed to load journal</div>
            <div className="text-xs mt-0.5">{error}</div>
          </div>
        </div>
      ) : summary ? (
        <div className="space-y-6">
          {/* Daily Nutrition Summary Card */}
          <DailyNutritionSummaryCard summary={summary} />

          {/* Meals Grouping Section */}
          <DailyMealSection
            meals={summary.meals}
            onEditEntry={handleEditEntry}
            onDeleteEntry={handleDeleteEntry}
            onAddMeal={(_mealType) => {
              setPrefilledProduct(null);
              setEditEntry(null);
              setIsLogModalOpen(true);
            }}
          />

          {/* Empty state notice if 0 entries on this day */}
          {summary.total_entries === 0 && (
            <Card className="border-dashed border-2 border-slate-200 text-center p-8 bg-slate-50/50">
              <CardContent className="space-y-3 max-w-sm mx-auto">
                <div className="h-12 w-12 rounded-2xl bg-emerald-100/70 text-emerald-700 flex items-center justify-center mx-auto">
                  <Clock className="h-6 w-6" />
                </div>
                <h3 className="text-base font-bold text-slate-900">
                  No Meals Logged for {isToday ? "Today" : "This Day"}
                </h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  NutriLens keeps scanning separate from actual consumption. Log what you actually ate to track daily nutrients.
                </p>
                <Button
                  onClick={() => handleOpenAddModal()}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs"
                >
                  <Plus className="h-3.5 w-3.5 mr-1" />
                  Log Your First Item
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      ) : null}

      {/* Log / Edit Meal Modal */}
      <LogMealModal
        isOpen={isLogModalOpen}
        onClose={() => {
          setIsLogModalOpen(false);
          setEditEntry(null);
          setPrefilledProduct(null);
        }}
        onSuccess={handleModalSuccess}
        initialProduct={prefilledProduct}
        editEntry={editEntry}
        defaultDate={selectedDate}
      />
    </div>
  );
};
