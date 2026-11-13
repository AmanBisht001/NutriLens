import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  ShieldQuestion,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Info,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  User,
} from "lucide-react";
import { apiService } from "@/services/api";
import type { PersonalSuitabilityResult, SuitabilityItem } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

// ---------------------------------------------------------------------------
// Status configuration
// ---------------------------------------------------------------------------
const STATUS_CONFIG: Record<
  string,
  {
    icon: React.ElementType;
    badgeClass: string;
    bannerClass: string;
    label: string;
  }
> = {
  "Suitable based on available information": {
    icon: ShieldCheck,
    badgeClass: "bg-emerald-100 text-emerald-800 border-emerald-300",
    bannerClass: "bg-emerald-50 border-emerald-200 text-emerald-900",
    label: "Suitable",
  },
  Caution: {
    icon: ShieldAlert,
    badgeClass: "bg-amber-100 text-amber-800 border-amber-300",
    bannerClass: "bg-amber-50 border-amber-200 text-amber-900",
    label: "Caution",
  },
  "Declared restriction conflict": {
    icon: ShieldX,
    badgeClass: "bg-rose-100 text-rose-800 border-rose-300",
    bannerClass: "bg-rose-50 border-rose-200 text-rose-900",
    label: "Restriction Conflict",
  },
  "Insufficient information": {
    icon: ShieldQuestion,
    badgeClass: "bg-slate-100 text-slate-700 border-slate-300",
    bannerClass: "bg-slate-50 border-slate-200 text-slate-700",
    label: "Insufficient Info",
  },
};

// ---------------------------------------------------------------------------
// Conflict / Caution item row
// ---------------------------------------------------------------------------
const SuitabilityItemRow: React.FC<{ item: SuitabilityItem; variant: "conflict" | "caution" | "positive" }> = ({
  item,
  variant,
}) => {
  const colorMap = {
    conflict: "text-rose-700 bg-rose-50 border-rose-200",
    caution: "text-amber-800 bg-amber-50 border-amber-200",
    positive: "text-emerald-800 bg-emerald-50 border-emerald-200",
  };
  const iconMap = {
    conflict: <ShieldX className="h-3.5 w-3.5 text-rose-600 flex-shrink-0 mt-0.5" />,
    caution: <AlertTriangle className="h-3.5 w-3.5 text-amber-600 flex-shrink-0 mt-0.5" />,
    positive: <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />,
  };

  return (
    <div className={`flex items-start gap-2 p-2.5 rounded-lg border text-xs ${colorMap[variant]}`}>
      {iconMap[variant]}
      <div>
        <span className="font-semibold">{item.title}</span>
        {item.source_ingredient && (
          <span className="ml-1 opacity-75">({item.source_ingredient})</span>
        )}
        <p className="mt-0.5 opacity-80">{item.detail}</p>
        {item.is_precautionary && (
          <span className="inline-block mt-1 px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 text-[10px] font-semibold uppercase tracking-wide">
            May Contain Advisory
          </span>
        )}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
interface PersonalSuitabilityCardProps {
  productId: string;
}

export const PersonalSuitabilityCard: React.FC<PersonalSuitabilityCardProps> = ({ productId }) => {
  const [result, setResult] = useState<PersonalSuitabilityResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showBreakdown, setShowBreakdown] = useState(false);

  const fetchSuitability = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiService.checkProductSuitability(productId);
      setResult(data);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError("Sign in to see your personal suitability assessment.");
      } else if (err.response?.status === 404) {
        setError("Product not found.");
      } else {
        setError("Could not load your personal suitability assessment.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [productId]);

  useEffect(() => {
    fetchSuitability();
  }, [fetchSuitability]);

  // ---- Loading state ----
  if (isLoading) {
    return (
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="pb-2 pt-5 px-5">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <User className="h-4 w-4 text-indigo-500" />
            Personal Suitability
          </CardTitle>
        </CardHeader>
        <CardContent className="px-5 pb-5">
          <div className="flex items-center gap-2 text-sm text-slate-500 py-4">
            <Loader2 className="h-4 w-4 animate-spin" />
            Evaluating against your dietary profile…
          </div>
        </CardContent>
      </Card>
    );
  }

  // ---- Error state ----
  if (error || !result) {
    return (
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="pb-2 pt-5 px-5">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <User className="h-4 w-4 text-indigo-500" />
            Personal Suitability
          </CardTitle>
        </CardHeader>
        <CardContent className="px-5 pb-5 space-y-3">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Info className="h-4 w-4 text-slate-400" />
            {error || "No suitability data available."}
          </div>
          <Button
            variant="outline"
            size="sm"
            className="text-xs"
            onClick={fetchSuitability}
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" /> Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const cfg = STATUS_CONFIG[result.status] ?? STATUS_CONFIG["Insufficient information"];
  const StatusIcon = cfg.icon;

  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="pb-3 pt-5 px-5">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <User className="h-4 w-4 text-indigo-500" />
            Personal Suitability
          </CardTitle>
          <Badge className={`text-xs px-3 py-1 font-semibold flex items-center gap-1.5 border ${cfg.badgeClass}`}>
            <StatusIcon className="h-3.5 w-3.5" />
            {cfg.label}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="px-5 pb-5 space-y-4">
        {/* Status banner with narrative */}
        <div className={`p-3.5 rounded-xl border text-sm flex items-start gap-2.5 ${cfg.bannerClass}`}>
          <StatusIcon className="h-4 w-4 flex-shrink-0 mt-0.5" />
          <span>{result.summary_narrative}</span>
        </div>

        {/* Conflicts */}
        {result.conflicts.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs font-semibold text-rose-700 uppercase tracking-wider">
              Declared Restriction Conflicts ({result.conflicts.length})
            </p>
            {result.conflicts.map((item, i) => (
              <SuitabilityItemRow key={i} item={item} variant="conflict" />
            ))}
          </div>
        )}

        {/* Cautions */}
        {result.cautions.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs font-semibold text-amber-700 uppercase tracking-wider">
              Cautions &amp; Advisories ({result.cautions.length})
            </p>
            {result.cautions.map((item, i) => (
              <SuitabilityItemRow key={i} item={item} variant="caution" />
            ))}
          </div>
        )}

        {/* Positive observations */}
        {result.positive_observations.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">
              Aligned with Your Goals ({result.positive_observations.length})
            </p>
            {result.positive_observations.map((item, i) => (
              <SuitabilityItemRow key={i} item={item} variant="positive" />
            ))}
          </div>
        )}

        {/* Safety warnings */}
        {result.safety_warnings.length > 0 && (
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            {result.safety_warnings.map((w, i) => (
              <p key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                <AlertTriangle className="h-3 w-3 text-slate-400 flex-shrink-0 mt-0.5" />
                {w}
              </p>
            ))}
          </div>
        )}

        {/* Evaluated preferences chips */}
        {result.evaluated_preferences && (
          <div className="space-y-2 pt-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Evaluated Against Your Profile
            </p>
            <div className="flex flex-wrap gap-1.5">
              {result.evaluated_preferences.dietary_preference &&
                result.evaluated_preferences.dietary_preference !== "none" && (
                  <Badge variant="outline" className="text-xs text-indigo-700 border-indigo-200 bg-indigo-50">
                    {result.evaluated_preferences.dietary_preference}
                  </Badge>
                )}
              {result.evaluated_preferences.allergies.map((a) => (
                <Badge key={a} variant="outline" className="text-xs text-amber-800 border-amber-200 bg-amber-50">
                  ⚠ {a}
                </Badge>
              ))}
              {result.evaluated_preferences.dietary_restrictions.map((r) => (
                <Badge key={r} variant="outline" className="text-xs text-slate-700 border-slate-200 bg-slate-50">
                  {r}
                </Badge>
              ))}
              {result.evaluated_preferences.nutrition_goals.map((g) => (
                <Badge key={g} variant="outline" className="text-xs text-rose-700 border-rose-200 bg-rose-50">
                  ♥ {g}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Score independence note */}
        <div className="flex items-center justify-between pt-1 border-t border-slate-100">
          <p className="text-[11px] text-slate-400 italic">
            General NutriLens score is independent of your personal profile.
          </p>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-slate-500 h-7 px-2"
            onClick={() => setShowBreakdown((v) => !v)}
          >
            {showBreakdown ? (
              <>
                <ChevronUp className="h-3.5 w-3.5 mr-1" /> Hide Details
              </>
            ) : (
              <>
                <ChevronDown className="h-3.5 w-3.5 mr-1" /> Engine Details
              </>
            )}
          </Button>
        </div>

        {/* Collapsible engine details */}
        {showBreakdown && (
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600 space-y-1">
            <p>
              <span className="font-semibold">Engine Version:</span> {result.engine_version}
            </p>
            {result.rules_applied.length > 0 && (
              <p>
                <span className="font-semibold">Rules Applied:</span> {result.rules_applied.join(", ")}
              </p>
            )}
            <p className="text-slate-400 italic mt-1">{result.disclaimer}</p>
          </div>
        )}

        {/* Safety disclaimer */}
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
          <p className="text-[11px] text-slate-500 italic">
            ⚠ Not detecting an allergen does not prove that the product is allergen-free. This is not medical advice.
            Always read the full product label.{" "}
            <Link to="/profile" className="underline text-indigo-600 hover:text-indigo-800">
              Update your preferences
            </Link>
            .
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
