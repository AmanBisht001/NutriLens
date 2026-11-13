import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams, Link } from "react-router-dom";
import {
  ArrowLeftRight,
  Plus,
  X,
  Sparkles,
  Trophy,
  HelpCircle,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { apiService } from "@/services/api";
import type {
  ComparisonMatrixResponse,
  ComparisonPriority,
  ProductSummary,
} from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import { PrioritySelector } from "@/components/comparison/PrioritySelector";
import { NutritionalComparisonChart } from "@/components/comparison/NutritionalComparisonChart";
import { ProductSelectorModal } from "@/components/comparison/ProductSelectorModal";

const NUTRIENT_ROWS: { key: string; label: string; unit: string; priorityMap?: ComparisonPriority }[] = [
  { key: "energy_kcal", label: "Energy / Calories", unit: "kcal" },
  { key: "total_sugar_g", label: "Total Sugar", unit: "g", priorityMap: "lower_sugar" },
  { key: "added_sugar_g", label: "Added Sugar", unit: "g" },
  { key: "total_fat_g", label: "Total Fat", unit: "g" },
  { key: "saturated_fat_g", label: "Saturated Fat", unit: "g", priorityMap: "lower_saturated_fat" },
  { key: "trans_fat_g", label: "Trans Fat", unit: "g" },
  { key: "sodium_mg", label: "Sodium", unit: "mg", priorityMap: "lower_sodium" },
  { key: "protein_g", label: "Protein", unit: "g", priorityMap: "higher_protein" },
  { key: "dietary_fibre_g", label: "Dietary Fibre", unit: "g", priorityMap: "higher_fibre" },
  { key: "carbohydrates_g", label: "Carbohydrates", unit: "g" },
];

export const CompareProductsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [productIds, setProductIds] = useState<string[]>([]);
  const [selectedPriorities, setSelectedPriorities] = useState<ComparisonPriority[]>([
    "lower_sugar",
    "higher_protein",
  ]);
  const [viewUnit, setViewUnit] = useState<"per_100" | "per_serving">("per_100");
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [comparisonData, setComparisonData] = useState<ComparisonMatrixResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync with URL query parameters (?products=id1,id2)
  useEffect(() => {
    const pParam = searchParams.get("products");
    if (pParam) {
      const ids = pParam.split(",").filter((id) => id.trim().length > 0);
      if (ids.length > 0) {
        setProductIds(ids);
      }
    }
  }, [searchParams]);

  // Fetch comparison data when productIds or priorities change
  const fetchComparison = useCallback(async () => {
    if (productIds.length < 2) {
      setComparisonData(null);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await apiService.compareProducts(productIds, selectedPriorities);
      setComparisonData(data);
    } catch (err: any) {
      console.error("Comparison request failed:", err);
      setError(
        err.response?.data?.detail || "Failed to compare selected products. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  }, [productIds, selectedPriorities]);

  useEffect(() => {
    fetchComparison();
  }, [fetchComparison]);

  // Update query params when productIds change
  const updateUrlWithIds = (ids: string[]) => {
    setProductIds(ids);
    if (ids.length > 0) {
      setSearchParams({ products: ids.join(",") });
    } else {
      setSearchParams({});
    }
  };

  const handleAddProduct = (product: ProductSummary) => {
    if (!productIds.includes(product.id)) {
      if (productIds.length >= 5) {
        alert("You can compare up to 5 products at once.");
        return;
      }
      updateUrlWithIds([...productIds, product.id]);
    }
  };

  const handleRemoveProduct = (productId: string) => {
    updateUrlWithIds(productIds.filter((id) => id !== productId));
  };

  // Find priority winner for a given nutrient key
  const getWinnerForNutrient = (key: string): string | null => {
    if (!comparisonData) return null;
    const row = NUTRIENT_ROWS.find((r) => r.key === key);
    if (!row || !row.priorityMap) return null;

    const prioEval = comparisonData.priority_evaluations.find(
      (e) => e.priority === row.priorityMap
    );
    return prioEval?.best_product_id || null;
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              Product Comparison
            </h1>
            <Badge variant="outline" className="text-xs bg-emerald-50 text-emerald-800 border-emerald-300">
              Deterministic Engine
            </Badge>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Side-by-side nutritional trade-off analysis, standardized per 100g/ml metrics, and personal suitability checks.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            onClick={() => setIsModalOpen(true)}
            className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs"
          >
            <Plus className="h-4 w-4 mr-1.5" /> Add Product ({productIds.length}/5)
          </Button>
          {productIds.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => updateUrlWithIds([])}
              className="text-xs text-slate-600"
            >
              Clear All
            </Button>
          )}
        </div>
      </div>

      {/* Priority Selector Bar */}
      <PrioritySelector
        selectedPriorities={selectedPriorities}
        onChange={setSelectedPriorities}
      />

      {/* Loading State */}
      {isLoading && (
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-12 flex flex-col items-center justify-center gap-3 text-slate-500">
            <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
            <span className="text-sm font-medium">Standardizing metrics and evaluating trade-offs...</span>
          </CardContent>
        </Card>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 flex items-start gap-3 text-red-800 text-sm">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <strong className="font-semibold">Comparison error:</strong> {error}
          </div>
        </div>
      )}

      {/* Empty State when fewer than 2 products */}
      {productIds.length < 2 && !isLoading && (
        <Card className="border-dashed border-2 border-slate-200 shadow-none text-center p-8 sm:p-12">
          <CardContent className="space-y-4 max-w-md mx-auto">
            <div className="h-16 w-16 mx-auto rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <ArrowLeftRight className="h-8 w-8" />
            </div>
            <CardTitle className="text-xl font-bold text-slate-900">
              Select at least 2 products to compare
            </CardTitle>
            <CardDescription className="text-slate-600 text-sm">
              Choose packaged foods from our verified catalogue to evaluate sugar deltas, sodium levels,
              protein contents, and personal allergen compatibility.
            </CardDescription>
            <div className="pt-2 flex flex-wrap justify-center gap-3">
              <Button
                onClick={() => setIsModalOpen(true)}
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                <Plus className="h-4 w-4 mr-1.5" /> Select Products
              </Button>
              <Button asChild variant="outline">
                <Link to="/catalogue">Browse Food Catalogue</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Comparison View */}
      {comparisonData && comparisonData.products.length >= 2 && !isLoading && (
        <div className="space-y-6">
          {/* Summary Banner */}
          <div className="p-4 bg-emerald-50/80 rounded-2xl border border-emerald-200 flex items-start gap-3 text-emerald-950 text-sm">
            <Sparkles className="h-5 w-5 text-emerald-700 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Trade-Off Analysis:</span> {comparisonData.summary}
            </div>
          </div>

          {/* Unit Switcher & Table Control */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
              <button
                onClick={() => setViewUnit("per_100")}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  viewUnit === "per_100"
                    ? "bg-white text-slate-900 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Standardized (Per 100g / 100ml)
              </button>
              <button
                onClick={() => setViewUnit("per_serving")}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  viewUnit === "per_serving"
                    ? "bg-white text-slate-900 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Per Declared Serving
              </button>
            </div>

            <span className="text-xs text-slate-400 italic">
              ℹ Missing nutrition facts are explicitly flagged as "Not Declared" rather than zero.
            </span>
          </div>

          {/* Side-by-Side Product Comparison Grid */}
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/70">
                    <th className="p-4 w-44 sm:w-56 text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Product Attributes
                    </th>
                    {comparisonData.products.map((prod) => (
                      <th
                        key={prod.product_id}
                        className="p-4 min-w-[200px] max-w-[260px] align-top relative"
                      >
                        <button
                          onClick={() => handleRemoveProduct(prod.product_id)}
                          className="absolute top-3 right-3 text-slate-400 hover:text-rose-600 h-6 w-6 rounded-md hover:bg-slate-100 flex items-center justify-center transition-colors"
                          title="Remove from comparison"
                        >
                          <X className="h-4 w-4" />
                        </button>

                        <div className="space-y-2 pr-6">
                          <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider">
                            {prod.brand || "Brand"}
                          </span>
                          <Link
                            to={`/products/${prod.product_id}`}
                            className="block text-sm font-bold text-slate-900 hover:text-emerald-700 line-clamp-2 transition-colors"
                          >
                            {prod.name}
                          </Link>
                          {prod.category && (
                            <Badge variant="outline" className="text-[10px] py-0 px-1.5 bg-white border-slate-200">
                              {prod.category}
                            </Badge>
                          )}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-100 text-xs">
                  {/* NutriLens Score Row */}
                  <tr className="bg-slate-50/40">
                    <td className="p-3.5 font-bold text-slate-700">NutriLens Score</td>
                    {comparisonData.products.map((prod) => {
                      const hasScore = prod.score !== null && prod.score !== undefined;
                      return (
                        <td key={prod.product_id} className="p-3.5">
                          {hasScore ? (
                            <div className="flex items-center gap-2">
                              <span
                                className={`text-base font-extrabold px-2.5 py-0.5 rounded-lg border ${
                                  prod.score! >= 75
                                    ? "bg-emerald-100 text-emerald-900 border-emerald-300"
                                    : prod.score! >= 50
                                    ? "bg-amber-100 text-amber-900 border-amber-300"
                                    : "bg-rose-100 text-rose-900 border-rose-300"
                                }`}
                              >
                                {prod.score}/100
                              </span>
                              <Badge variant="outline" className="font-bold">
                                Grade {prod.grade}
                              </Badge>
                            </div>
                          ) : (
                            <span className="text-slate-400 italic">Insufficient Data</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>

                  {/* Personal Suitability Row */}
                  <tr>
                    <td className="p-3.5 font-bold text-slate-700">Personal Suitability</td>
                    {comparisonData.products.map((prod) => (
                      <td key={prod.product_id} className="p-3.5 space-y-1">
                        <Badge
                          className={`text-xs px-2.5 py-0.5 font-semibold ${
                            prod.suitability_badge === "emerald"
                              ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                              : prod.suitability_badge === "rose"
                              ? "bg-rose-100 text-rose-800 border-rose-300"
                              : "bg-amber-100 text-amber-800 border-amber-300"
                          }`}
                        >
                          {prod.suitability_status}
                        </Badge>
                        {prod.suitability_conflicts.length > 0 && (
                          <div className="text-[11px] text-rose-700 font-medium">
                            ⚠ Conflicts: {prod.suitability_conflicts.join(", ")}
                          </div>
                        )}
                      </td>
                    ))}
                  </tr>

                  {/* Serving Size Row */}
                  <tr className="bg-slate-50/20">
                    <td className="p-3.5 font-bold text-slate-700">Declared Serving</td>
                    {comparisonData.products.map((prod) => (
                      <td key={prod.product_id} className="p-3.5 text-slate-600 font-medium">
                        {prod.serving_size || <span className="text-slate-400 italic">Not declared</span>}
                      </td>
                    ))}
                  </tr>

                  {/* Standardized Nutrients Section Header */}
                  <tr className="bg-slate-100/70 border-t border-slate-200">
                    <td colSpan={comparisonData.products.length + 1} className="p-2.5 px-4 font-bold text-slate-700 uppercase tracking-wider text-[11px]">
                      Nutritional Values ({viewUnit === "per_100" ? "Per 100g / 100ml Standardized" : "Per Serving"})
                    </td>
                  </tr>

                  {/* Nutrient Rows */}
                  {NUTRIENT_ROWS.map((row) => (
                    <tr key={row.key} className="hover:bg-slate-50/60 transition-colors">
                      <td className="p-3.5 font-medium text-slate-700 flex items-center justify-between">
                        <span>{row.label}</span>
                        <span className="text-[10px] text-slate-400 font-mono">({row.unit})</span>
                      </td>

                      {comparisonData.products.map((prod) => {
                        const vals = viewUnit === "per_100" ? prod.nutrients_per_100 : prod.nutrients_per_serving;
                        const val = vals[row.key];
                        const isWinner = getWinnerForNutrient(row.key) === prod.product_id;
                        const isMissing = val === null || val === undefined;

                        return (
                          <td key={prod.product_id} className="p-3.5">
                            <div className="flex items-center gap-1.5">
                              {!isMissing ? (
                                <span className={`font-mono font-semibold ${isWinner ? "text-emerald-700 font-bold" : "text-slate-800"}`}>
                                  {val} {row.unit}
                                </span>
                              ) : (
                                <span className="text-slate-400 italic text-[11px] flex items-center gap-1">
                                  <HelpCircle className="h-3 w-3 inline text-slate-300" /> Not Declared
                                </span>
                              )}

                              {isWinner && !isMissing && (
                                <Badge className="bg-amber-100 text-amber-900 border-amber-300 text-[10px] px-1.5 py-0 flex items-center gap-0.5">
                                  <Trophy className="h-2.5 w-2.5 text-amber-600" /> Best
                                </Badge>
                              )}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}

                  {/* Ingredients Section Header */}
                  <tr className="bg-slate-100/70 border-t border-slate-200">
                    <td colSpan={comparisonData.products.length + 1} className="p-2.5 px-4 font-bold text-slate-700 uppercase tracking-wider text-[11px]">
                      Ingredients &amp; Formulation
                    </td>
                  </tr>

                  {/* Total Ingredients Count */}
                  <tr>
                    <td className="p-3.5 font-medium text-slate-700">Total Ingredients</td>
                    {comparisonData.products.map((prod) => (
                      <td key={prod.product_id} className="p-3.5 font-bold text-slate-800">
                        {prod.ingredients.length} items
                      </td>
                    ))}
                  </tr>

                  {/* Common Ingredients Shared Across All */}
                  <tr className="bg-emerald-50/20">
                    <td className="p-3.5 font-medium text-slate-700">
                      <span className="font-bold text-emerald-800">Shared Ingredients</span>
                      <p className="text-[10px] text-slate-400">Present in all compared items</p>
                    </td>
                    <td colSpan={comparisonData.products.length} className="p-3.5">
                      {comparisonData.common_ingredients.length > 0 ? (
                        <div className="flex flex-wrap gap-1.5">
                          {comparisonData.common_ingredients.map((ing) => (
                            <Badge key={ing} variant="outline" className="bg-emerald-50 text-emerald-800 border-emerald-300 text-xs">
                              {ing}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-400 italic text-xs">No shared ingredients found across all products.</span>
                      )}
                    </td>
                  </tr>

                  {/* Ingredient Details List */}
                  <tr>
                    <td className="p-3.5 font-medium text-slate-700 align-top">Ingredient List</td>
                    {comparisonData.products.map((prod) => (
                      <td key={prod.product_id} className="p-3.5 align-top">
                        <div className="max-h-48 overflow-y-auto space-y-1 text-slate-600 text-[11px] pr-2">
                          {prod.ingredients.map((ing, i) => {
                            const isCommon = comparisonData.common_ingredients.some(
                              (ci) => ci.toLowerCase() === ing.toLowerCase()
                            );
                            return (
                              <div
                                key={i}
                                className={`px-2 py-0.5 rounded ${
                                  isCommon
                                    ? "bg-emerald-50 text-emerald-900 font-semibold"
                                    : "bg-slate-50 text-slate-700"
                                }`}
                              >
                                {ing}
                              </div>
                            );
                          })}
                        </div>
                      </td>
                    ))}
                  </tr>

                  {/* Allergens Section Header */}
                  <tr className="bg-slate-100/70 border-t border-slate-200">
                    <td colSpan={comparisonData.products.length + 1} className="p-2.5 px-4 font-bold text-slate-700 uppercase tracking-wider text-[11px]">
                      Allergens &amp; Warnings
                    </td>
                  </tr>

                  {/* Declared Allergens */}
                  <tr>
                    <td className="p-3.5 font-medium text-slate-700 align-top">Declared Allergens</td>
                    {comparisonData.products.map((prod) => (
                      <td key={prod.product_id} className="p-3.5 align-top">
                        {prod.allergens_declared.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {prod.allergens_declared.map((alg) => (
                              <Badge key={alg} variant="outline" className="bg-rose-50 text-rose-800 border-rose-300 text-xs">
                                ⚠ {alg}
                              </Badge>
                            ))}
                          </div>
                        ) : (
                          <span className="text-slate-400 italic text-xs">No declared allergens</span>
                        )}
                      </td>
                    ))}
                  </tr>

                  {/* Precautionary ("May Contain") */}
                  <tr>
                    <td className="p-3.5 font-medium text-slate-700 align-top">Precautionary Statements</td>
                    {comparisonData.products.map((prod) => (
                      <td key={prod.product_id} className="p-3.5 align-top">
                        {prod.allergens_precautionary.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {prod.allergens_precautionary.map((alg) => (
                              <Badge key={alg} variant="outline" className="bg-amber-50 text-amber-800 border-amber-300 text-xs">
                                May contain: {alg}
                              </Badge>
                            ))}
                          </div>
                        ) : (
                          <span className="text-slate-400 italic text-xs">None declared</span>
                        )}
                      </td>
                    ))}
                  </tr>

                  {/* Price Row */}
                  <tr className="bg-slate-50/20">
                    <td className="p-3.5 font-medium text-slate-700">Verified Price</td>
                    {comparisonData.products.map((prod) => (
                      <td key={prod.product_id} className="p-3.5 text-slate-400 italic">
                        {prod.price_display}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Visual Comparison Chart Section */}
          <NutritionalComparisonChart products={comparisonData.products} />
        </div>
      )}

      {/* Product Selector Modal */}
      <ProductSelectorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        selectedProductIds={productIds}
        onSelectProduct={handleAddProduct}
      />
    </div>
  );
};
