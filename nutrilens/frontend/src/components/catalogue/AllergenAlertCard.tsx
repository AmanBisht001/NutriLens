import React from "react";
import { AlertTriangle, ShieldCheck, ShieldAlert } from "lucide-react";
import type { ProductAllergen } from "@/types";
import { useAuth } from "@/context/AuthContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface AllergenAlertCardProps {
  allergens: ProductAllergen[];
}

export const AllergenAlertCard: React.FC<AllergenAlertCardProps> = ({ allergens }) => {
  const { user } = useAuth();
  const userAllergies = user?.profile?.allergies || [];

  // Find declared allergens and precautionary allergens
  const declared = allergens.filter((a) => a.declaration_type === "declared");
  const precautionary = allergens.filter((a) => a.declaration_type === "precautionary");

  // Check if any product allergen matches user's monitored allergies
  const matchingAllergies = allergens.filter((pa) =>
    userAllergies.some((userAllergy) =>
      pa.allergen.name.toLowerCase().includes(userAllergy.toLowerCase()) ||
      userAllergy.toLowerCase().includes(pa.allergen.name.toLowerCase())
    )
  );

  return (
    <div className="space-y-4">
      {/* High-priority Personal Allergen Alert if product matches user's profile allergies */}
      {matchingAllergies.length > 0 && (
        <div className="p-4 rounded-xl bg-rose-50 border-2 border-rose-300 flex items-start space-x-3 text-rose-900 shadow-sm animate-in fade-in">
          <ShieldAlert className="h-6 w-6 text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-bold text-base text-rose-950">
              Personal Allergy Warning Detected!
            </h4>
            <p className="text-xs text-rose-800 leading-relaxed">
              This product contains or may contain allergens flagged in your profile:
            </p>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {matchingAllergies.map((match) => (
                <Badge
                  key={match.allergen.id}
                  className="bg-rose-600 text-white font-bold text-xs"
                >
                  {match.allergen.name} ({match.declaration_type})
                </Badge>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* General Allergen Information Card */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="bg-slate-50/70 border-b border-slate-200 pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              <CardTitle className="text-lg">Allergen Declarations</CardTitle>
            </div>
            <Badge
              variant="outline"
              className={
                allergens.length > 0
                  ? "bg-amber-50 text-amber-900 border-amber-300 font-semibold"
                  : "bg-emerald-50 text-emerald-800 border-emerald-300 font-medium"
              }
            >
              {allergens.length > 0 ? `${allergens.length} Flagged` : "None Declared"}
            </Badge>
          </div>
          <CardDescription>
            Regulatory allergen warnings declared by the manufacturer on the package.
          </CardDescription>
        </CardHeader>

        <CardContent className="p-5 space-y-4">
          {allergens.length === 0 ? (
            <div className="flex items-center gap-2 p-3 bg-emerald-50/60 rounded-lg text-xs text-emerald-800">
              <ShieldCheck className="h-4 w-4 text-emerald-600 flex-shrink-0" />
              <span>No major food allergens are explicitly declared on this package label.</span>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Explicitly Declared Allergens ("Contains: ...") */}
              {declared.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Contains (Declared):
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {declared.map((pa) => (
                      <Badge
                        key={pa.allergen.id}
                        variant="secondary"
                        className="bg-amber-100 text-amber-950 border border-amber-300 px-3 py-1 text-xs font-semibold"
                      >
                        {pa.allergen.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Precautionary Allergens ("May contain: ...") */}
              {precautionary.length > 0 && (
                <div className="space-y-1.5 pt-2 border-t border-slate-100">
                  <span className="text-xs font-medium text-slate-600 uppercase tracking-wider">
                    May Contain (Cross-Contact Precaution):
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {precautionary.map((pa) => (
                      <Badge
                        key={pa.allergen.id}
                        variant="outline"
                        className="bg-slate-50 text-slate-700 border-slate-200 px-2.5 py-0.5 text-xs"
                      >
                        {pa.allergen.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
