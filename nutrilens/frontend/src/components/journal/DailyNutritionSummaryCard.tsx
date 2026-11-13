import React from "react";
import {
  Flame,
  Wheat,
  Beef,
  Droplet,
  ShieldCheck,
  AlertTriangle,
  Info,
  CheckCircle2,
  Sparkles,
  HelpCircle,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DailyJournalSummaryResponse } from "@/types";

interface DailyNutritionSummaryCardProps {
  summary: DailyJournalSummaryResponse;
}

export const DailyNutritionSummaryCard: React.FC<DailyNutritionSummaryCardProps> = ({
  summary,
}) => {
  const calories = summary.totals["energy_kcal"]?.total || 0;
  const protein = summary.totals["protein_g"]?.total;
  const carbs = summary.totals["carbohydrates_g"]?.total;
  const fat = summary.totals["total_fat_g"]?.total;
  const sugar = summary.totals["total_sugar_g"]?.total;
  const sodium = summary.totals["sodium_mg"]?.total;
  const fibre = summary.totals["dietary_fibre_g"]?.total;
  const satFat = summary.totals["saturated_fat_g"]?.total;

  // Reference calorie baseline for progress ring/bar (standard 2,000 kcal general adult intake)
  const calPercent = Math.min(100, Math.round((calories / 2000) * 100));

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "on_track":
        return (
          <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200 text-xs font-semibold">
            <CheckCircle2 className="h-3 w-3 mr-1" /> On Track
          </Badge>
        );
      case "caution":
        return (
          <Badge className="bg-amber-100 text-amber-800 border-amber-200 text-xs font-semibold">
            <AlertTriangle className="h-3 w-3 mr-1" /> Caution
          </Badge>
        );
      case "exceeded":
        return (
          <Badge className="bg-rose-100 text-rose-800 border-rose-200 text-xs font-semibold">
            <AlertTriangle className="h-3 w-3 mr-1" /> Exceeded
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="text-slate-600 bg-slate-50 text-xs">
            <Info className="h-3 w-3 mr-1" /> Notice
          </Badge>
        );
    }
  };

  return (
    <Card className="border-slate-200 shadow-xs overflow-hidden">
      <CardContent className="p-5 sm:p-6 space-y-6">
        {/* Top Header Row: Calories & Total Weight */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-3.5">
            <div className="h-12 w-12 rounded-2xl bg-amber-500/10 border border-amber-200/60 text-amber-600 flex items-center justify-center shrink-0">
              <Flame className="h-6 w-6 fill-amber-500 text-amber-500" />
            </div>
            <div>
              <div className="text-xs uppercase font-bold text-slate-500 tracking-wider">
                Daily Energy Intake
              </div>
              <div className="flex items-baseline space-x-2">
                <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                  {calories}
                </span>
                <span className="text-sm font-semibold text-slate-500">kcal</span>
                <span className="text-xs text-slate-400">
                  (~{calPercent}% of 2,000 kcal standard reference)
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl text-center">
              <span className="text-[11px] text-slate-500 uppercase font-medium block">
                Total Consumed
              </span>
              <span className="font-bold text-slate-900 text-sm">
                {summary.total_weight_g}g
              </span>
            </div>
            <div className="bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl text-center">
              <span className="text-[11px] text-slate-500 uppercase font-medium block">
                Logged Foods
              </span>
              <span className="font-bold text-emerald-700 text-sm">
                {summary.total_entries} {summary.total_entries === 1 ? "item" : "items"}
              </span>
            </div>
          </div>
        </div>

        {/* Calorie Progress Bar */}
        <div className="space-y-1">
          <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                calPercent > 100
                  ? "bg-rose-500"
                  : calPercent > 85
                  ? "bg-amber-500"
                  : "bg-emerald-500"
              }`}
              style={{ width: `${Math.min(100, calPercent)}%` }}
            />
          </div>
        </div>

        {/* Core Macronutrients Grid */}
        <div>
          <div className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2.5">
            Core Macronutrients
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {/* Protein */}
            <div className="p-3 bg-emerald-50/50 border border-emerald-100 rounded-xl">
              <div className="flex items-center justify-between text-xs text-emerald-800 font-medium mb-1">
                <span className="flex items-center gap-1">
                  <Beef className="h-3.5 w-3.5 text-emerald-600" /> Protein
                </span>
              </div>
              <div className="text-lg font-bold text-slate-900">
                {protein != null ? `${protein}g` : "N/D"}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                {summary.totals["protein_g"]?.declared_items || 0} of {summary.total_entries} items
              </div>
            </div>

            {/* Carbohydrates */}
            <div className="p-3 bg-amber-50/50 border border-amber-100 rounded-xl">
              <div className="flex items-center justify-between text-xs text-amber-800 font-medium mb-1">
                <span className="flex items-center gap-1">
                  <Wheat className="h-3.5 w-3.5 text-amber-600" /> Carbs
                </span>
              </div>
              <div className="text-lg font-bold text-slate-900">
                {carbs != null ? `${carbs}g` : "N/D"}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                {summary.totals["carbohydrates_g"]?.declared_items || 0} of {summary.total_entries} items
              </div>
            </div>

            {/* Total Fat */}
            <div className="p-3 bg-indigo-50/50 border border-indigo-100 rounded-xl">
              <div className="flex items-center justify-between text-xs text-indigo-800 font-medium mb-1">
                <span className="flex items-center gap-1">
                  <Droplet className="h-3.5 w-3.5 text-indigo-600" /> Fat
                </span>
              </div>
              <div className="text-lg font-bold text-slate-900">
                {fat != null ? `${fat}g` : "N/D"}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                {summary.totals["total_fat_g"]?.declared_items || 0} of {summary.total_entries} items
              </div>
            </div>

            {/* Dietary Fibre */}
            <div className="p-3 bg-teal-50/50 border border-teal-100 rounded-xl">
              <div className="flex items-center justify-between text-xs text-teal-800 font-medium mb-1">
                <span className="flex items-center gap-1">
                  <Sparkles className="h-3.5 w-3.5 text-teal-600" /> Fibre
                </span>
              </div>
              <div className="text-lg font-bold text-slate-900">
                {fibre != null ? `${fibre}g` : "N/D"}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                {summary.totals["dietary_fibre_g"]?.declared_items || 0} of {summary.total_entries} items
              </div>
            </div>
          </div>
        </div>

        {/* Monitored Micronutrients & Guardrails */}
        <div className="pt-2 border-t border-slate-100">
          <div className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2.5">
            Key Dietary Guardrails
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Sugar */}
            <div className="p-3 bg-white border border-slate-200 rounded-xl">
              <div className="flex items-center justify-between text-xs text-slate-600 mb-1">
                <span className="font-semibold text-slate-800">Total Sugar</span>
                <span className="text-[10px] text-slate-400">Ref: ≤ 50g/day</span>
              </div>
              <div className="text-base font-bold text-slate-900">
                {sugar != null ? `${sugar}g` : "Not Declared"}
              </div>
              <div className="text-[10px] text-slate-500 mt-1">
                {summary.totals["total_sugar_g"]?.missing_items > 0 ? (
                  <span className="text-amber-700 flex items-center gap-1">
                    <HelpCircle className="h-3 w-3" />
                    {summary.totals["total_sugar_g"].missing_items} item undeclared
                  </span>
                ) : (
                  <span>All items declared</span>
                )}
              </div>
            </div>

            {/* Sodium */}
            <div className="p-3 bg-white border border-slate-200 rounded-xl">
              <div className="flex items-center justify-between text-xs text-slate-600 mb-1">
                <span className="font-semibold text-slate-800">Sodium</span>
                <span className="text-[10px] text-slate-400">Ref: ≤ 2,000mg</span>
              </div>
              <div className="text-base font-bold text-slate-900">
                {sodium != null ? `${sodium}mg` : "Not Declared"}
              </div>
              <div className="text-[10px] text-slate-500 mt-1">
                {summary.totals["sodium_mg"]?.missing_items > 0 ? (
                  <span className="text-amber-700 flex items-center gap-1">
                    <HelpCircle className="h-3 w-3" />
                    {summary.totals["sodium_mg"].missing_items} item undeclared
                  </span>
                ) : (
                  <span>All items declared</span>
                )}
              </div>
            </div>

            {/* Saturated Fat */}
            <div className="p-3 bg-white border border-slate-200 rounded-xl">
              <div className="flex items-center justify-between text-xs text-slate-600 mb-1">
                <span className="font-semibold text-slate-800">Saturated Fat</span>
                <span className="text-[10px] text-slate-400">Ref: ≤ 20g/day</span>
              </div>
              <div className="text-base font-bold text-slate-900">
                {satFat != null ? `${satFat}g` : "Not Declared"}
              </div>
              <div className="text-[10px] text-slate-500 mt-1">
                {summary.totals["saturated_fat_g"]?.missing_items > 0 ? (
                  <span className="text-amber-700 flex items-center gap-1">
                    <HelpCircle className="h-3 w-3" />
                    {summary.totals["saturated_fat_g"].missing_items} item undeclared
                  </span>
                ) : (
                  <span>All items declared</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Nutritional Goal Progress (When Configured) */}
        {summary.goal_progress && summary.goal_progress.length > 0 && (
          <div className="pt-2 border-t border-slate-100 space-y-2.5">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              <span className="text-xs uppercase font-bold text-slate-700 tracking-wider">
                Personal Nutrition Goal Progress
              </span>
            </div>

            <div className="space-y-2">
              {summary.goal_progress.map((gp) => (
                <div
                  key={gp.goal_key}
                  className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-slate-900">
                        {gp.goal_label}
                      </span>
                      {getStatusBadge(gp.status)}
                    </div>
                    <p className="text-xs text-slate-600">{gp.message}</p>
                  </div>

                  {gp.current_value != null && (
                    <div className="text-xs font-medium text-slate-500 shrink-0 self-end sm:self-center">
                      Logged: <strong className="text-slate-800">{gp.current_value}{gp.unit}</strong>
                      {gp.target_benchmark && (
                        <span> / Ref: {gp.target_benchmark}{gp.unit}</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Non-Medical Disclaimer */}
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-500 flex items-start space-x-2">
          <Info className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{summary.disclaimer}</span>
        </div>
      </CardContent>
    </Card>
  );
};
