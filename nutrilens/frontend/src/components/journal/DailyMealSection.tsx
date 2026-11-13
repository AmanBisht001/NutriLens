import React, { useState } from "react";
import {
  Coffee,
  Sun,
  Moon,
  Apple,
  Sparkles,
  Edit2,
  Trash2,
  Plus,
  Flame,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DailyMealGroup, JournalEntryItem } from "@/types";

interface DailyMealSectionProps {
  meals: Record<string, DailyMealGroup>;
  onEditEntry: (entry: JournalEntryItem) => void;
  onDeleteEntry: (entryId: string) => void;
  onAddMeal: (mealType: string) => void;
}

const MEAL_CONFIG = [
  { id: "breakfast", label: "Breakfast", icon: Coffee, color: "text-amber-600 bg-amber-50 border-amber-200" },
  { id: "lunch", label: "Lunch", icon: Sun, color: "text-emerald-600 bg-emerald-50 border-emerald-200" },
  { id: "dinner", label: "Dinner", icon: Moon, color: "text-indigo-600 bg-indigo-50 border-indigo-200" },
  { id: "snack", label: "Snacks", icon: Apple, color: "text-rose-600 bg-rose-50 border-rose-200" },
  { id: "other", label: "Other", icon: Sparkles, color: "text-slate-600 bg-slate-50 border-slate-200" },
];

export const DailyMealSection: React.FC<DailyMealSectionProps> = ({
  meals,
  onEditEntry,
  onDeleteEntry,
  onAddMeal,
}) => {
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      {MEAL_CONFIG.map((group) => {
        const mealGroup = meals[group.id] || {
          meal_type: group.id,
          label: group.label,
          entries: [],
          total_calories: 0,
          total_weight_g: 0,
        };
        const IconComponent = group.icon;
        const entries = mealGroup.entries || [];

        return (
          <div
            key={group.id}
            className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden"
          >
            {/* Meal Header */}
            <div className="flex items-center justify-between px-5 py-3.5 bg-slate-50/70 border-b border-slate-100">
              <div className="flex items-center space-x-2.5">
                <div className={`p-1.5 rounded-lg border ${group.color}`}>
                  <IconComponent className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{group.label}</h3>
                  <div className="text-xs text-slate-500">
                    {entries.length} {entries.length === 1 ? "item" : "items"}
                    {mealGroup.total_weight_g > 0 && ` • ${mealGroup.total_weight_g}g total`}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                {mealGroup.total_calories > 0 && (
                  <div className="flex items-center gap-1 text-xs font-bold text-emerald-800 bg-emerald-100/70 px-2.5 py-1 rounded-full">
                    <Flame className="h-3.5 w-3.5 text-amber-500 fill-amber-500" />
                    <span>{mealGroup.total_calories} kcal</span>
                  </div>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onAddMeal(group.id)}
                  className="h-8 text-xs text-slate-700 hover:text-emerald-700 hover:bg-emerald-50 border-slate-200"
                >
                  <Plus className="h-3.5 w-3.5 mr-1" />
                  Add
                </Button>
              </div>
            </div>

            {/* Entries List */}
            <div className="p-4">
              {entries.length === 0 ? (
                <div
                  onClick={() => onAddMeal(group.id)}
                  className="border-2 border-dashed border-slate-200 rounded-xl p-4 text-center cursor-pointer hover:border-emerald-300 hover:bg-emerald-50/20 transition-colors group"
                >
                  <p className="text-xs text-slate-400 group-hover:text-emerald-700 font-medium">
                    + No {group.label.toLowerCase()} logged yet. Click to record a food item.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {entries.map((item) => (
                    <div
                      key={item.id}
                      className="p-3.5 rounded-xl border border-slate-100 hover:border-slate-200 bg-slate-50/40 hover:bg-white transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                    >
                      {/* Product details */}
                      <div className="flex items-start space-x-3 min-w-0">
                        {item.product_image_url ? (
                          <img
                            src={item.product_image_url}
                            alt={item.product_name}
                            className="h-12 w-12 rounded-lg object-cover border border-slate-200 shrink-0 bg-white"
                          />
                        ) : (
                          <div className="h-12 w-12 rounded-lg bg-emerald-100/60 border border-emerald-200 text-emerald-800 flex items-center justify-center font-bold text-sm shrink-0">
                            {item.product_name.slice(0, 2).toUpperCase()}
                          </div>
                        )}

                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm text-slate-900 truncate">
                              {item.product_name}
                            </span>
                            {item.product_brand && (
                              <Badge variant="outline" className="text-[10px] text-slate-500 py-0 px-1.5 font-normal">
                                {item.product_brand}
                              </Badge>
                            )}
                          </div>

                          <div className="text-xs text-slate-500 mt-0.5">
                            <span className="font-medium text-slate-700">
                              {item.total_weight_g}g consumed
                            </span>
                            {item.quantity > 0 && item.serving_size_g && (
                              <span> ({item.quantity} × {item.serving_size_g}g serving)</span>
                            )}
                            {item.notes && (
                              <span className="italic text-slate-400 block sm:inline sm:ml-2">
                                “{item.notes}”
                              </span>
                            )}
                          </div>

                          {/* Scaled Nutrients Micro-Pills */}
                          <div className="flex flex-wrap items-center gap-1.5 mt-2">
                            {item.nutrients.energy_kcal != null && (
                              <span className="inline-flex items-center text-[11px] font-semibold text-emerald-900 bg-emerald-100/80 px-2 py-0.5 rounded-md">
                                <Flame className="h-3 w-3 text-amber-500 mr-1" />
                                {item.nutrients.energy_kcal} kcal
                              </span>
                            )}
                            {item.nutrients.total_sugar_g != null && (
                              <span className="text-[11px] text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                                Sugar: <strong className="text-slate-800">{item.nutrients.total_sugar_g}g</strong>
                              </span>
                            )}
                            {item.nutrients.protein_g != null && (
                              <span className="text-[11px] text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                                Protein: <strong className="text-slate-800">{item.nutrients.protein_g}g</strong>
                              </span>
                            )}
                            {item.nutrients.sodium_mg != null && (
                              <span className="text-[11px] text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                                Sodium: <strong className="text-slate-800">{item.nutrients.sodium_mg}mg</strong>
                              </span>
                            )}
                            {item.nutrients.dietary_fibre_g != null && (
                              <span className="text-[11px] text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                                Fibre: <strong className="text-slate-800">{item.nutrients.dietary_fibre_g}g</strong>
                              </span>
                            )}
                            {item.nutrients.missing_nutrients && item.nutrients.missing_nutrients.length > 0 && (
                              <span className="text-[10px] text-amber-700 bg-amber-50 border border-amber-200 px-1.5 py-0.5 rounded inline-flex items-center gap-1">
                                <AlertCircle className="h-2.5 w-2.5" />
                                {item.nutrients.missing_nutrients.length} undeclared
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Item Actions */}
                      <div className="flex items-center space-x-1.5 self-end sm:self-center shrink-0">
                        {deleteConfirmId === item.id ? (
                          <div className="flex items-center space-x-1 bg-rose-50 border border-rose-200 rounded-lg p-1 animate-in fade-in">
                            <span className="text-[11px] text-rose-700 font-medium px-1.5">Delete?</span>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => {
                                onDeleteEntry(item.id);
                                setDeleteConfirmId(null);
                              }}
                              className="h-7 text-xs px-2 bg-rose-600 hover:bg-rose-700"
                            >
                              Yes
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => setDeleteConfirmId(null)}
                              className="h-7 text-xs px-2 text-slate-600"
                            >
                              No
                            </Button>
                          </div>
                        ) : (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onEditEntry(item)}
                              className="h-8 w-8 p-0 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg"
                              title="Edit logged quantity or meal"
                            >
                              <Edit2 className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setDeleteConfirmId(item.id)}
                              className="h-8 w-8 p-0 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg"
                              title="Delete entry"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
