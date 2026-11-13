import React, { useState, useEffect, useMemo } from "react";
import {
  X,
  Search,
  Check,
  Coffee,
  Sun,
  Moon,
  Apple,
  Sparkles,
  Scale,
  Flame,
  AlertCircle,
  Loader2,
  BookMarked,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { apiService } from "@/services/api";
import { JournalEntryItem, ProductSummary } from "@/types";

interface LogMealModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialProduct?: {
    id: string;
    name: string;
    brand?: string | null;
    serving_size?: string | null;
    nutrition_facts?: any;
  } | null;
  editEntry?: JournalEntryItem | null;
  defaultDate?: string;
}

const MEAL_TYPES = [
  { id: "breakfast", label: "Breakfast", icon: Coffee },
  { id: "lunch", label: "Lunch", icon: Sun },
  { id: "dinner", label: "Dinner", icon: Moon },
  { id: "snack", label: "Snack", icon: Apple },
  { id: "other", label: "Other", icon: Sparkles },
];

export const LogMealModal: React.FC<LogMealModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialProduct,
  editEntry,
  defaultDate,
}) => {
  // Product state
  const [selectedProduct, setSelectedProduct] = useState<{
    id: string;
    name: string;
    brand?: string | null;
    serving_size?: string | null;
    nutrition_facts?: any;
  } | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<ProductSummary[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Form fields
  const [mealType, setMealType] = useState<string>("snack");
  const [consumedDate, setConsumedDate] = useState<string>(
    defaultDate || new Date().toISOString().split("T")[0]
  );
  const [consumedTime, setConsumedTime] = useState<string>(
    new Date().toTimeString().slice(0, 5)
  );
  const [quantity, setQuantity] = useState<number>(1.0);
  const [servingSizeG, setServingSizeG] = useState<string>("");
  const [totalWeightG, setTotalWeightG] = useState<string>("100");
  const [inputMode, setInputMode] = useState<"servings" | "weight">("servings");
  const [notes, setNotes] = useState<string>("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize or reset when modal opens or props change
  useEffect(() => {
    if (!isOpen) return;

    setError(null);
    if (editEntry) {
      setSelectedProduct({
        id: editEntry.product_id,
        name: editEntry.product_name,
        brand: editEntry.product_brand,
        serving_size: editEntry.serving_size_g ? `${editEntry.serving_size_g}g` : null,
      });
      setMealType(editEntry.meal_type || "snack");
      const d = new Date(editEntry.consumed_at);
      setConsumedDate(d.toISOString().split("T")[0]);
      setConsumedTime(d.toTimeString().slice(0, 5));
      setQuantity(editEntry.quantity || 1.0);
      setServingSizeG(editEntry.serving_size_g ? String(editEntry.serving_size_g) : "");
      setTotalWeightG(String(editEntry.total_weight_g || 100));
      setInputMode(editEntry.serving_size_g ? "servings" : "weight");
      setNotes(editEntry.notes || "");
    } else if (initialProduct) {
      setSelectedProduct(initialProduct);
      setMealType("snack");
      setConsumedDate(defaultDate || new Date().toISOString().split("T")[0]);
      setConsumedTime(new Date().toTimeString().slice(0, 5));
      setQuantity(1.0);

      // Extract grams from serving size if available
      const parsedGrams = parseGramsFromServing(initialProduct.serving_size);
      if (parsedGrams) {
        setServingSizeG(String(parsedGrams));
        setTotalWeightG(String(parsedGrams));
        setInputMode("servings");
      } else {
        setServingSizeG("100");
        setTotalWeightG("100");
        setInputMode("weight");
      }
      setNotes("");
    } else {
      setSelectedProduct(null);
      setMealType("snack");
      setConsumedDate(defaultDate || new Date().toISOString().split("T")[0]);
      setConsumedTime(new Date().toTimeString().slice(0, 5));
      setQuantity(1.0);
      setServingSizeG("100");
      setTotalWeightG("100");
      setInputMode("servings");
      setNotes("");
      setSearchQuery("");
      setSearchResults([]);
    }
  }, [isOpen, editEntry, initialProduct, defaultDate]);

  function parseGramsFromServing(str?: string | null): number | null {
    if (!str) return null;
    const match = str.match(/(\d+(?:\.\d+)?)\s*(?:g|ml)\b/i);
    return match ? parseFloat(match[1]) : null;
  }

  // Update total weight when quantity or servingSize changes in "servings" mode
  useEffect(() => {
    if (inputMode === "servings") {
      const sSize = parseFloat(servingSizeG) || 100;
      const computed = Math.round(quantity * sSize * 10) / 10;
      setTotalWeightG(String(computed));
    }
  }, [quantity, servingSizeG, inputMode]);

  // Product search debounce
  useEffect(() => {
    if (!searchQuery.trim() || selectedProduct) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await apiService.getProducts({
          search: searchQuery.trim(),
          page_size: 6,
        });
        setSearchResults(res.items);
      } catch (err) {
        console.error("Search failed:", err);
      } finally {
        setIsSearching(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery, selectedProduct]);

  // Real-time proportional nutrition scaling calculation
  const computedNutrientsPreview = useMemo(() => {
    const totalG = parseFloat(totalWeightG) || 0;
    const scaleFactor = totalG / 100.0;
    const facts = selectedProduct?.nutrition_facts;

    if (!facts) {
      return {
        scaleFactor,
        calories: null,
        sugar: null,
        sodium: null,
        protein: null,
      };
    }

    return {
      scaleFactor,
      calories: facts.energy_kcal != null ? Math.round(facts.energy_kcal * scaleFactor * 10) / 10 : null,
      sugar: facts.total_sugar_g != null ? Math.round(facts.total_sugar_g * scaleFactor * 10) / 10 : null,
      sodium: facts.sodium_mg != null ? Math.round(facts.sodium_mg * scaleFactor * 10) / 10 : null,
      protein: facts.protein_g != null ? Math.round(facts.protein_g * scaleFactor * 10) / 10 : null,
    };
  }, [selectedProduct, totalWeightG]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProduct) {
      setError("Please select a food product to log.");
      return;
    }

    const finalWeight = parseFloat(totalWeightG);
    if (isNaN(finalWeight) || finalWeight <= 0) {
      setError("Please enter a valid consumed weight in grams/ml.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const consumedAtIso = new Date(`${consumedDate}T${consumedTime}:00`).toISOString();

      if (editEntry) {
        await apiService.updateJournalEntry(editEntry.id, {
          meal_type: mealType,
          consumed_at: consumedAtIso,
          quantity: quantity,
          serving_unit: "g",
          serving_size_g: parseFloat(servingSizeG) || null,
          total_weight_g: finalWeight,
          notes: notes.trim() || null,
        });
      } else {
        await apiService.createJournalEntry({
          product_id: selectedProduct.id,
          meal_type: mealType,
          consumed_at: consumedAtIso,
          quantity: quantity,
          serving_unit: "g",
          serving_size_g: parseFloat(servingSizeG) || null,
          total_weight_g: finalWeight,
          notes: notes.trim() || null,
        });
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      console.error("Failed to save journal entry:", err);
      setError(err?.response?.data?.detail || "Failed to log food consumption. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-xl max-h-[90vh] overflow-y-auto">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50 rounded-t-2xl">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-emerald-100 text-emerald-700 rounded-xl">
              <BookMarked className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                {editEntry ? "Edit Consumption Entry" : "Log Food Consumption"}
              </h2>
              <p className="text-xs text-slate-500">
                Calculates actual nutrient intake scaled to consumed quantity
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm flex items-start space-x-2">
              <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* 1. Product Selection */}
          <div className="space-y-2">
            <Label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              1. Food Product *
            </Label>

            {selectedProduct ? (
              <div className="flex items-center justify-between p-3.5 bg-emerald-50/60 border border-emerald-200 rounded-xl">
                <div>
                  <div className="font-semibold text-slate-900 text-sm">
                    {selectedProduct.name}
                  </div>
                  <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
                    {selectedProduct.brand && <span>{selectedProduct.brand}</span>}
                    {selectedProduct.serving_size && (
                      <span className="text-emerald-700 font-medium">
                        • Standard serving: {selectedProduct.serving_size}
                      </span>
                    )}
                  </div>
                </div>
                {!editEntry && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="text-xs text-slate-500 hover:text-slate-800"
                    onClick={() => {
                      setSelectedProduct(null);
                      setSearchQuery("");
                    }}
                  >
                    Change
                  </Button>
                )}
              </div>
            ) : (
              <div className="relative">
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="Search packaged food from catalogue..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 text-sm"
                  />
                  {isSearching && (
                    <Loader2 className="absolute right-3 top-2.5 h-4 w-4 text-emerald-600 animate-spin" />
                  )}
                </div>

                {/* Autocomplete dropdown */}
                {searchResults.length > 0 && (
                  <div className="absolute z-20 mt-1 w-full bg-white border border-slate-200 rounded-xl shadow-lg max-h-60 overflow-y-auto divide-y divide-slate-100">
                    {searchResults.map((prod) => (
                      <button
                        key={prod.id}
                        type="button"
                        onClick={() => {
                          setSelectedProduct({
                            ...prod,
                            serving_size: prod.serving_size != null ? String(prod.serving_size) : null,
                          });
                          setSearchResults([]);
                          const parsed = parseGramsFromServing(prod.serving_size != null ? String(prod.serving_size) : null);
                          if (parsed) {
                            setServingSizeG(String(parsed));
                            setTotalWeightG(String(parsed));
                          }
                        }}
                        className="w-full text-left px-3.5 py-2.5 hover:bg-slate-50 transition-colors flex items-center justify-between text-sm"
                      >
                        <div>
                          <div className="font-medium text-slate-900">{prod.name}</div>
                          <div className="text-xs text-slate-500">
                            {prod.brand || "Packaged Food"} {prod.category ? `• ${prod.category}` : ""}
                          </div>
                        </div>
                        {prod.serving_size && (
                          <Badge variant="outline" className="text-xs bg-slate-50">
                            {prod.serving_size}
                          </Badge>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 2. Meal Type Selector */}
          <div className="space-y-2">
            <Label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              2. Meal Type
            </Label>
            <div className="grid grid-cols-5 gap-2">
              {MEAL_TYPES.map((m) => {
                const IconComponent = m.icon;
                const isSelected = mealType === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setMealType(m.id)}
                    className={`flex flex-col items-center justify-center py-2.5 px-1 rounded-xl border text-xs font-medium transition-all ${
                      isSelected
                        ? "bg-emerald-600 border-emerald-600 text-white shadow-sm"
                        : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    <IconComponent className={`h-4 w-4 mb-1 ${isSelected ? "text-white" : "text-slate-500"}`} />
                    <span>{m.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 3. Date & Time */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Date
              </Label>
              <Input
                type="date"
                value={consumedDate}
                onChange={(e) => setConsumedDate(e.target.value)}
                className="text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Time
              </Label>
              <Input
                type="time"
                value={consumedTime}
                onChange={(e) => setConsumedTime(e.target.value)}
                className="text-sm"
              />
            </div>
          </div>

          {/* 4. Quantity & Consumed Weight */}
          <div className="space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-200/80">
            <div className="flex items-center justify-between">
              <Label className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Scale className="h-3.5 w-3.5 text-emerald-600" />
                <span>3. Consumed Quantity</span>
              </Label>

              <div className="flex items-center bg-white rounded-lg border p-0.5 text-xs">
                <button
                  type="button"
                  onClick={() => setInputMode("servings")}
                  className={`px-2.5 py-1 rounded-md transition-colors ${
                    inputMode === "servings"
                      ? "bg-emerald-600 text-white font-medium shadow-xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  By Servings
                </button>
                <button
                  type="button"
                  onClick={() => setInputMode("weight")}
                  className={`px-2.5 py-1 rounded-md transition-colors ${
                    inputMode === "weight"
                      ? "bg-emerald-600 text-white font-medium shadow-xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Direct Grams/ml
                </button>
              </div>
            </div>

            {inputMode === "servings" ? (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <span className="text-xs text-slate-600">Servings Count:</span>
                  <div className="flex items-center space-x-1.5">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setQuantity(Math.max(0.5, quantity - 0.5))}
                      className="h-9 w-9 p-0 text-sm font-bold"
                    >
                      -
                    </Button>
                    <Input
                      type="number"
                      step="0.1"
                      min="0.1"
                      value={quantity}
                      onChange={(e) => setQuantity(parseFloat(e.target.value) || 1.0)}
                      className="text-center font-semibold text-sm h-9"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setQuantity(quantity + 0.5)}
                      className="h-9 w-9 p-0 text-sm font-bold"
                    >
                      +
                    </Button>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-xs text-slate-600">Grams per Serving:</span>
                  <div className="relative">
                    <Input
                      type="number"
                      min="1"
                      placeholder="e.g. 30"
                      value={servingSizeG}
                      onChange={(e) => setServingSizeG(e.target.value)}
                      className="text-sm h-9 pr-8"
                    />
                    <span className="absolute right-3 top-2 text-xs text-slate-400">g</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-1">
                <span className="text-xs text-slate-600">Total Consumed Weight:</span>
                <div className="relative">
                  <Input
                    type="number"
                    min="1"
                    placeholder="e.g. 75"
                    value={totalWeightG}
                    onChange={(e) => setTotalWeightG(e.target.value)}
                    className="text-sm h-9 pr-12 font-medium"
                  />
                  <span className="absolute right-3 top-2 text-xs font-semibold text-emerald-700">
                    grams
                  </span>
                </div>
              </div>
            )}

            {/* Calculated Weight Summary Pill */}
            <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-200">
              <span className="text-slate-500">Effective Consumed Weight:</span>
              <span className="font-bold text-emerald-800 bg-emerald-100/60 px-2 py-0.5 rounded-md">
                {totalWeightG || 0}g ({Math.round(((parseFloat(totalWeightG) || 0) / 100) * 100)}% of 100g)
              </span>
            </div>

            {/* Live Nutrient Scaling Preview */}
            {computedNutrientsPreview.calories != null && (
              <div className="pt-2">
                <div className="text-[11px] uppercase font-semibold text-slate-500 mb-1.5 flex items-center gap-1">
                  <Flame className="h-3 w-3 text-amber-500" />
                  <span>Scaled Nutritional Intake Preview:</span>
                </div>
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  <div className="p-1.5 bg-white rounded-lg border border-slate-200">
                    <div className="text-slate-500 text-[10px]">Calories</div>
                    <div className="font-bold text-slate-900">{computedNutrientsPreview.calories} kcal</div>
                  </div>
                  <div className="p-1.5 bg-white rounded-lg border border-slate-200">
                    <div className="text-slate-500 text-[10px]">Sugar</div>
                    <div className="font-bold text-slate-900">
                      {computedNutrientsPreview.sugar != null ? `${computedNutrientsPreview.sugar}g` : "N/D"}
                    </div>
                  </div>
                  <div className="p-1.5 bg-white rounded-lg border border-slate-200">
                    <div className="text-slate-500 text-[10px]">Sodium</div>
                    <div className="font-bold text-slate-900">
                      {computedNutrientsPreview.sodium != null ? `${computedNutrientsPreview.sodium}mg` : "N/D"}
                    </div>
                  </div>
                  <div className="p-1.5 bg-white rounded-lg border border-slate-200">
                    <div className="text-slate-500 text-[10px]">Protein</div>
                    <div className="font-bold text-slate-900">
                      {computedNutrientsPreview.protein != null ? `${computedNutrientsPreview.protein}g` : "N/D"}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 5. Optional Notes */}
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Optional Notes
            </Label>
            <Input
              placeholder="e.g. With low-fat milk, post-workout snack"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="text-sm"
              maxLength={200}
            />
          </div>

          {/* Modal Actions */}
          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || !selectedProduct}
              className="bg-emerald-600 hover:bg-emerald-700 text-white min-w-[120px]"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Saving...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4 mr-1.5" />
                  {editEntry ? "Update Entry" : "Save Log"}
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
