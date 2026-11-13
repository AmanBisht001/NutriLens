import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Users,
  Package,
  CheckCircle2,
  Beaker,
  ScanLine,
  Sliders,
  Flag,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { api } from "@/services/api";
import { AdminDashboardStats } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const AdminDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getAdminStats();
      setStats(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load admin statistics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b pb-6">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200 font-semibold px-2.5 py-0.5 text-xs">
              <ShieldCheck className="h-3.5 w-3.5 mr-1 text-purple-600" />
              Administrative Command Center
            </Badge>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight mt-2">
            NutriLens Knowledge & Platform Administration
          </h1>
          <p className="text-slate-600 text-sm mt-1">
            Real-time database statistics, product verification, ingredient registry, scoring versioning, and community issue review.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchStats}
            disabled={loading}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh Data
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center justify-between">
          <span>{error}</span>
          <Button variant="outline" size="sm" onClick={fetchStats} className="bg-white">
            Retry
          </Button>
        </div>
      )}

      {/* Primary KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Total Users */}
        <Card className="shadow-sm border-slate-200 hover:shadow transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Total Users
            </CardTitle>
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
              <Users className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-slate-900">
              {loading ? "..." : stats?.total_users.toLocaleString() ?? 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">Registered consumer accounts</p>
          </CardContent>
        </Card>

        {/* Total Products */}
        <Card className="shadow-sm border-slate-200 hover:shadow transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Catalogued Products
            </CardTitle>
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
              <Package className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-slate-900">
              {loading ? "..." : stats?.total_products.toLocaleString() ?? 0}
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-500 mt-1">
              <span className="text-emerald-700 font-medium flex items-center gap-0.5">
                <CheckCircle2 className="h-3 w-3" /> {stats?.verified_products ?? 0} verified
              </span>
              <span>•</span>
              <span className="text-amber-700 font-medium">
                {stats?.unverified_products ?? 0} unverified
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Total Ingredients */}
        <Card className="shadow-sm border-slate-200 hover:shadow transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Ingredient Registry
            </CardTitle>
            <div className="p-2 rounded-lg bg-amber-50 text-amber-600">
              <Beaker className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-slate-900">
              {loading ? "..." : stats?.total_ingredients.toLocaleString() ?? 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">Standardized taxonomy & aliases</p>
          </CardContent>
        </Card>

        {/* Total Scans */}
        <Card className="shadow-sm border-slate-200 hover:shadow transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              OCR Label Scans
            </CardTitle>
            <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
              <ScanLine className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-slate-900">
              {loading ? "..." : stats?.total_scans.toLocaleString() ?? 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">Processed food labels</p>
          </CardContent>
        </Card>
      </div>

      {/* Secondary Status Row: Scoring Engine Rule & Reported Issues */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Active Scoring Rule Banner */}
        <Card className="shadow-sm border-slate-200 bg-gradient-to-br from-purple-50/50 via-white to-slate-50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Sliders className="h-5 w-5 text-purple-600" />
                <CardTitle className="text-base font-bold text-slate-900">Scoring Engine Status</CardTitle>
              </div>
              <Badge className="bg-purple-600 text-white font-mono text-xs">
                {stats?.active_scoring_rule_version || "Default v1.0"}
              </Badge>
            </div>
            <CardDescription className="text-xs">
              Deterministic NutriLens score computation version currently applied to all product analyses.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-600 leading-relaxed">
              NutriLens scores are calculated using strictly immutable rule sets with configurable nutrient cutoffs and category weights. Creating a new rule version preserves all historic scores.
            </p>
            <div className="pt-2">
              <Link to="/admin/scoring-rules">
                <Button size="sm" variant="outline" className="text-purple-700 border-purple-200 hover:bg-purple-50">
                  Manage Scoring Rules & Weights <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* User-Reported Data Issues */}
        <Card className="shadow-sm border-slate-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Flag className="h-5 w-5 text-amber-600" />
                <CardTitle className="text-base font-bold text-slate-900">Community Issue Queue</CardTitle>
              </div>
              <Badge variant={stats && stats.pending_issues > 0 ? "destructive" : "secondary"}>
                {stats?.pending_issues ?? 0} Pending
              </Badge>
            </div>
            <CardDescription className="text-xs">
              User-submitted reports regarding inaccurate ingredients, OCR misreads, or incorrect nutrition tables.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-2 py-2 text-center bg-slate-50 rounded-lg border border-slate-100">
              <div>
                <p className="text-lg font-bold text-amber-600">{stats?.pending_issues ?? 0}</p>
                <p className="text-[11px] text-slate-500 uppercase tracking-wide">Awaiting Review</p>
              </div>
              <div>
                <p className="text-lg font-bold text-emerald-600">{stats?.resolved_issues ?? 0}</p>
                <p className="text-[11px] text-slate-500 uppercase tracking-wide">Resolved</p>
              </div>
              <div>
                <p className="text-lg font-bold text-slate-800">{stats?.total_issues ?? 0}</p>
                <p className="text-[11px] text-slate-500 uppercase tracking-wide">Total Submissions</p>
              </div>
            </div>
            <div className="pt-1">
              <Link to="/admin/issues">
                <Button size="sm" variant="outline" className="text-amber-800 border-amber-200 hover:bg-amber-50">
                  Review Reported Data Issues <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Catalog Category Distribution Breakdown */}
      {stats?.category_breakdown && Object.keys(stats.category_breakdown).length > 0 && (
        <Card className="shadow-sm border-slate-200">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-900">Products by Category</CardTitle>
            <CardDescription className="text-xs">
              Live count of verified and unverified packaged items across all product classifications.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {Object.entries(stats.category_breakdown).map(([category, count]) => (
                <div
                  key={category}
                  className="p-3 rounded-lg border border-slate-100 bg-slate-50/80 flex flex-col justify-between"
                >
                  <span className="text-xs font-semibold text-slate-700 capitalize truncate" title={category}>
                    {category}
                  </span>
                  <span className="text-xl font-bold text-emerald-700 mt-2">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Management Navigation Hub */}
      <div>
        <h2 className="text-lg font-bold text-slate-900 mb-4">Administration Workflows</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Link
            to="/admin/products"
            className="p-5 rounded-xl border border-slate-200 bg-white hover:border-emerald-400 hover:shadow-md transition-all group"
          >
            <div className="h-10 w-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
              <Package className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-sm group-hover:text-emerald-700">Product Management</h3>
            <p className="text-xs text-slate-500 mt-1">
              Add, edit, verify nutrition facts, assign categories, and manage ingredient bindings.
            </p>
          </Link>

          <Link
            to="/admin/ingredients"
            className="p-5 rounded-xl border border-slate-200 bg-white hover:border-amber-400 hover:shadow-md transition-all group"
          >
            <div className="h-10 w-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center mb-3 group-hover:bg-amber-600 group-hover:text-white transition-colors">
              <Beaker className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-sm group-hover:text-amber-700">Ingredient Taxonomy</h3>
            <p className="text-xs text-slate-500 mt-1">
              Maintain standardized names, concern levels, INS numbers, source evidence, and allergens.
            </p>
          </Link>

          <Link
            to="/admin/scoring-rules"
            className="p-5 rounded-xl border border-slate-200 bg-white hover:border-purple-400 hover:shadow-md transition-all group"
          >
            <div className="h-10 w-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center mb-3 group-hover:bg-purple-600 group-hover:text-white transition-colors">
              <Sliders className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-sm group-hover:text-purple-700">Scoring Engine</h3>
            <p className="text-xs text-slate-500 mt-1">
              Configure thresholds, weights, and versioning rules with mathematical validation.
            </p>
          </Link>

          <Link
            to="/admin/issues"
            className="p-5 rounded-xl border border-slate-200 bg-white hover:border-indigo-400 hover:shadow-md transition-all group"
          >
            <div className="h-10 w-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
              <Flag className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-sm group-hover:text-indigo-700">Report Review</h3>
            <p className="text-xs text-slate-500 mt-1">
              Resolve user-flagged nutrition and label errors with audit tracking notes.
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
};
