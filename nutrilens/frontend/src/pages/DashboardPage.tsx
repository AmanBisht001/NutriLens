import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ScanLine,
  Camera,
  Search,
  ShieldCheck,
  AlertTriangle,
  Sparkles,
  BookMarked,
  Heart,
  Activity,
  Layers,
  ChevronRight,
  RefreshCw,
  Clock,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/services/api";
import type { ScanHistoryItem } from "@/types";

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const dietaryPreference = user?.profile?.dietary_preference || "None";
  const allergies = user?.profile?.allergies || [];
  const restrictions = user?.profile?.dietary_restrictions || [];
  const goals = user?.profile?.nutrition_goals || [];

  // Fetch real scan history from backend
  const {
    data: scanHistoryData,
    isLoading: isLoadingScans,
    isError: isScansError,
    error: scansError,
    refetch: refetchScans,
  } = useQuery({
    queryKey: ["scan-history", user?.id],
    queryFn: () => api.getScanHistory(1, 5),
    enabled: !!user,
  });

  const recentScans: ScanHistoryItem[] = scanHistoryData?.items || [];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto w-full">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-emerald-700 via-emerald-600 to-teal-700 rounded-2xl p-6 sm:p-8 text-white shadow-md relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 opacity-10 pointer-events-none hidden md:flex items-center pr-8">
          <ShieldCheck className="h-64 w-64 text-white" />
        </div>

        <div className="relative z-10 max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur text-white text-xs font-medium">
            <Sparkles className="h-3.5 w-3.5 text-emerald-200" />
            <span>NutriLens Food Intelligence Active</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Welcome back, {user?.full_name?.split(" ")[0] || "there"}!
          </h1>

          <p className="text-emerald-100 text-sm sm:text-base leading-relaxed">
            Your personalized food scanner is ready. Every product you scan will be automatically verified
            against your dietary rules, allergens, and personal nutrition goals.
          </p>

          {/* Quick Dietary Tags Pill Row */}
          <div className="pt-2 flex flex-wrap items-center gap-2">
            <span className="text-xs text-emerald-200 font-medium">Active Guardrails:</span>
            {dietaryPreference !== "None" ? (
              <Badge className="bg-white/20 text-white hover:bg-white/30 border-none text-xs">
                {dietaryPreference}
              </Badge>
            ) : (
              <Badge className="bg-white/20 text-white hover:bg-white/30 border-none text-xs">
                No Diet Specified
              </Badge>
            )}

            {allergies.length > 0 ? (
              <Badge className="bg-amber-400 text-amber-950 font-semibold border-none text-xs">
                {allergies.length} {allergies.length === 1 ? "Allergy" : "Allergies"} Monitored
              </Badge>
            ) : (
              <Badge className="bg-white/20 text-white hover:bg-white/30 border-none text-xs">
                No Allergies Set
              </Badge>
            )}

            <Link
              to="/profile"
              className="text-xs text-emerald-100 hover:text-white underline underline-offset-2 ml-1"
            >
              Update preferences
            </Link>
          </div>
        </div>
      </div>

      {/* Quick Scan Action Hero Card */}
      <Card className="border-emerald-200 bg-gradient-to-br from-emerald-50/60 via-white to-white shadow-sm">
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div className="space-y-1.5 max-w-xl">
              <div className="flex items-center space-x-2 text-emerald-700 font-semibold text-xs tracking-wider uppercase">
                <ScanLine className="h-4 w-4" />
                <span>Instant Ingredient Analysis</span>
              </div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                Scan Food Product or Nutrition Label
              </h2>
              <p className="text-sm text-slate-600">
                Capture the ingredient list or barcode on any packaged grocery product to instantly reveal
                hidden allergens, NOVA ultra-processed grades, and nutritional quality scores.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Button
                asChild
                className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm font-semibold"
              >
                <Link to="/scan">
                  <Camera className="h-4 w-4 mr-2" />
                  Scan Food Now
                </Link>
              </Button>
              <Button asChild variant="outline" className="border-slate-300">
                <Link to="/catalogue">
                  <Search className="h-4 w-4 mr-2" />
                  Browse Catalogue
                </Link>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Grid: Recently Scanned Products & Nutrition Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recently Scanned Products Section */}
        <Card className="border-slate-200 shadow-sm flex flex-col">
          <CardHeader className="pb-3 border-b bg-slate-50/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <ScanLine className="h-5 w-5 text-emerald-600" />
                <CardTitle className="text-base font-bold">Recently Scanned Products</CardTitle>
              </div>
              <Button
                variant="ghost"
                size="sm"
                asChild
                className="h-7 text-xs text-slate-600 hover:text-emerald-700 hover:bg-emerald-50 px-2"
              >
                <Link to="/scan">
                  <span>Live Scanner</span>
                  <ChevronRight className="h-3.5 w-3.5 ml-1" />
                </Link>
              </Button>
            </div>
            <CardDescription>
              Chronological log of items scanned via OCR or packaging reader.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 p-0">
            {isLoadingScans ? (
              <div className="flex flex-col items-center justify-center p-8 space-y-3">
                <RefreshCw className="h-6 w-6 text-emerald-600 animate-spin" />
                <p className="text-sm text-slate-500">Loading your scanned items...</p>
              </div>
            ) : isScansError ? (
              <div className="p-8 text-center flex flex-col items-center justify-center">
                <div className="h-12 w-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center mb-3">
                  <AlertTriangle className="h-6 w-6" />
                </div>
                <h4 className="text-sm font-semibold text-slate-800">Failed to load scan history</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-xs">
                  {(scansError as any)?.message || "A network or server error occurred."}
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => refetchScans()}
                  className="mt-4 text-xs h-8"
                >
                  <RefreshCw className="h-3.5 w-3.5 mr-1" /> Retry
                </Button>
              </div>
            ) : recentScans.length === 0 ? (
              /* Genuine Empty State (No Fabricated Statistics) */
              <div className="flex flex-col items-center justify-center p-8 text-center">
                <div className="h-14 w-14 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 mb-4 shadow-xs">
                  <Layers className="h-7 w-7" />
                </div>
                <h3 className="text-base font-semibold text-slate-900">
                  No products scanned yet
                </h3>
                <p className="text-sm text-slate-500 max-w-sm mt-1.5 leading-relaxed">
                  When you scan food packages or upload nutrition labels, your product history and compatibility
                  breakdowns will appear here.
                </p>
                <Button asChild size="sm" className="mt-5 bg-emerald-600 hover:bg-emerald-700 text-white">
                  <Link to="/scan">
                    <Camera className="h-4 w-4 mr-1.5" />
                    Scan First Product
                  </Link>
                </Button>
              </div>
            ) : (
              /* Real List of Scanned Products */
              <div className="divide-y divide-slate-100">
                {recentScans.map((scan) => {
                  const scoreBadgeColor =
                    scan.grade === "A"
                      ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                      : scan.grade === "B"
                      ? "bg-green-100 text-green-800 border-green-300"
                      : scan.grade === "C"
                      ? "bg-amber-100 text-amber-800 border-amber-300"
                      : scan.grade === "D"
                      ? "bg-orange-100 text-orange-800 border-orange-300"
                      : scan.grade === "E"
                      ? "bg-rose-100 text-rose-800 border-rose-300"
                      : "bg-slate-100 text-slate-700 border-slate-300";

                  const formattedDate = scan.created_at
                    ? new Date(scan.created_at).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : "Recently";

                  return (
                    <div
                      key={scan.id}
                      onClick={() => navigate(`/scan?id=${scan.id}`)}
                      className="p-4 flex items-center justify-between hover:bg-slate-50 transition cursor-pointer group"
                    >
                      <div className="flex items-center space-x-3.5 min-w-0">
                        {scan.image_url ? (
                          <img
                            src={scan.image_url}
                            alt={scan.product_name}
                            className="h-12 w-12 rounded-lg object-cover border border-slate-200 bg-white shrink-0"
                          />
                        ) : (
                          <div className="h-12 w-12 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 shrink-0">
                            <Camera className="h-6 w-6" />
                          </div>
                        )}
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-slate-900 truncate group-hover:text-emerald-700 transition">
                            {scan.product_name || "Unknown Product"}
                          </p>
                          <div className="flex items-center space-x-2 text-xs text-slate-500 mt-0.5">
                            {scan.brand && (
                              <span className="font-medium text-slate-700">{scan.brand} •</span>
                            )}
                            <span className="flex items-center">
                              <Clock className="h-3 w-3 mr-1 inline" />
                              {formattedDate}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 shrink-0 ml-3">
                        {scan.score !== null && scan.score !== undefined ? (
                          <div className="text-right">
                            <Badge className={`text-xs font-bold border px-2 py-0.5 ${scoreBadgeColor}`}>
                              {scan.score}/100 ({scan.grade || "Score"})
                            </Badge>
                          </div>
                        ) : (
                          <Badge variant="outline" className="text-xs text-slate-500 border-slate-200">
                            Nutrients N/A
                          </Badge>
                        )}
                        <ChevronRight className="h-4 w-4 text-slate-400 group-hover:text-emerald-600 transition" />
                      </div>
                    </div>
                  );
                })}

                <div className="p-3 bg-slate-50/50 border-t border-slate-100 text-center">
                  <Button
                    variant="ghost"
                    size="sm"
                    asChild
                    className="text-xs text-emerald-700 hover:text-emerald-800 hover:bg-emerald-50 w-full"
                  >
                    <Link to="/scan">
                      <Camera className="h-3.5 w-3.5 mr-1.5" />
                      Scan Another Product
                    </Link>
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Nutrition Summary Section */}
        <Card className="border-slate-200 shadow-sm flex flex-col">
          <CardHeader className="pb-3 border-b bg-slate-50/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-emerald-600" />
                <CardTitle className="text-base font-bold">Nutrition & Health Summary</CardTitle>
              </div>
              <Badge variant="outline" className="text-xs text-slate-500">
                Daily Intake
              </Badge>
            </div>
            <CardDescription>
              Aggregated macronutrients and dietary goal progress.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col items-center justify-center p-8 text-center">
            {/* Genuine Empty State (No Fabricated Statistics) */}
            <div className="h-14 w-14 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-500 mb-4 shadow-xs">
              <BookMarked className="h-7 w-7" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">
              No logged nutrition data
            </h3>
            <p className="text-sm text-slate-500 max-w-sm mt-1.5 leading-relaxed">
              Calories, sodium levels, sugar content, and personalized suitability metrics will be
              calculated as you log consumed food items in your Food Journal.
            </p>
            <Button asChild variant="outline" size="sm" className="mt-5 border-slate-300">
              <Link to="/journal">
                <BookMarked className="h-4 w-4 mr-1.5" />
                View Food Journal
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Personalized Health Snapshot Row */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="pb-3 border-b bg-slate-50/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="h-5 w-5 text-emerald-600" />
              <CardTitle className="text-base font-bold">Your Configured Dietary Safeguards</CardTitle>
            </div>
            <Link
              to="/profile"
              className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
            >
              <span>Edit Settings</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Allergens Column */}
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-800 uppercase tracking-wider">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
                <span>Monitored Allergens ({allergies.length})</span>
              </div>
              {allergies.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {allergies.map((allergy) => (
                    <Badge
                      key={allergy}
                      variant="secondary"
                      className="bg-amber-50 text-amber-900 border border-amber-200 text-xs"
                    >
                      {allergy}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">
                  No allergens flagged. You can add allergies in your profile.
                </p>
              )}
            </div>

            {/* Dietary Restrictions Column */}
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-800 uppercase tracking-wider">
                <ShieldCheck className="h-3.5 w-3.5 text-indigo-600" />
                <span>Restrictions ({restrictions.length})</span>
              </div>
              {restrictions.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {restrictions.map((r) => (
                    <Badge
                      key={r}
                      variant="secondary"
                      className="bg-indigo-50 text-indigo-900 border border-indigo-200 text-xs"
                    >
                      {r}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">
                  No dietary restrictions configured.
                </p>
              )}
            </div>

            {/* Nutrition Goals Column */}
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-800 uppercase tracking-wider">
                <Heart className="h-3.5 w-3.5 text-rose-600" />
                <span>Personal Goals ({goals.length})</span>
              </div>
              {goals.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {goals.map((g) => (
                    <Badge
                      key={g}
                      variant="secondary"
                      className="bg-rose-50 text-rose-900 border border-rose-200 text-xs"
                    >
                      {g}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">
                  No specific nutrition goals set yet.
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
