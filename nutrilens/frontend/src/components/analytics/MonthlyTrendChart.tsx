import React, { useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { Calendar } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { MonthlyAnalyticsResponse } from "@/types";

interface MonthlyTrendChartProps {
  analytics: MonthlyAnalyticsResponse;
}

export const MonthlyTrendChart: React.FC<MonthlyTrendChartProps> = ({ analytics }) => {
  const [selectedMetric, setSelectedMetric] = useState<"calories" | "sugar" | "sodium">("calories");
  const { daily_trends, averages, active_days, total_logged_meals } = analytics;

  const chartData = daily_trends.map((d) => ({
    date: d.date.slice(5),
    day: d.date.slice(8), // day number
    fullDate: d.date,
    entries: d.entry_count,
    calories: d.calories || 0,
    sugar: d.sugar_g || 0,
    sodium: d.sodium_mg || 0,
  }));

  if (active_days === 0) {
    return (
      <Card className="border-slate-200 shadow-xs text-center p-8 sm:p-12">
        <CardContent className="space-y-3 max-w-md mx-auto">
          <div className="h-14 w-14 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center mx-auto">
            <Calendar className="h-7 w-7" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">No Monthly Log History</h3>
          <p className="text-xs text-slate-500">
            No consumption logs recorded for this 30-day period. As you log your packaged meals,
            monthly patterns and nutrient distributions will be charted here.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-slate-200 shadow-xs">
      <CardContent className="p-5 sm:p-6 space-y-6">
        {/* Monthly Summary Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <div className="text-[11px] text-slate-500 uppercase font-medium">Monthly Meals</div>
            <div className="text-xl font-bold text-slate-900 mt-0.5">{total_logged_meals}</div>
            <div className="text-[10px] text-slate-400">Total logs</div>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <div className="text-[11px] text-slate-500 uppercase font-medium">Logged Days</div>
            <div className="text-xl font-bold text-emerald-700 mt-0.5">{active_days} days</div>
            <div className="text-[10px] text-slate-400">With recorded meals</div>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <div className="text-[11px] text-slate-500 uppercase font-medium">Month Avg Calories</div>
            <div className="text-xl font-bold text-amber-700 mt-0.5">
              {averages.calories != null ? `${averages.calories} kcal` : "N/D"}
            </div>
            <div className="text-[10px] text-slate-400">On active days</div>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <div className="text-[11px] text-slate-500 uppercase font-medium">Month Avg Sugar</div>
            <div className="text-xl font-bold text-rose-700 mt-0.5">
              {averages.sugar_g != null ? `${averages.sugar_g}g` : "N/D"}
            </div>
            <div className="text-[10px] text-slate-400">Per logged day</div>
          </div>
        </div>

        {/* Metric Selector */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100">
          <div className="text-xs uppercase font-bold text-slate-500 tracking-wider">
            30-Day Intake Distribution
          </div>

          <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs font-medium gap-1">
            <button
              onClick={() => setSelectedMetric("calories")}
              className={`px-3 py-1 rounded-lg transition-colors ${
                selectedMetric === "calories"
                  ? "bg-white text-emerald-900 font-bold shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Calories
            </button>
            <button
              onClick={() => setSelectedMetric("sugar")}
              className={`px-3 py-1 rounded-lg transition-colors ${
                selectedMetric === "sugar"
                  ? "bg-white text-emerald-900 font-bold shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Sugar
            </button>
            <button
              onClick={() => setSelectedMetric("sodium")}
              className={`px-3 py-1 rounded-lg transition-colors ${
                selectedMetric === "sodium"
                  ? "bg-white text-emerald-900 font-bold shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Sodium
            </button>
          </div>
        </div>

        {/* 30-Day Bar Chart */}
        <div className="h-64 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="day" tick={{ fontSize: 11, fill: "#64748b" }} interval={2} />
              <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
              <Tooltip
                formatter={(val: any) => [
                  selectedMetric === "calories"
                    ? `${val} kcal`
                    : selectedMetric === "sugar"
                    ? `${val}g`
                    : `${val}mg`,
                  selectedMetric === "calories" ? "Calories" : selectedMetric === "sugar" ? "Sugar" : "Sodium",
                ]}
                labelFormatter={(_label, payload) => payload?.[0]?.payload?.fullDate || ""}
              />
              <Bar
                dataKey={selectedMetric}
                fill={selectedMetric === "calories" ? "#10b981" : selectedMetric === "sugar" ? "#f43f5e" : "#0ea5e9"}
                radius={[3, 3, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
