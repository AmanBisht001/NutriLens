import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Sparkles,
  ArrowRight,
  ArrowLeftRight,
  TrendingUp,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { apiService } from "@/services/api";
import type { ProductAlternativesResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface AlternativeRecommendationsCardProps {
  productId: string;
  currentProductName?: string;
  limit?: number;
}

export const AlternativeRecommendationsCard: React.FC<AlternativeRecommendationsCardProps> = ({
  productId,
  currentProductName: _currentProductName,
  limit = 3,
}) => {
  const navigate = useNavigate();
  const [data, setData] = useState<ProductAlternativesResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!productId) return;

    const fetchAlternatives = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const resp = await apiService.getProductAlternatives(productId, undefined, limit);
        setData(resp);
      } catch (err: any) {
        console.error("Failed to load alternatives:", err);
        setError("Could not load alternative recommendations.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchAlternatives();
  }, [productId, limit]);

  if (isLoading) {
    return (
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-6 flex items-center justify-center gap-2 text-slate-500 text-sm">
          <Loader2 className="h-4 w-4 animate-spin text-emerald-600" />
          Analyzing healthier catalogue alternatives...
        </CardContent>
      </Card>
    );
  }

  if (error || !data || data.alternatives.length === 0) {
    return null; // Don't show card if no valid alternatives exist in catalogue
  }

  return (
    <Card className="border-slate-200 shadow-sm overflow-hidden">
      <CardHeader className="bg-slate-50/70 border-b border-slate-100 p-5">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-slate-900">
                Personalized Alternative Recommendations
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Healthier, diet-compatible alternatives from our verified catalogue
              </CardDescription>
            </div>
          </div>
          <Badge variant="outline" className="text-xs bg-white text-emerald-800 border-emerald-300 font-semibold">
            {data.alternatives.length} Alternatives Found
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.alternatives.map((alt) => {
            const hasScore = alt.score !== null && alt.score !== undefined;

            return (
              <div
                key={alt.product_id}
                className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col justify-between hover:border-emerald-300 hover:shadow-xs transition-all space-y-3"
              >
                <div className="space-y-2">
                  {/* Top Badge Row */}
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider truncate">
                      {alt.brand || "Brand"}
                    </span>
                    {hasScore && (
                      <Badge
                        className={`text-xs px-2 py-0.5 font-bold ${
                          alt.score! >= 75
                            ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                            : alt.score! >= 50
                            ? "bg-amber-100 text-amber-800 border-amber-300"
                            : "bg-rose-100 text-rose-800 border-rose-300"
                        }`}
                      >
                        Score: {alt.score}/100
                      </Badge>
                    )}
                  </div>

                  {/* Product Title */}
                  <Link
                    to={`/products/${alt.product_id}`}
                    className="text-sm font-bold text-slate-900 hover:text-emerald-700 line-clamp-2 transition-colors"
                  >
                    {alt.name}
                  </Link>

                  {/* Category and Suitability */}
                  <div className="flex flex-wrap gap-1 text-[11px]">
                    {alt.category && (
                      <Badge variant="outline" className="py-0 px-1.5 text-slate-600 bg-slate-50 border-slate-200">
                        {alt.category}
                      </Badge>
                    )}
                    <Badge
                      variant="outline"
                      className={`py-0 px-1.5 font-medium ${
                        alt.suitability_badge === "emerald"
                          ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                          : "bg-amber-50 text-amber-800 border-amber-200"
                      }`}
                    >
                      {alt.suitability_status === "Suitable based on available information"
                        ? "Suitable"
                        : "Caution"}
                    </Badge>
                  </div>

                  {/* Traceable Reasons */}
                  <div className="pt-2 border-t border-slate-100 space-y-1">
                    <p className="text-[11px] font-semibold text-slate-700 uppercase tracking-wider">
                      Why this alternative:
                    </p>
                    {alt.reasons.slice(0, 2).map((r, i) => (
                      <p key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
                        <span>{r}</span>
                      </p>
                    ))}
                    {alt.nutritional_advantages.slice(0, 1).map((adv, i) => (
                      <p key={i} className="text-xs text-indigo-700 font-medium flex items-start gap-1.5">
                        <TrendingUp className="h-3.5 w-3.5 text-indigo-600 flex-shrink-0 mt-0.5" />
                        <span>{adv}</span>
                      </p>
                    ))}
                  </div>
                </div>

                {/* Bottom Action Buttons */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                  <Button
                    asChild
                    variant="ghost"
                    size="sm"
                    className="text-xs text-slate-600 hover:text-emerald-700 px-2 h-8"
                  >
                    <Link to={`/products/${alt.product_id}`}>
                      View Details <ArrowRight className="h-3 w-3 ml-1" />
                    </Link>
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => navigate(`/compare?products=${productId},${alt.product_id}`)}
                    className="text-xs border-emerald-600 text-emerald-700 hover:bg-emerald-50 h-8 px-2.5"
                  >
                    <ArrowLeftRight className="h-3 w-3 mr-1" /> Compare
                  </Button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Traceability Notice */}
        <p className="text-[11px] text-slate-400 italic">
          ℹ Recommendations are deterministically ranked based on higher NutriLens scores, reduced sugar/sodium,
          and compatibility with your declared dietary profile. No fabricated records are used.
        </p>
      </CardContent>
    </Card>
  );
};
