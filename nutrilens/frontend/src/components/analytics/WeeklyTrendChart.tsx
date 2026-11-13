import React, { useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { Flame, Beef, Apple, Sparkles, BarChart3, Info } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { WeeklyAnalyticsResponse } from "@/types";

interface WeeklyTrendChartProps {
  analytics: WeeklyAnalyticsResponse;
}

export const WeeklyTrendChart: React.FC<WeeklyTrendChartProps> = ({ analytics }) => {
  const [activeMetric, setActiveMetric] = useState<"calories" | "macros" | "sugar_sodium" | "fibre">(
    "calories"
  );

  const { daily_trends, averages, active_days, total_logged_meals } = analytics;

  // Chart data formatting
  const chartData = daily_trends.map((d) => ({
    date: d.date.slice(5), // "MM-DD"
    day: d.day_name,
    fullDate: d.date,
    entries: d.entry_count,
    calories: d.calories || 0,
    protein: d.protein_g || 0,
    carbs: d.carbs_g || 0,
    fat: d.fat_g || 0,
    sugar: d.sugar_g || 0,
    sodium: d.sodium_mg || 0,
    fibre: d.fibre_g || 0,
  }));

  if (active_days === 0) {
    return (
      <Card className="border-slate-200 shadow-xs text-center p-8 sm:p-12">
        <CardContent className="space-y-3 max-w-md mx-auto">
          <div className="h-14 w-14 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center mx-auto">
            <BarChart3 className="h-7 w-7" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">No Weekly Log History</h3>
          <p className="text-xs text-slate-500">
            Log your daily meals in the Food Journal to see 7-day longitudinal trends in calories,
            sugar, sodium, and macronutrient intake.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-slate-200 shadow-xs">
      <CardContent className="p-5 sm:p-6 space-y-6">
        {/* Metric Summary Stat Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl">
            <div className="text-[11px] text-slate-500 uppercase font-medium">Logged Meals</div>
            <div className="text-xl font-bold text-slate-900 mt-0.5">{total_logged_meals}</div>
            <div className="text-[10px] text-slate-400">In 7-day window</div>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl">
            <div className="text-[11px] text-slate-500 uppercase font-medium">Active Days</div>
            <div className="text-xl font-bold text-emerald-700 mt-0.5">{active_days} of 7</div>
            <div className="text-[10px] text-slate-400">Logging frequency</div>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl">
            <div className="text-[11px] text-slate-500 uppercase font-medium">Daily Avg Energy</div>
            <div className="text-xl font-bold text-amber-700 mt-0.5">
              {averages.calories != null ? `${averages.calories} kcal` : "N/D"}
            </div>
            <div className="text-[10px] text-slate-400">On active days</div>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl">
            <div className="text-[11px] text-slate-500 uppercase font-medium">Daily Avg Sugar</div>
            <div className="text-xl font-bold text-rose-700 mt-0.5">
              {averages.sugar_g != null ? `${averages.sugar_g}g` : "N/D"}
            </div>
            <div className="text-[10px] text-slate-400">Ref: ≤ 50g/day</div>
          </div>
        </div>

        {/* Metric Switcher Tab Row */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100">
          <div className="text-xs uppercase font-bold text-slate-500 tracking-wider">
            7-Day Nutritional Trends
          </div>

          <div className="flex flex-wrap items-center bg-slate-100 p-1 rounded-xl gap-1 text-xs font-medium">
            <button
              onClick={() => setActiveMetric("calories")}
              className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeMetric === "calories"
                  ? "bg-white text-emerald-900 font-bold shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Flame className="h-3.5 w-3.5 text-amber-500" />
              <span>Calories</span>
            </button>

            <button
              onClick={() => setActiveMetric("macros")}
              className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeMetric === "macros"
                  ? "bg-white text-emerald-900 font-bold shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Beef className="h-3.5 w-3.5 text-indigo-500" />
              <span>Macronutrients</span>
            </button>

            <button
              onClick={() => setActiveMetric("sugar_sodium")}
              className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeMetric === "sugar_sodium"
                  ? "bg-white text-emerald-900 font-bold shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Apple className="h-3.5 w-3.5 text-rose-500" />
              <span>Sugar & Sodium</span>
            </button>

            <button
              onClick={() => setActiveMetric("fibre")}
              className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeMetric === "fibre"
                  ? "bg-white text-emerald-900 font-bold shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Sparkles className="h-3.5 w-3.5 text-teal-500" />
              <span>Fibre</span>
            </button>
          </div>
        </div>

        {/* Recharts Visualizations */}
        <div className="h-72 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            {activeMetric === "calories" ? (
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="calColor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="day" tick={{ fontSize: 12, fill: "#64748b" }} />
                <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
                <Tooltip
                  formatter={(val: any) => [`${val} kcal`, "Energy Intake"]}
                  labelFormatter={(_label, payload) => payload?.[0]?.payload?.fullDate || ""}
                />
                <Area
                  type="monotone"
                  dataKey="calories"
                  stroke="#10b981"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#calColor)"
                  name="Calories (kcal)"
                />
              </AreaChart>
            ) : activeMetric === "macros" ? (
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="day" tick={{ fontSize: 12, fill: "#64748b" }} />
                <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
                <Tooltip
                  formatter={(val: any, name: any) => [`${val}g`, name]}
                  labelFormatter={(_label, payload) => payload?.[0]?.payload?.fullDate || ""}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                <Bar dataKey="protein" fill="#10b981" name="Protein (g)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="carbs" fill="#f59e0b" name="Carbs (g)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="fat" fill="#6366f1" name="Fat (g)" radius={[4, 4, 0, 0]} />
              </BarChart>
            ) : activeMetric === "sugar_sodium" ? (
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="day" tick={{ fontSize: 12, fill: "#64748b" }} />
                <YAxis yAxisId="left" tick={{ fontSize: 12, fill: "#64748b" }} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12, fill: "#64748b" }} />
                <Tooltip
                  labelFormatter={(_label, payload) => payload?.[0]?.payload?.fullDate || ""}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                <Bar
                  yAxisId="left"
                  dataKey="sugar"
                  fill="#f43f5e"
                  name="Total Sugar (g)"
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  yAxisId="right"
                  dataKey="sodium"
                  fill="#0ea5e9"
                  name="Sodium (mg)"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            ) : (
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="fibColor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#14b8a6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="day" tick={{ fontSize: 12, fill: "#64748b" }} />
                <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
                <Tooltip
                  formatter={(val: any) => [`${val}g`, "Dietary Fibre"]}
                  labelFormatter={(_label, payload) => payload?.[0]?.payload?.fullDate || ""}
                />
                <Area
                  type="monotone"
                  dataKey="fibre"
                  stroke="#14b8a6"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#fibColor)"
                  name="Fibre (g)"
                />
              </AreaChart>
            )}
          </ResponsiveContainer>
        </div>

        {/* Non-medical Disclaimer Footer */}
        <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl text-xs text-slate-500 flex items-start gap-2">
          <Info className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{analytics.disclaimer}</span>
        </div>
      </CardContent>
    </Card>
  );
};
