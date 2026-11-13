import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  ArrowLeftRight,
  BookMarked,
  ShieldCheck,
  Scale,
  Barcode,
  Layers,
  Loader2,
  AlertCircle,
  Info,
  Flag,
} from "lucide-react";
import { api, apiService } from "@/services/api";
import type { ProductDetail } from "@/types";
import { NutritionalFactsCard } from "@/components/catalogue/NutritionalFactsCard";
import { IngredientListCard } from "@/components/catalogue/IngredientListCard";
import { AllergenAlertCard } from "@/components/catalogue/AllergenAlertCard";
import { NutritionScoreAnalysisCard } from "@/components/catalogue/NutritionScoreAnalysisCard";
import { PersonalSuitabilityCard } from "@/components/catalogue/PersonalSuitabilityCard";
import { AlternativeRecommendationsCard } from "@/components/comparison/AlternativeRecommendationsCard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const ProductDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const fetchProduct = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiService.getProduct(id);
        setProduct(data);
      } catch (err: any) {
        setError(
          err.response?.status === 404
            ? "Product not found in the catalogue."
            : "Failed to load product details. Please try again."
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchProduct();
  }, [id]);

  // Report Issue Modal State
  const [reportModalOpen, setReportModalOpen] = useState<boolean>(false);
  const [reportType, setReportType] = useState<string>("incorrect_ingredients");
  const [reportDesc, setReportDesc] = useState<string>("");
  const [reportSubmitting, setReportSubmitting] = useState<boolean>(false);
  const [reportSuccess, setReportSuccess] = useState<boolean>(false);

  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!product || !reportDesc.trim()) return;

    try {
      setReportSubmitting(true);
      await api.reportProductIssue(product.id, {
        issue_type: reportType,
        description: reportDesc.trim(),
      });
      setReportSuccess(true);
      setTimeout(() => {
        setReportSuccess(false);
        setReportModalOpen(false);
        setReportDesc("");
      }, 2000);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to submit issue report. Please log in first.");
    } finally {
      setReportSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-3">
        <Loader2 className="h-8 w-8 text-emerald-600 animate-spin" />
        <p className="text-sm text-slate-500 font-medium">Loading product profile...</p>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="p-8 max-w-xl mx-auto text-center space-y-4">
        <div className="h-14 w-14 rounded-2xl bg-red-50 text-red-600 mx-auto flex items-center justify-center">
          <AlertCircle className="h-8 w-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Product Not Found</h2>
        <p className="text-sm text-slate-600">{error || "Could not retrieve this product."}</p>
        <Button asChild className="bg-emerald-600 hover:bg-emerald-700 text-white">
          <Link to="/catalogue">
            <ArrowLeft className="h-4 w-4 mr-1.5" /> Return to Catalogue
          </Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Back button & Breadcrumb */}
      <div className="flex items-center space-x-2 text-sm text-slate-500">
        <Link
          to="/catalogue"
          className="hover:text-emerald-700 font-medium flex items-center gap-1 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Catalogue
        </Link>
        <span>/</span>
        <span className="text-slate-400">{product.category || "Product"}</span>
        <span>/</span>
        <span className="text-slate-700 font-semibold truncate max-w-xs">{product.name}</span>
      </div>

      {/* Hero Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider">
                {product.brand || "Generic Brand"}
              </span>
              {product.category && (
                <Badge variant="outline" className="text-xs bg-slate-50 text-slate-700 border-slate-200">
                  {product.category}
                </Badge>
              )}
              {product.is_demo_data && (
                <Badge
                  variant="outline"
                  className="text-xs bg-amber-50 text-amber-900 border-amber-300 font-semibold"
                >
                  Demonstration Record
                </Badge>
              )}
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {product.name}
            </h1>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <Button
              asChild
              variant="outline"
              size="sm"
              className="text-xs border-emerald-600 text-emerald-700 hover:bg-emerald-50 h-8 font-semibold"
            >
              <Link to="/journal" state={{ logProduct: product }}>
                <BookMarked className="h-3.5 w-3.5 mr-1.5" /> Log in Journal
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              size="sm"
              className="text-xs border-slate-300 text-slate-700 hover:bg-slate-50 h-8 font-semibold"
            >
              <Link to={`/compare?products=${product.id}`}>
                <ArrowLeftRight className="h-3.5 w-3.5 mr-1.5" /> Compare Product
              </Link>
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setReportModalOpen(true)}
              className="text-xs border-amber-300 text-amber-800 hover:bg-amber-50 h-8 font-semibold"
            >
              <Flag className="h-3.5 w-3.5 mr-1.5 text-amber-600" /> Report Issue
            </Button>
            {product.is_verified ? (
              <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 text-xs px-3 py-1 flex items-center gap-1.5 font-semibold">
                <ShieldCheck className="h-4 w-4 text-emerald-700" />
                Laboratory Verified
              </Badge>
            ) : (
              <Badge
                variant="secondary"
                className="text-xs text-slate-600 bg-slate-100 px-3 py-1 font-medium"
              >
                Unverified Package Transcription
              </Badge>
            )}
          </div>
        </div>

        {/* Quick Meta Row */}
        <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 border-t border-slate-100 pt-3">
          {product.serving_size && (
            <span className="flex items-center gap-1.5 font-medium">
              <Scale className="h-4 w-4 text-slate-400" />
              Declared Serving: <strong className="text-slate-800">{product.serving_size}</strong>
            </span>
          )}
          {product.barcode && (
            <span className="flex items-center gap-1.5 font-mono text-slate-500">
              <Barcode className="h-4 w-4 text-slate-400" />
              Barcode: {product.barcode}
            </span>
          )}
          <span className="flex items-center gap-1.5 text-slate-500">
            <Layers className="h-4 w-4 text-slate-400" />
            Data Source: <span className="capitalize font-medium text-slate-700">{product.data_source}</span>
          </span>
        </div>

        {/* Verification / Demo Warning Banner */}
        {product.is_demo_data && (
          <div className="p-3.5 bg-amber-50 rounded-xl border border-amber-200 flex items-start gap-2.5 text-xs text-amber-900">
            <Info className="h-4 w-4 text-amber-700 mt-0.5 flex-shrink-0" />
            <div>
              <strong className="font-semibold">Development Demonstration Data:</strong> {product.verification_note || "Values displayed are illustrative parameters designed for system calibration and interface development. Do not use for clinical dietary management."}
            </div>
          </div>
        )}
      </div>

      {/* Day 5 & 6 — Nutrition Score + Personal Suitability (side by side on large screens) */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Day 5 Deterministic Nutrition Score & Analysis Section */}
        <NutritionScoreAnalysisCard
          analysis={product.nutrition_analysis}
          servingSize={product.serving_size != null ? String(product.serving_size) : null}
        />

        {/* Day 6 Personalized Dietary Suitability Section */}
        <PersonalSuitabilityCard productId={product.id} />
      </div>

      {/* Day 7 — Personalized Alternative Recommendations Section */}
      <AlternativeRecommendationsCard
        productId={product.id}
        currentProductName={product.name}
      />

      {/* Main Two-Column Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (7 cols): Allergens & Ingredients */}
        <div className="lg:col-span-7 space-y-6">
          {/* Allergen Alerts Card */}
          <AllergenAlertCard allergens={product.product_allergens} />

          {/* Structured Ingredient Knowledge Base Card */}
          <IngredientListCard
            ingredients={product.product_ingredients}
            rawText={product.raw_ingredients_text}
          />
        </div>

        {/* Right Column (5 cols): Nutritional Facts & Metadata */}
        <div className="lg:col-span-5 space-y-6">
          {/* Nutrition Facts Table Card */}
          <NutritionalFactsCard
            nutrition={product.nutrition_facts}
            servingSize={product.serving_size != null ? String(product.serving_size) : null}
          />

          {/* Record Metadata Card */}
          <Card className="border-slate-200 shadow-sm text-xs text-slate-600">
            <CardHeader className="pb-2 pt-4 px-5">
              <CardTitle className="text-sm font-semibold">Record Metadata</CardTitle>
            </CardHeader>
            <CardContent className="px-5 pb-4 space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">NutriLens Product ID:</span>
                <span className="font-mono text-slate-700 truncate max-w-[200px]">
                  {product.id}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Total Ingredients Mapped:</span>
                <span className="font-semibold text-slate-800">
                  {product.product_ingredients.length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Allergen Declarations:</span>
                <span className="font-semibold text-slate-800">
                  {product.product_allergens.length}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Report Issue Modal */}
      {reportModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full overflow-hidden">
            <div className="px-6 py-4 border-b flex items-center justify-between bg-slate-50">
              <div className="flex items-center space-x-2">
                <Flag className="h-4 w-4 text-amber-600" />
                <h3 className="text-sm font-bold text-slate-900">Report Inaccurate Food Data</h3>
              </div>
              <button
                type="button"
                onClick={() => setReportModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 font-bold text-xs"
              >
                ✕
              </button>
            </div>

            {reportSuccess ? (
              <div className="p-6 text-center space-y-3">
                <div className="h-10 w-10 rounded-full bg-emerald-100 text-emerald-700 mx-auto flex items-center justify-center">
                  <ShieldCheck className="h-6 w-6" />
                </div>
                <h4 className="font-bold text-slate-900 text-sm">Report Submitted for Verification</h4>
                <p className="text-xs text-slate-500">
                  Thank you for helping keep the NutriLens knowledge base accurate. An administrator will review your report shortly.
                </p>
              </div>
            ) : (
              <form onSubmit={handleReportSubmit} className="p-6 space-y-4 text-xs">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Issue Category</label>
                  <select
                    value={reportType}
                    onChange={(e) => setReportType(e.target.value)}
                    className="h-9 w-full px-3 rounded-md border border-input bg-background text-xs"
                  >
                    <option value="incorrect_ingredients">Ingredient list mismatch</option>
                    <option value="inaccurate_nutrition">Inaccurate nutrition facts / calories</option>
                    <option value="mislabeled_allergens">Missing or incorrect allergen declaration</option>
                    <option value="incorrect_barcode">Incorrect product barcode / GTIN</option>
                    <option value="ocr_error">OCR transcription artifact / typo</option>
                    <option value="other">Other factual discrepancy</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Describe the Discrepancy *
                  </label>
                  <textarea
                    required
                    rows={4}
                    value={reportDesc}
                    onChange={(e) => setReportDesc(e.target.value)}
                    placeholder="e.g. The physical package lists 18g total sugar per 100g, but the table shows 8g. Also contains soy lecithin..."
                    className="w-full p-2.5 border rounded-md text-xs focus:ring-1 focus:ring-amber-500"
                  />
                </div>

                <div className="pt-2 flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setReportModalOpen(false)}
                    className="text-xs"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    size="sm"
                    disabled={reportSubmitting}
                    className="bg-amber-600 hover:bg-amber-700 text-white text-xs"
                  >
                    {reportSubmitting ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                    ) : null}
                    Submit Report
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
