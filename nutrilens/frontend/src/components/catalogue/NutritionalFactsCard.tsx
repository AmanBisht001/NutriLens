import React from "react";
import { Activity, Info } from "lucide-react";
import type { NutritionFacts } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface NutritionalFactsCardProps {
  nutrition: NutritionFacts | null | undefined;
  servingSize?: string | null;
}

export const NutritionalFactsCard: React.FC<NutritionalFactsCardProps> = ({
  nutrition,
  servingSize,
}) => {
  if (!nutrition) {
    return (
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5 text-emerald-600" />
            Nutritional Facts
          </CardTitle>
          <CardDescription>Laboratory nutrient declaration.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500 italic">
            Nutritional facts have not yet been declared or transcribed for this item.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Calculate equivalent salt from sodium (salt = sodium_mg * 2.5 / 1000 in grams)
  const saltGrams =
    nutrition.sodium_mg !== null && nutrition.sodium_mg !== undefined
      ? ((nutrition.sodium_mg * 2.5) / 1000).toFixed(2)
      : null;

  return (
    <Card className="border-slate-200 shadow-sm overflow-hidden">
      <CardHeader className="bg-slate-50/70 border-b border-slate-200 pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-emerald-600" />
            <CardTitle className="text-lg">Nutritional Information</CardTitle>
          </div>
          <Badge variant="outline" className="text-xs bg-white text-slate-700">
            {nutrition.serving_unit === "per_serving" ? "Per Serving" : "Per 100g / 100ml"}
          </Badge>
        </div>
        {servingSize && (
          <CardDescription className="text-xs text-slate-500 pt-1">
            Reference Serving Size: <span className="font-semibold text-slate-700">{servingSize}</span>
          </CardDescription>
        )}
      </CardHeader>

      <CardContent className="p-0">
        {/* Illustrative Demo Notice */}
        {nutrition.is_illustrative && (
          <div className="p-3 bg-amber-50/80 border-b border-amber-200 flex items-start gap-2 text-xs text-amber-900">
            <Info className="h-4 w-4 text-amber-700 mt-0.5 flex-shrink-0" />
            <span>
              <strong className="font-semibold">Illustrative Development Data:</strong> These values are
              demonstration parameters for algorithmic calibration and testing. They do not represent
              laboratory-certified facts.
            </span>
          </div>
        )}

        {/* Nutritional Facts Table */}
        <div className="divide-y divide-slate-100 text-sm">
          {/* Energy / Calories */}
          <div className="flex items-center justify-between px-5 py-3 bg-emerald-50/30 font-bold text-slate-900">
            <span>Energy / Calories</span>
            <span className="text-base text-emerald-800">
              {nutrition.energy_kcal !== null && nutrition.energy_kcal !== undefined
                ? `${nutrition.energy_kcal} kcal`
                : "—"}
            </span>
          </div>

          {/* Total Fat */}
          <div className="flex items-center justify-between px-5 py-2.5">
            <span className="font-semibold text-slate-800">Total Fat</span>
            <span className="text-slate-700">
              {nutrition.total_fat_g !== null && nutrition.total_fat_g !== undefined
                ? `${nutrition.total_fat_g} g`
                : "—"}
            </span>
          </div>

          {/* Saturated Fat */}
          <div className="flex items-center justify-between px-5 py-2 pl-9 text-xs text-slate-600">
            <span>of which Saturated Fat</span>
            <span>
              {nutrition.saturated_fat_g !== null && nutrition.saturated_fat_g !== undefined
                ? `${nutrition.saturated_fat_g} g`
                : "—"}
            </span>
          </div>

          {/* Trans Fat */}
          <div className="flex items-center justify-between px-5 py-2 pl-9 text-xs text-slate-600">
            <span>of which Trans Fat</span>
            <span>
              {nutrition.trans_fat_g !== null && nutrition.trans_fat_g !== undefined
                ? `${nutrition.trans_fat_g} g`
                : "—"}
            </span>
          </div>

          {/* Cholesterol */}
          {nutrition.cholesterol_mg !== null && nutrition.cholesterol_mg !== undefined && (
            <div className="flex items-center justify-between px-5 py-2.5">
              <span className="font-semibold text-slate-800">Cholesterol</span>
              <span className="text-slate-700">{nutrition.cholesterol_mg} mg</span>
            </div>
          )}

          {/* Carbohydrates */}
          <div className="flex items-center justify-between px-5 py-2.5">
            <span className="font-semibold text-slate-800">Total Carbohydrates</span>
            <span className="text-slate-700">
              {nutrition.carbohydrates_g !== null && nutrition.carbohydrates_g !== undefined
                ? `${nutrition.carbohydrates_g} g`
                : "—"}
            </span>
          </div>

          {/* Total Sugars */}
          <div className="flex items-center justify-between px-5 py-2 pl-9 text-xs text-slate-600">
            <span>of which Total Sugars</span>
            <span>
              {nutrition.total_sugar_g !== null && nutrition.total_sugar_g !== undefined
                ? `${nutrition.total_sugar_g} g`
                : "—"}
            </span>
          </div>

          {/* Added Sugars */}
          {nutrition.added_sugar_g !== null && nutrition.added_sugar_g !== undefined && (
            <div className="flex items-center justify-between px-5 py-2 pl-12 text-xs text-slate-500">
              <span>includes Added Sugars</span>
              <span className="font-semibold text-slate-700">{nutrition.added_sugar_g} g</span>
            </div>
          )}

          {/* Dietary Fibre */}
          <div className="flex items-center justify-between px-5 py-2.5">
            <span className="font-semibold text-slate-800">Dietary Fibre</span>
            <span className="text-slate-700">
              {nutrition.dietary_fibre_g !== null && nutrition.dietary_fibre_g !== undefined
                ? `${nutrition.dietary_fibre_g} g`
                : "—"}
            </span>
          </div>

          {/* Protein */}
          <div className="flex items-center justify-between px-5 py-2.5">
            <span className="font-semibold text-slate-800">Protein</span>
            <span className="text-slate-700">
              {nutrition.protein_g !== null && nutrition.protein_g !== undefined
                ? `${nutrition.protein_g} g`
                : "—"}
            </span>
          </div>

          {/* Sodium */}
          <div className="flex items-center justify-between px-5 py-2.5">
            <span className="font-semibold text-slate-800">Sodium</span>
            <span className="text-slate-700">
              {nutrition.sodium_mg !== null && nutrition.sodium_mg !== undefined
                ? `${nutrition.sodium_mg} mg`
                : "—"}
            </span>
          </div>

          {/* Salt Equivalent */}
          {saltGrams && (
            <div className="flex items-center justify-between px-5 py-2 pl-9 text-xs text-slate-500">
              <span>Equivalent Salt</span>
              <span>{saltGrams} g</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
