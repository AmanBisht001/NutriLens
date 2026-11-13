import React, { useState } from "react";
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  FileText,
} from "lucide-react";
import type { ProductIngredient } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface IngredientListCardProps {
  ingredients: ProductIngredient[];
  rawText?: string | null;
}

export const IngredientListCard: React.FC<IngredientListCardProps> = ({
  ingredients,
  rawText,
}) => {
  const [showRawText, setShowRawText] = useState(false);

  const getConcernBadge = (level?: string) => {
    switch (level?.toLowerCase()) {
      case "high":
        return (
          <Badge className="bg-rose-100 text-rose-800 border-rose-300 hover:bg-rose-100 text-[11px] font-semibold">
            High Concern
          </Badge>
        );
      case "moderate":
        return (
          <Badge className="bg-amber-100 text-amber-900 border-amber-300 hover:bg-amber-100 text-[11px] font-semibold">
            Moderate
          </Badge>
        );
      case "safe":
      default:
        return (
          <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 hover:bg-emerald-100 text-[11px] font-medium">
            Safe
          </Badge>
        );
    }
  };

  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="bg-slate-50/70 border-b border-slate-200 pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <BookOpen className="h-5 w-5 text-emerald-600" />
            <CardTitle className="text-lg">Structured Ingredients ({ingredients.length})</CardTitle>
          </div>
          <Badge variant="outline" className="text-xs bg-white text-slate-700">
            Canonical Knowledge Base
          </Badge>
        </div>
        <CardDescription>
          Ingredients resolved from food packaging labels, categorized by technological function and
          safety evaluation.
        </CardDescription>
      </CardHeader>

      <CardContent className="p-5 space-y-4">
        {ingredients.length === 0 ? (
          <p className="text-sm text-slate-500 italic text-center py-6">
            No structured ingredients mapped for this product yet.
          </p>
        ) : (
          <div className="space-y-3">
            {ingredients.map((item, index) => {
              const ing = item.ingredient;
              return (
                <div
                  key={ing.id || index}
                  className="p-3.5 rounded-lg border border-slate-200 hover:border-slate-300 transition-colors bg-white flex flex-col sm:flex-row sm:items-start justify-between gap-3"
                >
                  {/* Left: order index, name, category, and purpose */}
                  <div className="flex items-start gap-3">
                    <span className="flex-shrink-0 h-6 w-6 rounded-full bg-slate-100 text-slate-600 text-xs font-bold flex items-center justify-center mt-0.5">
                      {item.order_index !== undefined ? item.order_index + 1 : index + 1}
                    </span>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-bold text-slate-900">{ing.name}</span>
                        {ing.ins_number && (
                          <Badge
                            variant="secondary"
                            className="text-[10px] bg-slate-100 text-slate-700 font-mono"
                          >
                            {ing.ins_number}
                          </Badge>
                        )}
                        {ing.category && (
                          <Badge
                            variant="outline"
                            className="text-[10px] text-slate-600 uppercase tracking-wider"
                          >
                            {ing.category}
                          </Badge>
                        )}
                      </div>

                      {/* Ingredient purpose explanation */}
                      {ing.purpose && (
                        <p className="text-xs text-slate-600 leading-relaxed">
                          <strong className="text-slate-700 font-medium">Role:</strong> {ing.purpose}
                        </p>
                      )}

                      {/* Original label wording if different */}
                      {item.original_text && item.original_text !== ing.name && (
                        <p className="text-[11px] text-slate-400 italic">
                          Label text: "{item.original_text}"
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Right: Concern level badge */}
                  <div className="flex-shrink-0 sm:self-center">
                    {getConcernBadge(ing.concern_level)}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Raw Ingredients Text Accordion */}
        {rawText && (
          <div className="pt-2 border-t border-slate-100">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowRawText(!showRawText)}
              className="w-full justify-between text-xs text-slate-600 hover:text-slate-900 px-2"
            >
              <span className="flex items-center gap-1.5 font-medium">
                <FileText className="h-4 w-4 text-slate-500" />
                Original Package Label Ingredient Text
              </span>
              {showRawText ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>

            {showRawText && (
              <div className="mt-2 p-3.5 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700 leading-relaxed font-mono">
                {rawText}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
