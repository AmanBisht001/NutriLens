import React, { useState } from "react";
import {
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Info,
  ChevronDown,
  ChevronUp,
  Scale,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { NutritionAnalysis } from "@/types";

interface NutritionScoreAnalysisCardProps {
  analysis?: NutritionAnalysis | null;
  servingSize?: string | null;
}

export const NutritionScoreAnalysisCard: React.FC<NutritionScoreAnalysisCardProps> = ({
  analysis,
  servingSize,
}) => {
  // Toggle between per-100g/ml and per-serving view
  const [viewMode, setViewMode] = useState<"per_100" | "per_serving">("per_100");
  const [showExplanationBreakdown, setShowExplanationBreakdown] = useState<boolean>(false);

  if (!analysis) {
    return (
      <Card className="border-slate-200 shadow-sm p-6 text-center text-slate-500 text-xs">
        Nutritional score analysis is currently unavailable for this item.
      </Card>
    );
  }

  const isLiquid = analysis.standard_unit === "per_100ml";
  const standardUnitLabel = isLiquid ? "Per 100ml" : "Per 100g";
  const servingUnitLabel = analysis.serving_size_info.raw_text
    ? `Per Serving (${analysis.serving_size_info.raw_text})`
    : servingSize
    ? `Per Serving (${servingSize})`
    : "Per Serving";

  const activeValues =
    viewMode === "per_serving" ? analysis.per_serving_values : analysis.per_100_values;

  // Grade badge styling helper
  const getScoreTheme = (color: string) => {
    switch (color) {
      case "emerald":
        return {
          bg: "bg-emerald-500",
          lightBg: "bg-emerald-50",
          border: "border-emerald-200",
          text: "text-emerald-800",
          badge: "bg-emerald-100 text-emerald-900 border-emerald-300",
          ring: "ring-emerald-500/20",
        };
      case "green":
        return {
          bg: "bg-green-500",
          lightBg: "bg-green-50",
          border: "border-green-200",
          text: "text-green-800",
          badge: "bg-green-100 text-green-900 border-green-300",
          ring: "ring-green-500/20",
        };
      case "amber":
        return {
          bg: "bg-amber-500",
          lightBg: "bg-amber-50",
          border: "border-amber-200",
          text: "text-amber-800",
          badge: "bg-amber-100 text-amber-900 border-amber-300",
          ring: "ring-amber-500/20",
        };
      case "orange":
        return {
          bg: "bg-orange-500",
          lightBg: "bg-orange-50",
          border: "border-orange-200",
          text: "text-orange-800",
          badge: "bg-orange-100 text-orange-900 border-orange-300",
          ring: "ring-orange-500/20",
        };
      case "rose":
        return {
          bg: "bg-rose-500",
          lightBg: "bg-rose-50",
          border: "border-rose-200",
          text: "text-rose-800",
          badge: "bg-rose-100 text-rose-900 border-rose-300",
          ring: "ring-rose-500/20",
        };
      default:
        return {
          bg: "bg-slate-400",
          lightBg: "bg-slate-50",
          border: "border-slate-200",
          text: "text-slate-800",
          badge: "bg-slate-100 text-slate-800 border-slate-300",
          ring: "ring-slate-400/20",
        };
    }
  };

  const theme = getScoreTheme(analysis.rating_color);

  // -------------------------------------------------------------------------
  // Render: INSUFFICIENT DATA STATE (No manufactured score)
  // -------------------------------------------------------------------------
  if (analysis.status === "insufficient_data") {
    return (
      <Card className="border-amber-200 shadow-sm overflow-hidden">
        <CardHeader className="bg-amber-50/60 pb-3 border-b border-amber-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center">
                <AlertTriangle className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base font-bold text-amber-950">
                  NutriLens Nutrition Score: Insufficient Data
                </CardTitle>
                <CardDescription className="text-xs text-amber-800/80">
                  Score withheld to protect data integrity and avoid manufactured estimates.
                </CardDescription>
              </div>
            </div>
            <Badge variant="outline" className="text-[11px] bg-white border-amber-300 text-amber-900 font-mono">
              Rule: {analysis.scoring_rule_version}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-5 space-y-4">
          <div className="p-3.5 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900 space-y-2">
            <p className="font-semibold flex items-center gap-1.5">
              <Info className="h-4 w-4 text-amber-700 flex-shrink-0" />
              Critical Macronutrients Missing:
            </p>
            <div className="flex flex-wrap gap-1.5 pl-5">
              {analysis.missing_critical_fields.map((field) => (
                <span
                  key={field}
                  className="px-2 py-0.5 rounded bg-white border border-amber-300 font-mono text-[11px] text-amber-900 font-medium"
                >
                  {field}
                </span>
              ))}
            </div>
            <p className="text-[11px] text-amber-800/90 pl-5">
              NutriLens requires complete declarations for Energy, Sugar, Saturated Fat, Total Fat, Protein, and Sodium before calculating a verified nutritional rating.
            </p>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-600 pt-1">
            <span>Label Data Completeness:</span>
            <div className="flex items-center gap-2">
              <div className="w-28 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-500 rounded-full"
                  style={{ width: `${analysis.data_completeness_pct}%` }}
                />
              </div>
              <span className="font-semibold">{analysis.data_completeness_pct}%</span>
            </div>
          </div>

          <p className="text-[10px] text-slate-400 italic pt-2 border-t border-slate-100">
            {analysis.disclaimer}
          </p>
        </CardContent>
      </Card>
    );
  }

  // -------------------------------------------------------------------------
  // Render: COMPLETE NUTRITION SCORE & ANALYSIS
  // -------------------------------------------------------------------------
  return (
    <Card className="border-slate-200 shadow-sm overflow-hidden">
      {/* Score Header & Visualization Banner */}
      <CardHeader className="bg-gradient-to-br from-slate-50 to-white pb-4 border-b border-slate-100">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs bg-white text-emerald-800 border-emerald-200 font-medium flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-emerald-600" /> NutriLens Nutrition Score
              </Badge>
              <Badge variant="outline" className="text-[10px] text-slate-500 border-slate-200 font-mono">
                {analysis.scoring_rule_version}
              </Badge>
            </div>
            <CardTitle className="text-lg font-bold text-slate-900">
              Nutritional Profile & Score Analysis
            </CardTitle>
            <CardDescription className="text-xs text-slate-600">
              Deterministic, category-calibrated evaluation based on normalized label values.
            </CardDescription>
          </div>

          {/* Main Score Visual Pill */}
          <div className="flex items-center gap-3 bg-white p-3 rounded-2xl border border-slate-200 shadow-xs self-start sm:self-auto">
            <div
              className={`h-14 w-14 rounded-xl ${theme.bg} text-white flex flex-col items-center justify-center font-extrabold shadow-sm`}
            >
              <span className="text-xl leading-none">{analysis.score}</span>
              <span className="text-[9px] uppercase tracking-wider font-semibold opacity-90">
                / 100
              </span>
            </div>

            <div className="space-y-0.5">
              <div className="flex items-center gap-1.5">
                <span className={`text-xs font-bold uppercase tracking-wide ${theme.text}`}>
                  Grade {analysis.grade}
                </span>
                <span className="text-slate-300">•</span>
                <span className="text-xs font-semibold text-slate-700">
                  {analysis.rating_label}
                </span>
              </div>
              <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden mt-1">
                <div
                  className={`h-full ${theme.bg} rounded-full transition-all duration-500`}
                  style={{ width: `${analysis.score}%` }}
                />
              </div>
              <p className="text-[10px] text-slate-400">
                {analysis.data_completeness_pct}% Data Complete
              </p>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-5 space-y-6">
        {/* Narrative Summary */}
        <div className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200/80 text-xs text-slate-700 leading-relaxed">
          <strong className="text-slate-900 font-semibold block mb-0.5">Summary:</strong>
          {analysis.nutrition_summary}
        </div>

        {/* Positive & Negative Factors Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Positive Factors */}
          <div className="p-4 rounded-xl border border-emerald-100 bg-emerald-50/40 space-y-2.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-900 uppercase tracking-wider">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>Positive Nutritional Factors</span>
            </div>
            {analysis.positive_factors.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No significant positive bonuses detected.</p>
            ) : (
              <ul className="space-y-2">
                {analysis.positive_factors.map((factor, idx) => (
                  <li key={idx} className="flex items-start justify-between text-xs gap-2">
                    <span className="text-slate-700 leading-tight">
                      <strong className="text-emerald-950 font-semibold">{factor.factor}:</strong>{" "}
                      {factor.description}
                    </span>
                    <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 text-[10px] px-1.5 py-0 font-mono flex-shrink-0">
                      {factor.impact}
                    </Badge>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Attention Factors (Negatives) */}
          <div className="p-4 rounded-xl border border-amber-100 bg-amber-50/40 space-y-2.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900 uppercase tracking-wider">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <span>Factors Requiring Attention</span>
            </div>
            {analysis.attention_factors.length === 0 ? (
              <p className="text-xs text-emerald-700 italic flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" /> No high-risk nutrient penalties incurred.
              </p>
            ) : (
              <ul className="space-y-2">
                {analysis.attention_factors.map((factor, idx) => (
                  <li key={idx} className="flex items-start justify-between text-xs gap-2">
                    <span className="text-slate-700 leading-tight">
                      <strong className="text-amber-950 font-semibold">{factor.factor}:</strong>{" "}
                      {factor.description}
                    </span>
                    <Badge className="bg-rose-50 text-rose-800 border-rose-200 text-[10px] px-1.5 py-0 font-mono flex-shrink-0">
                      {factor.impact}
                    </Badge>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Nutritional Information with Per-100g vs Per-Serving Toggle */}
        <div className="space-y-3 pt-2 border-t border-slate-100">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                <Scale className="h-3.5 w-3.5 text-emerald-600" />
                Nutritional Breakdown & Qualitative Levels
              </h4>
              <p className="text-[11px] text-slate-500">
                Values normalized and calculated deterministically.
              </p>
            </div>

            {/* Toggle Buttons */}
            <div className="inline-flex rounded-lg p-0.5 bg-slate-100 border border-slate-200 text-xs self-start sm:self-auto">
              <button
                type="button"
                onClick={() => setViewMode("per_100")}
                className={`px-3 py-1 rounded-md font-medium text-xs transition-all ${
                  viewMode === "per_100"
                    ? "bg-white text-emerald-800 shadow-2xs font-semibold"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {standardUnitLabel}
              </button>
              <button
                type="button"
                onClick={() => setViewMode("per_serving")}
                disabled={!analysis.serving_size_info.quantity}
                className={`px-3 py-1 rounded-md font-medium text-xs transition-all ${
                  viewMode === "per_serving"
                    ? "bg-white text-emerald-800 shadow-2xs font-semibold"
                    : "text-slate-600 hover:text-slate-900 disabled:opacity-50 disabled:cursor-not-allowed"
                }`}
              >
                {servingUnitLabel}
              </button>
            </div>
          </div>

          {/* Nutrient Cards Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5">
            {/* Calories */}
            <div className="p-2.5 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
              <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block">
                Energy
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-base font-bold text-slate-900">
                  {activeValues.energy_kcal ?? "—"}
                </span>
                <span className="text-[10px] text-slate-400">kcal</span>
              </div>
              <Badge variant="outline" className="text-[9px] py-0 px-1.5 font-medium border-slate-200 text-slate-600">
                {analysis.nutrient_evaluations.energy_kcal?.level || "neutral"}
              </Badge>
            </div>

            {/* Total Sugar */}
            <div className="p-2.5 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
              <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block">
                Total Sugar
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-base font-bold text-slate-900">
                  {activeValues.total_sugar_g ?? "—"}
                </span>
                <span className="text-[10px] text-slate-400">g</span>
              </div>
              <Badge
                variant="outline"
                className={`text-[9px] py-0 px-1.5 font-medium capitalize ${
                  analysis.nutrient_evaluations.total_sugar_g?.level === "high"
                    ? "bg-rose-50 text-rose-800 border-rose-200"
                    : analysis.nutrient_evaluations.total_sugar_g?.level === "low"
                    ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                    : "bg-slate-100 text-slate-700 border-slate-200"
                }`}
              >
                {analysis.nutrient_evaluations.total_sugar_g?.level || "moderate"} sugar
              </Badge>
            </div>

            {/* Saturated Fat */}
            <div className="p-2.5 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
              <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block">
                Saturated Fat
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-base font-bold text-slate-900">
                  {activeValues.saturated_fat_g ?? "—"}
                </span>
                <span className="text-[10px] text-slate-400">g</span>
              </div>
              <Badge
                variant="outline"
                className={`text-[9px] py-0 px-1.5 font-medium capitalize ${
                  analysis.nutrient_evaluations.saturated_fat_g?.level === "high"
                    ? "bg-rose-50 text-rose-800 border-rose-200"
                    : analysis.nutrient_evaluations.saturated_fat_g?.level === "low"
                    ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                    : "bg-slate-100 text-slate-700 border-slate-200"
                }`}
              >
                {analysis.nutrient_evaluations.saturated_fat_g?.level || "moderate"} sat fat
              </Badge>
            </div>

            {/* Sodium */}
            <div className="p-2.5 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
              <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block">
                Sodium
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-base font-bold text-slate-900">
                  {activeValues.sodium_mg ?? "—"}
                </span>
                <span className="text-[10px] text-slate-400">mg</span>
              </div>
              <Badge
                variant="outline"
                className={`text-[9px] py-0 px-1.5 font-medium capitalize ${
                  analysis.nutrient_evaluations.sodium_mg?.level === "high"
                    ? "bg-rose-50 text-rose-800 border-rose-200"
                    : analysis.nutrient_evaluations.sodium_mg?.level === "low"
                    ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                    : "bg-slate-100 text-slate-700 border-slate-200"
                }`}
              >
                {analysis.nutrient_evaluations.sodium_mg?.level || "moderate"} sodium
              </Badge>
            </div>

            {/* Dietary Fibre */}
            <div className="p-2.5 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
              <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block">
                Dietary Fibre
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-base font-bold text-slate-900">
                  {activeValues.dietary_fibre_g ?? "—"}
                </span>
                <span className="text-[10px] text-slate-400">g</span>
              </div>
              <Badge
                variant="outline"
                className={`text-[9px] py-0 px-1.5 font-medium ${
                  (activeValues.dietary_fibre_g || 0) >= 6
                    ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                    : (activeValues.dietary_fibre_g || 0) >= 3
                    ? "bg-green-50 text-green-800 border-green-200"
                    : "bg-slate-100 text-slate-600 border-slate-200"
                }`}
              >
                {(activeValues.dietary_fibre_g || 0) >= 3 ? "Good source" : "Low fibre"}
              </Badge>
            </div>

            {/* Protein */}
            <div className="p-2.5 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
              <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block">
                Protein
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-base font-bold text-slate-900">
                  {activeValues.protein_g ?? "—"}
                </span>
                <span className="text-[10px] text-slate-400">g</span>
              </div>
              <Badge
                variant="outline"
                className={`text-[9px] py-0 px-1.5 font-medium ${
                  (activeValues.protein_g || 0) >= 10
                    ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                    : (activeValues.protein_g || 0) >= 5
                    ? "bg-green-50 text-green-800 border-green-200"
                    : "bg-slate-100 text-slate-600 border-slate-200"
                }`}
              >
                {(activeValues.protein_g || 0) >= 5 ? "Protein source" : "Standard"}
              </Badge>
            </div>

            {/* Trans Fat */}
            <div className="p-2.5 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
              <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block">
                Trans Fat
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-base font-bold text-slate-900">
                  {activeValues.trans_fat_g ?? "0.0"}
                </span>
                <span className="text-[10px] text-slate-400">g</span>
              </div>
              <Badge
                variant="outline"
                className={`text-[9px] py-0 px-1.5 font-medium ${
                  (activeValues.trans_fat_g || 0) > 0
                    ? "bg-rose-100 text-rose-900 border-rose-300 font-semibold"
                    : "bg-emerald-50 text-emerald-800 border-emerald-200"
                }`}
              >
                {(activeValues.trans_fat_g || 0) > 0 ? "Warning: Contains Trans Fat" : "Zero Trans Fat"}
              </Badge>
            </div>

            {/* Total Fat */}
            <div className="p-2.5 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
              <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block">
                Total Fat
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-base font-bold text-slate-900">
                  {activeValues.total_fat_g ?? "—"}
                </span>
                <span className="text-[10px] text-slate-400">g</span>
              </div>
              <span className="text-[9px] text-slate-400 block truncate">
                Carbs: {activeValues.carbohydrates_g ?? "—"}g
              </span>
            </div>
          </div>
        </div>

        {/* Explainable Scoring Breakdown Accordion */}
        <div className="border border-slate-200 rounded-xl overflow-hidden">
          <button
            type="button"
            onClick={() => setShowExplanationBreakdown(!showExplanationBreakdown)}
            className="w-full p-3 bg-slate-50 hover:bg-slate-100/80 text-xs font-semibold text-slate-800 flex items-center justify-between transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <Info className="h-3.5 w-3.5 text-slate-500" />
              How was this score calculated? (Transparent Scoring Breakdown)
            </span>
            {showExplanationBreakdown ? (
              <ChevronUp className="h-4 w-4 text-slate-500" />
            ) : (
              <ChevronDown className="h-4 w-4 text-slate-500" />
            )}
          </button>

          {showExplanationBreakdown && (
            <div className="p-4 bg-white text-xs space-y-3 border-t border-slate-200">
              <p className="text-slate-600 leading-relaxed">
                {analysis.score_explanation}
              </p>

              {analysis.score_breakdown && (
                <div className="bg-slate-50 p-3 rounded-lg font-mono text-[11px] space-y-1.5 text-slate-700">
                  <div className="flex justify-between font-bold text-slate-900 border-b border-slate-200 pb-1">
                    <span>Base Neutral Baseline:</span>
                    <span>+{analysis.score_breakdown.base_score} pts</span>
                  </div>

                  {Object.entries(analysis.score_breakdown.penalties).map(([key, val]) => (
                    <div key={key} className="flex justify-between text-rose-700">
                      <span>• Penalty ({key}):</span>
                      <span>-{val} pts</span>
                    </div>
                  ))}

                  {Object.entries(analysis.score_breakdown.bonuses).map(([key, val]) => (
                    <div key={key} className="flex justify-between text-emerald-700">
                      <span>• Bonus ({key}):</span>
                      <span>+{val} pts</span>
                    </div>
                  ))}

                  <div className="flex justify-between font-bold text-slate-900 border-t border-slate-200 pt-1 text-xs">
                    <span>Final Deterministic Score:</span>
                    <span>{analysis.score} / 100</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Mandatory Educational Disclaimer */}
        <p className="text-[10px] text-slate-400 italic pt-1 leading-relaxed">
          {analysis.disclaimer}
        </p>
      </CardContent>
    </Card>
  );
};
