import React from "react";
import type { ProductComparisonItem } from "@/types";
import { BarChart3, HelpCircle } from "lucide-react";

interface NutritionalComparisonChartProps {
  products: ProductComparisonItem[];
}

const PRODUCT_COLORS = [
  { bg: "bg-emerald-500", text: "text-emerald-700", border: "border-emerald-300", light: "bg-emerald-50" },
  { bg: "bg-indigo-500", text: "text-indigo-700", border: "border-indigo-300", light: "bg-indigo-50" },
  { bg: "bg-amber-500", text: "text-amber-700", border: "border-amber-300", light: "bg-amber-50" },
  { bg: "bg-rose-500", text: "text-rose-700", border: "border-rose-300", light: "bg-rose-50" },
  { bg: "bg-sky-500", text: "text-sky-700", border: "border-sky-300", light: "bg-sky-50" },
  { bg: "bg-purple-500", text: "text-purple-700", border: "border-purple-300", light: "bg-purple-50" },
];

const METRICS: { key: string; label: string; unit: string; maxRef: number }[] = [
  { key: "energy_kcal", label: "Energy / Calories", unit: "kcal", maxRef: 600 },
  { key: "total_sugar_g", label: "Total Sugar", unit: "g", maxRef: 50 },
  { key: "total_fat_g", label: "Total Fat", unit: "g", maxRef: 40 },
  { key: "saturated_fat_g", label: "Saturated Fat", unit: "g", maxRef: 20 },
  { key: "sodium_mg", label: "Sodium", unit: "mg", maxRef: 1000 },
  { key: "protein_g", label: "Protein", unit: "g", maxRef: 25 },
  { key: "dietary_fibre_g", label: "Dietary Fibre", unit: "g", maxRef: 15 },
];

export const NutritionalComparisonChart: React.FC<NutritionalComparisonChartProps> = ({
  products,
}) => {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3 pb-2 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <BarChart3 className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Nutritional Comparison Chart
            </h3>
            <p className="text-xs text-slate-500">
              Normalized comparative metrics (standardized per 100g / 100ml)
            </p>
          </div>
        </div>

        {/* Product Color Legend */}
        <div className="flex flex-wrap gap-2.5">
          {products.map((prod, idx) => {
            const col = PRODUCT_COLORS[idx % PRODUCT_COLORS.length];
            return (
              <div
                key={prod.product_id}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border ${col.light} ${col.border} ${col.text}`}
              >
                <span className={`h-2.5 w-2.5 rounded-full ${col.bg}`} />
                <span className="truncate max-w-[120px]">{prod.name}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="space-y-6">
        {METRICS.map((metric) => {
          // Find max value in this metric across compared products
          const values = products.map((p) => p.nutrients_per_100[metric.key]);
          const numValues = values.filter((v): v is number => v !== null && v !== undefined);
          const maxInRow = numValues.length > 0 ? Math.max(...numValues, metric.maxRef * 0.2) : metric.maxRef;

          return (
            <div key={metric.key} className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                <span>{metric.label}</span>
                <span className="text-slate-400 font-mono">Standardized in {metric.unit}</span>
              </div>

              <div className="space-y-1.5 bg-slate-50/70 p-3 rounded-xl border border-slate-100">
                {products.map((prod, idx) => {
                  const val = prod.nutrients_per_100[metric.key];
                  const col = PRODUCT_COLORS[idx % PRODUCT_COLORS.length];
                  const isMissing = val === null || val === undefined;
                  const widthPct = isMissing ? 0 : Math.min(100, Math.max(3, (val / maxInRow) * 100));

                  return (
                    <div key={prod.product_id} className="flex items-center gap-3 text-xs">
                      {/* Product Name Snippet */}
                      <span className="w-24 sm:w-32 truncate font-medium text-slate-600 flex-shrink-0">
                        {prod.name}
                      </span>

                      {/* Bar Gauge */}
                      <div className="flex-1 h-5 bg-white border border-slate-200/80 rounded-md overflow-hidden relative flex items-center">
                        {!isMissing ? (
                          <div
                            className={`h-full ${col.bg} transition-all duration-500 rounded-sm`}
                            style={{ width: `${widthPct}%` }}
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-[11px] text-slate-400 italic bg-slate-100/50">
                            <HelpCircle className="h-3 w-3 mr-1 inline opacity-60" />
                            Not declared on package
                          </div>
                        )}
                      </div>

                      {/* Numeric Value Tag */}
                      <span className="w-20 text-right font-mono font-semibold text-slate-800 flex-shrink-0">
                        {!isMissing ? (
                          <span>
                            {val} <span className="text-[10px] text-slate-500 font-normal">{metric.unit}</span>
                          </span>
                        ) : (
                          <span className="text-slate-400 font-normal italic text-[11px]">—</span>
                        )}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
