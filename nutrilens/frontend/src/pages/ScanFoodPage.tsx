import React, { useState, useRef, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  Camera,
  Upload,
  X,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Plus,
  Sparkles,
  ShieldAlert,
  Check,
  ArrowLeft,
  Edit3,
  Save,
  Info,
  AlertCircle,
  ThumbsUp,
  ThumbsDown,
  Activity,
  Sliders,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import axios from "axios";
import { api, API_BASE_URL } from "@/services/api";
import type {
  ScanSession,
  ExtractedNutritionFacts,
  ScanCorrectionPayload,
  ScanConfirmPayload,
  ScanAnalysisResult,
} from "@/types";

interface QueuedImage {
  id: string;
  file: File;
  previewUrl: string;
}

const PROCESSING_STEPS = [
  { id: 1, label: "Connecting to server..." },
  { id: 2, label: "Uploading image..." },
  { id: 3, label: "Reading food label (OCR)..." },
  { id: 4, label: "Extracting ingredients & nutrition..." },
  { id: 5, label: "Analyzing & scoring..." },
  { id: 6, label: "Preparing your report..." },
];

export const ScanFoodPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  // Mode: "scan" | "processing" | "results"
  const [viewMode, setViewMode] = useState<"scan" | "processing" | "results">("scan");

  // Camera & Image state
  const [queuedImage, setQueuedImage] = useState<QueuedImage | null>(null);
  const [cameraActive, setCameraActive] = useState<boolean>(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Scan execution & progress state
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [scanSession, setScanSession] = useState<ScanSession | null>(null);

  // Edit / Re-analyze state
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [isReanalyzing, setIsReanalyzing] = useState<boolean>(false);
  const [isSavingCatalogue, setIsSavingCatalogue] = useState<boolean>(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Editable fields for correction
  const [editProductName, setEditProductName] = useState<string>("");
  const [editBrand, setEditBrand] = useState<string>("");
  const [editCategory, setEditCategory] = useState<string>("Snacks & Namkeen");
  const [editServingSize, setEditServingSize] = useState<string>("100g");
  const [editIngredients, setEditIngredients] = useState<string[]>([]);
  const [newIngredientInput, setNewIngredientInput] = useState<string>("");
  const [editNutritionFacts, setEditNutritionFacts] = useState<ExtractedNutritionFacts>({});

  // If URL has ?id=<scan_id>, load that scan directly for report viewing
  useEffect(() => {
    const scanId = searchParams.get("id");
    if (scanId && !scanSession) {
      api.getScanSession(scanId)
        .then((session) => {
          setScanSession(session);
          initializeEditForm(session);
          setViewMode("results");
        })
        .catch((err) => {
          console.error("Failed to load scan from ID:", err);
        });
    }
  }, [searchParams]);

  // ---------------------------------------------------------------------------
  // Camera Handling
  // ---------------------------------------------------------------------------
  const startCamera = async () => {
    setCameraError(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Browser camera access is not supported on this device or browser.");
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      mediaStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
    } catch (err: any) {
      setCameraError(
        err.message || "Failed to access device camera. Please check camera permissions."
      );
      setCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const file = new File([blob], `scan_${Date.now()}.jpg`, {
          type: "image/jpeg",
        });
        const previewUrl = URL.createObjectURL(blob);
        const item: QueuedImage = {
          id: String(Date.now()),
          file,
          previewUrl,
        };
        setQueuedImage(item);
        stopCamera();
        // Automatically start the analysis pipeline
        executeAutomatedScan(item);
      },
      "image/jpeg",
      0.92
    );
  };

  // ---------------------------------------------------------------------------
  // File Upload Handling
  // ---------------------------------------------------------------------------
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const file = files[0];
    const previewUrl = URL.createObjectURL(file);
    const item: QueuedImage = {
      id: String(Date.now()),
      file,
      previewUrl,
    };
    setQueuedImage(item);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    // Automatically start the analysis pipeline
    executeAutomatedScan(item);
  };

  const clearSelectedImage = () => {
    if (queuedImage) {
      URL.revokeObjectURL(queuedImage.previewUrl);
      setQueuedImage(null);
    }
    setScanError(null);
  };

  // ---------------------------------------------------------------------------
  // Automated Scan Execution & Multi-Stage Progression
  // ---------------------------------------------------------------------------
  const executeAutomatedScan = async (imageToScan?: QueuedImage) => {
    if (isScanning) return; // Prevent duplicate concurrent submissions
    const targetImage = imageToScan || queuedImage;
    if (!targetImage) {
      setScanError("Please select or capture a food label image.");
      return;
    }

    setScanError(null);
    setIsScanning(true);
    setViewMode("processing");
    setCurrentStepIndex(0);

    // Step progression: advance one step every 4s so the UI doesn't race ahead
    // of the actual backend work (OCR + LLM can take 30–90 seconds total).
    let step = 0;
    const interval = setInterval(() => {
      step += 1;
      // Stay on the second-to-last step until the response arrives
      if (step < PROCESSING_STEPS.length - 1) {
        setCurrentStepIndex(step);
      }
    }, 4000);

    try {
      // 1. Ping the health endpoint first so Render's free-tier dyno fully wakes up
      //    before we send the heavyweight scan payload.
      //    Use a 70-second dedicated timeout so we actually wait through Render's
      //    cold-start window (~30-60s) rather than giving up at 15s.
      try {
        await axios.get(`${API_BASE_URL}/api/health`, { timeout: 70000 });
      } catch {
        // Backend may still be starting; proceed with scan anyway – the 180s
        // scan timeout gives it another chance to respond.
      }

      // 2. Perform the actual scan (120-second timeout set in api.ts)
      const session = await api.scanFoodImages([targetImage.file], ["other"]);
      clearInterval(interval);
      setCurrentStepIndex(PROCESSING_STEPS.length - 1);

      // Brief delay so user sees final "Preparing your report..."
      setTimeout(() => {
        setIsScanning(false);
        setScanSession(session);
        initializeEditForm(session);
        setViewMode("results");
        // Invalidate scan history and dashboard queries so new scan appears immediately
        queryClient.invalidateQueries({ queryKey: ["scan-history"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }, 500);
    } catch (err: any) {
      setIsScanning(false);
      clearInterval(interval);
      setViewMode("scan");
      let msg: string =
        err.response?.data?.detail || err.message || "Failed to process food label image.";
      // Provide a friendlier message for timeout errors
      if (msg.toLowerCase().includes("timeout") || msg.toLowerCase().includes("network")) {
        msg =
          "Analysis is taking longer than expected (the server may be starting up — this can take up to 60 seconds on first use). " +
          "Click \"Try Again\" below to retry.";
      }
      setScanError(msg);
    }
  };

  const initializeEditForm = (session: ScanSession) => {
    const analysis: ScanAnalysisResult | undefined = session.analysis || undefined;
    const extracted = session.corrected_data || session.extracted_data || {};

    setEditProductName(analysis?.product_name || extracted.product_name || "Unknown Product");
    setEditBrand(analysis?.brand || extracted.brand || "");
    setEditCategory(analysis?.category || extracted.category || "Snacks & Namkeen");
    setEditServingSize(analysis?.serving_size || extracted.serving_size || "100g");
    setEditIngredients(extracted.ingredients || []);
    setEditNutritionFacts(extracted.nutrition_facts || {});
  };

  // ---------------------------------------------------------------------------
  // Re-Analysis on User Correction
  // ---------------------------------------------------------------------------
  const handleReanalyze = async () => {
    if (!scanSession) return;
    setIsReanalyzing(true);
    setScanError(null);
    setSaveSuccessMsg(null);

    const payload: ScanCorrectionPayload = {
      product_name: editProductName.trim() || "Unknown Product",
      brand: editBrand.trim() || undefined,
      category: editCategory,
      serving_size: editServingSize.trim() || "100g",
      ingredients: editIngredients,
      nutrition_facts: editNutritionFacts,
    };

    try {
      const updated = await api.updateScanCorrection(scanSession.id, payload);
      setScanSession(updated);
      setIsEditing(false);
      setSaveSuccessMsg("Analysis re-calculated with your updated label values.");
      setTimeout(() => setSaveSuccessMsg(null), 4000);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || "Failed to re-calculate analysis.";
      setScanError(msg);
    } finally {
      setIsReanalyzing(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Save to Catalogue (Optional Action)
  // ---------------------------------------------------------------------------
  const handleSaveToCatalogue = async () => {
    if (!scanSession) return;
    setIsSavingCatalogue(true);
    setScanError(null);

    const confirmPayload: ScanConfirmPayload = {
      product_name: editProductName.trim() || "Unknown Product",
      brand: editBrand.trim() || undefined,
      category: editCategory,
      serving_size: editServingSize.trim() || "100g",
      ingredients: editIngredients,
      nutrition_facts: editNutritionFacts,
      declared_allergens: scanSession.extracted_data?.declared_allergens || [],
      precautionary_allergens: scanSession.extracted_data?.precautionary_allergens || [],
    };

    try {
      const res = await api.confirmScan(scanSession.id, confirmPayload);
      setSaveSuccessMsg("Product successfully added to the NutriLens catalogue!");
      setTimeout(() => {
        navigate(`/catalogue/${res.product_id}`);
      }, 1200);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || "Failed to save product to catalogue.";
      setScanError(msg);
      setIsSavingCatalogue(false);
    }
  };

  const handleNutrientChange = (field: keyof ExtractedNutritionFacts, valStr: string) => {
    const val = valStr === "" ? undefined : parseFloat(valStr);
    setEditNutritionFacts((prev) => ({
      ...prev,
      [field]: isNaN(val as number) ? undefined : val,
    }));
  };

  const addIngredientTag = () => {
    if (!newIngredientInput.trim()) return;
    setEditIngredients((prev) => [...prev, newIngredientInput.trim()]);
    setNewIngredientInput("");
  };

  const removeIngredientTag = (index: number) => {
    setEditIngredients((prev) => prev.filter((_, i) => i !== index));
  };

  const analysis = scanSession?.analysis;

  // Grade color helper
  const getGradeBadge = (grade?: string | null) => {
    if (!grade) return <Badge variant="outline" className="text-slate-500">Unavailable</Badge>;
    const map: Record<string, string> = {
      A: "bg-emerald-600 hover:bg-emerald-700 text-white",
      B: "bg-teal-600 hover:bg-teal-700 text-white",
      C: "bg-amber-500 hover:bg-amber-600 text-white",
      D: "bg-orange-500 hover:bg-orange-600 text-white",
      E: "bg-rose-600 hover:bg-rose-700 text-white",
    };
    return (
      <span className={`inline-flex items-center justify-center font-bold px-3 py-1 rounded-md text-base ${map[grade] || "bg-slate-700 text-white"}`}>
        Grade {grade}
      </span>
    );
  };

  const getSuitabilityBadge = (status?: string | null, color?: string | null) => {
    if (!status) return <Badge variant="outline">Not evaluated</Badge>;
    const c = color || "slate";
    const colorMap: Record<string, string> = {
      emerald: "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-200",
      green: "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-200",
      amber: "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950 dark:text-amber-200",
      rose: "bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-950 dark:text-rose-200",
      slate: "bg-slate-100 text-slate-800 border-slate-300 dark:bg-slate-900 dark:text-slate-200",
    };
    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${colorMap[c] || colorMap.slate}`}>
        <Activity className="h-3.5 w-3.5" />
        {status}
      </span>
    );
  };

  // ---------------------------------------------------------------------------
  // VIEW: Processing Animation
  // ---------------------------------------------------------------------------
  if (viewMode === "processing") {
    return (
      <div className="max-w-2xl mx-auto py-12 px-4 sm:px-6">
        <Card className="border-emerald-200 dark:border-emerald-900/50 shadow-lg text-center p-8">
          <div className="relative mx-auto w-24 h-24 mb-6">
            <div className="absolute inset-0 rounded-full border-4 border-emerald-100 dark:border-emerald-950 animate-ping opacity-30" />
            <div className="w-24 h-24 rounded-full border-4 border-emerald-500 border-t-transparent animate-spin flex items-center justify-center bg-emerald-50 dark:bg-emerald-950/40">
              <Sparkles className="h-10 w-10 text-emerald-600 dark:text-emerald-400" />
            </div>
          </div>

          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 mb-2">
            Analyzing Food Label
          </h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mb-8">
            Extracting nutritional facts, ingredients, and personal suitability...
          </p>

          <div className="space-y-3 max-w-md mx-auto text-left">
            {PROCESSING_STEPS.map((step, idx) => {
              const isPast = idx < currentStepIndex;
              const isCurrent = idx === currentStepIndex;

              return (
                <div
                  key={step.id}
                  className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                    isCurrent
                      ? "bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800"
                      : isPast
                      ? "bg-slate-50 dark:bg-slate-900/40 text-slate-600 dark:text-slate-400"
                      : "opacity-40 text-slate-400 dark:text-slate-600"
                  }`}
                >
                  {isPast ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                  ) : isCurrent ? (
                    <RefreshCw className="h-5 w-5 text-emerald-600 dark:text-emerald-400 animate-spin flex-shrink-0" />
                  ) : (
                    <div className="h-5 w-5 rounded-full border-2 border-slate-300 dark:border-slate-700 flex-shrink-0" />
                  )}
                  <span className={`text-sm font-medium ${isCurrent ? "text-emerald-900 dark:text-emerald-200" : ""}`}>
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="mt-8 text-xs text-slate-400 dark:text-slate-500 space-y-1">
            <p>Automated OCR &amp; Intelligence Engine • No barcode or manual identification required</p>
            <p className="text-amber-500 dark:text-amber-400 font-medium">
              ⏱ First scan may take up to 90 seconds while the server wakes up. Please wait.
            </p>
          </div>
        </Card>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // VIEW: Results Page (Section A through F)
  // ---------------------------------------------------------------------------
  if (viewMode === "results" && analysis) {
    const nutrition = analysis.nutrition_analysis;
    const ingredients = analysis.ingredient_intelligence;
    const suitability = analysis.suitability_analysis;
    const quality = analysis.data_quality;

    return (
      <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 space-y-6">
        {/* Navigation & Actions Top Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200 dark:border-slate-800">
          <div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                clearSelectedImage();
                setViewMode("scan");
              }}
              className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 -ml-2 mb-1"
            >
              <ArrowLeft className="h-4 w-4 mr-1.5" />
              Scan Another Food
            </Button>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Food Label Analysis Report
              <Badge variant="outline" className="text-xs font-normal">Automated</Badge>
            </h1>
          </div>

          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditing(!isEditing)}
              className="gap-1.5"
            >
              <Edit3 className="h-4 w-4" />
              {isEditing ? "Close Editor" : "Edit Extracted Values"}
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleSaveToCatalogue}
              disabled={isSavingCatalogue}
              className="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              {isSavingCatalogue ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Save to Catalogue
            </Button>
          </div>
        </div>

        {saveSuccessMsg && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 dark:bg-emerald-950/60 dark:border-emerald-800 rounded-lg flex items-center gap-2.5 text-emerald-800 dark:text-emerald-200 text-sm">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0" />
            <span>{saveSuccessMsg}</span>
          </div>
        )}

        {scanError && (
          <div className="p-4 bg-rose-50 border border-rose-200 dark:bg-rose-950/60 dark:border-rose-800 rounded-lg flex items-center gap-2.5 text-rose-800 dark:text-rose-200 text-sm">
            <AlertTriangle className="h-5 w-5 text-rose-600 flex-shrink-0" />
            <span>{scanError}</span>
          </div>
        )}

        {/* SECTION A: Product Overview */}
        <Card className="border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 p-6">
            <div className="flex-1 space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs uppercase font-semibold tracking-wider text-emerald-600 dark:text-emerald-400">
                  {analysis.brand || "Unspecified Brand"}
                </span>
                <span className="text-slate-300 dark:text-slate-700">•</span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {analysis.category || "General Food Item"}
                </span>
                <span className="text-slate-300 dark:text-slate-700">•</span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Serving: {analysis.serving_size || "100g"}
                </span>
              </div>

              <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-slate-100">
                {analysis.product_name || "Unknown Product"}
              </h2>

              <p className="text-xs text-slate-400 dark:text-slate-500">
                Scanned on {new Date(analysis.scan_timestamp).toLocaleString()} • Automatic OCR Analysis
              </p>
            </div>

            {queuedImage && (
              <div className="flex-shrink-0 relative group">
                <img
                  src={queuedImage.previewUrl}
                  alt="Scanned Food Label"
                  className="w-24 h-24 object-cover rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm"
                />
              </div>
            )}
          </div>
        </Card>

        {/* Interactive Inline Correction Panel */}
        {isEditing && (
          <Card className="border-emerald-300 dark:border-emerald-800 bg-emerald-50/40 dark:bg-emerald-950/20 shadow-sm p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-emerald-200 dark:border-emerald-900 pb-3">
              <div>
                <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-base flex items-center gap-2">
                  <Sliders className="h-4 w-4 text-emerald-600" />
                  Correct Extracted Information
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Edit misread OCR numbers or text. Re-calculating updates the NutriLens score and suitability in real time.
                </p>
              </div>
              <Button
                size="sm"
                variant="default"
                onClick={handleReanalyze}
                disabled={isReanalyzing}
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                {isReanalyzing ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <RefreshCw className="h-4 w-4 mr-1" />}
                Re-calculate Analysis
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit-name" className="text-xs">Product Name</Label>
                <Input
                  id="edit-name"
                  value={editProductName}
                  onChange={(e) => setEditProductName(e.target.value)}
                  placeholder="e.g. Britannia Digestive Cookies"
                  className="h-9 mt-1 text-sm bg-white dark:bg-slate-900"
                />
              </div>
              <div>
                <Label htmlFor="edit-brand" className="text-xs">Brand</Label>
                <Input
                  id="edit-brand"
                  value={editBrand}
                  onChange={(e) => setEditBrand(e.target.value)}
                  placeholder="e.g. Britannia"
                  className="h-9 mt-1 text-sm bg-white dark:bg-slate-900"
                />
              </div>
              <div>
                <Label htmlFor="edit-serving" className="text-xs">Serving Size</Label>
                <Input
                  id="edit-serving"
                  value={editServingSize}
                  onChange={(e) => setEditServingSize(e.target.value)}
                  placeholder="e.g. 30g or 100ml"
                  className="h-9 mt-1 text-sm bg-white dark:bg-slate-900"
                />
              </div>
              <div>
                <Label htmlFor="edit-cat" className="text-xs">Category</Label>
                <Input
                  id="edit-cat"
                  value={editCategory}
                  onChange={(e) => setEditCategory(e.target.value)}
                  placeholder="e.g. Biscuits & Cookies"
                  className="h-9 mt-1 text-sm bg-white dark:bg-slate-900"
                />
              </div>
            </div>

            <div>
              <Label className="text-xs font-semibold mb-2 block">
                Nutritional Values (Per 100g / 100ml)
              </Label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div>
                  <span className="text-xs text-slate-500 block mb-1">Energy (kcal)</span>
                  <Input
                    type="number"
                    step="0.1"
                    value={editNutritionFacts.energy_kcal ?? ""}
                    onChange={(e) => handleNutrientChange("energy_kcal", e.target.value)}
                    placeholder="—"
                    className="h-8 text-xs bg-white dark:bg-slate-900"
                  />
                </div>
                <div>
                  <span className="text-xs text-slate-500 block mb-1">Total Fat (g)</span>
                  <Input
                    type="number"
                    step="0.1"
                    value={editNutritionFacts.total_fat_g ?? ""}
                    onChange={(e) => handleNutrientChange("total_fat_g", e.target.value)}
                    placeholder="—"
                    className="h-8 text-xs bg-white dark:bg-slate-900"
                  />
                </div>
                <div>
                  <span className="text-xs text-slate-500 block mb-1">Saturated Fat (g)</span>
                  <Input
                    type="number"
                    step="0.1"
                    value={editNutritionFacts.saturated_fat_g ?? ""}
                    onChange={(e) => handleNutrientChange("saturated_fat_g", e.target.value)}
                    placeholder="—"
                    className="h-8 text-xs bg-white dark:bg-slate-900"
                  />
                </div>
                <div>
                  <span className="text-xs text-slate-500 block mb-1">Total Sugar (g)</span>
                  <Input
                    type="number"
                    step="0.1"
                    value={editNutritionFacts.total_sugar_g ?? ""}
                    onChange={(e) => handleNutrientChange("total_sugar_g", e.target.value)}
                    placeholder="—"
                    className="h-8 text-xs bg-white dark:bg-slate-900"
                  />
                </div>
                <div>
                  <span className="text-xs text-slate-500 block mb-1">Added Sugar (g)</span>
                  <Input
                    type="number"
                    step="0.1"
                    value={editNutritionFacts.added_sugar_g ?? ""}
                    onChange={(e) => handleNutrientChange("added_sugar_g", e.target.value)}
                    placeholder="—"
                    className="h-8 text-xs bg-white dark:bg-slate-900"
                  />
                </div>
                <div>
                  <span className="text-xs text-slate-500 block mb-1">Protein (g)</span>
                  <Input
                    type="number"
                    step="0.1"
                    value={editNutritionFacts.protein_g ?? ""}
                    onChange={(e) => handleNutrientChange("protein_g", e.target.value)}
                    placeholder="—"
                    className="h-8 text-xs bg-white dark:bg-slate-900"
                  />
                </div>
                <div>
                  <span className="text-xs text-slate-500 block mb-1">Dietary Fibre (g)</span>
                  <Input
                    type="number"
                    step="0.1"
                    value={editNutritionFacts.dietary_fibre_g ?? ""}
                    onChange={(e) => handleNutrientChange("dietary_fibre_g", e.target.value)}
                    placeholder="—"
                    className="h-8 text-xs bg-white dark:bg-slate-900"
                  />
                </div>
                <div>
                  <span className="text-xs text-slate-500 block mb-1">Sodium (mg)</span>
                  <Input
                    type="number"
                    step="0.1"
                    value={editNutritionFacts.sodium_mg ?? ""}
                    onChange={(e) => handleNutrientChange("sodium_mg", e.target.value)}
                    placeholder="—"
                    className="h-8 text-xs bg-white dark:bg-slate-900"
                  />
                </div>
              </div>
            </div>

            <div>
              <Label className="text-xs font-semibold mb-2 block">Ingredients List</Label>
              <div className="flex flex-wrap gap-1.5 mb-2.5">
                {editIngredients.map((ing, idx) => (
                  <Badge key={idx} variant="secondary" className="gap-1 pr-1 text-xs">
                    {ing}
                    <button
                      type="button"
                      onClick={() => removeIngredientTag(idx)}
                      className="hover:text-rose-600 ml-1"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  value={newIngredientInput}
                  onChange={(e) => setNewIngredientInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addIngredientTag())}
                  placeholder="Add missing ingredient..."
                  className="h-8 text-xs max-w-sm bg-white dark:bg-slate-900"
                />
                <Button size="sm" variant="outline" onClick={addIngredientTag} className="h-8 text-xs">
                  <Plus className="h-3.5 w-3.5 mr-1" /> Add
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* SECTION B: NutriLens Score */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-sm">
          <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
            <CardTitle className="text-lg font-bold flex items-center justify-between">
              <span>Section B: NutriLens Nutritional Score</span>
              {nutrition.is_available && getGradeBadge(nutrition.grade)}
            </CardTitle>
            <CardDescription className="text-xs">
              Deterministic, evidence-based nutrition evaluation scaled 0 to 100.
            </CardDescription>
          </CardHeader>

          <CardContent className="pt-6">
            {!nutrition.is_available ? (
              <div className="p-6 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-center space-y-3">
                <AlertCircle className="h-10 w-10 text-slate-400 mx-auto" />
                <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-base">
                  Nutritional Scoring Unavailable
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 max-w-lg mx-auto">
                  {nutrition.message || "No complete nutrition facts table was detected on the label."}
                </p>
                <p className="text-xs text-slate-400 dark:text-slate-500 max-w-md mx-auto italic">
                  NutriLens never invents numbers or treats missing values as zero. When critical nutrients are missing, score calculation is honest and withheld.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-6 p-4 rounded-xl bg-slate-50 dark:bg-slate-900/50">
                  <div className="flex items-center gap-4">
                    <div className="w-20 h-20 rounded-full border-4 border-emerald-500 flex flex-col items-center justify-center bg-white dark:bg-slate-950 shadow-sm">
                      <span className="text-2xl font-black text-slate-900 dark:text-slate-100 leading-none">
                        {nutrition.score}
                      </span>
                      <span className="text-[10px] text-slate-400 font-medium uppercase mt-0.5">/ 100</span>
                    </div>

                    <div>
                      <div className="text-base font-bold text-slate-900 dark:text-slate-100">
                        {nutrition.rating_label} Rating
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mt-0.5">
                        {nutrition.nutrition_summary || "Nutritional evaluation completed according to standardized nutrient thresholds."}
                      </p>
                    </div>
                  </div>

                  <div className="text-xs text-slate-500 space-y-1 sm:text-right border-t sm:border-t-0 pt-2 sm:pt-0">
                    <div>Reference: <span className="font-semibold text-slate-700 dark:text-slate-300">100{nutrition.standard_unit?.includes("ml") ? "ml" : "g"}</span></div>
                    <div>Data completeness: <span className="font-semibold text-emerald-600">{nutrition.data_completeness_pct ?? 100}%</span></div>
                  </div>
                </div>

                {/* Positive & Attention Factors */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-900/40">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-300 flex items-center gap-1.5 mb-2.5">
                      <ThumbsUp className="h-3.5 w-3.5" />
                      Positive Nutritional Factors
                    </h4>
                    {nutrition.positive_factors && nutrition.positive_factors.length > 0 ? (
                      <ul className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                        {nutrition.positive_factors.map((factor, i) => {
                          const text = typeof factor === "string" ? factor : (factor.factor || factor.description);
                          return (
                            <li key={i} className="flex items-start gap-1.5">
                              <span className="text-emerald-500 font-bold">•</span>
                              <span>{text}</span>
                            </li>
                          );
                        })}
                      </ul>
                    ) : (
                      <p className="text-xs text-slate-400 italic">No significant positive nutritional bonuses observed.</p>
                    )}
                  </div>

                  <div className="p-4 rounded-lg bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-amber-800 dark:text-amber-300 flex items-center gap-1.5 mb-2.5">
                      <ThumbsDown className="h-3.5 w-3.5" />
                      Attention / High Nutrient Factors
                    </h4>
                    {nutrition.attention_factors && nutrition.attention_factors.length > 0 ? (
                      <ul className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                        {nutrition.attention_factors.map((factor, i) => {
                          const text = typeof factor === "string" ? factor : (factor.factor || factor.description);
                          return (
                            <li key={i} className="flex items-start gap-1.5">
                              <span className="text-amber-500 font-bold">•</span>
                              <span>{text}</span>
                            </li>
                          );
                        })}
                      </ul>
                    ) : (
                      <p className="text-xs text-slate-400 italic">No adverse nutrient penalties observed.</p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* SECTION C: Nutrition Breakdown Table */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-sm">
          <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
            <CardTitle className="text-lg font-bold flex items-center justify-between">
              <span>Section C: Nutrition Facts Breakdown</span>
              <span className="text-xs font-normal text-slate-400">
                Normalized per 100{nutrition.standard_unit?.includes("ml") ? "ml" : "g"} and per serving ({analysis.serving_size || "100g"})
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-400 uppercase">
                    <th className="py-2.5 px-3">Nutrient</th>
                    <th className="py-2.5 px-3 text-right">Per 100g / 100ml</th>
                    <th className="py-2.5 px-3 text-right">Per Serving</th>
                    <th className="py-2.5 px-3 text-right">Nutritional Note</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-xs">
                  {[
                    { label: "Energy", key: "energy_kcal", unit: "kcal" },
                    { label: "Total Fat", key: "total_fat_g", unit: "g" },
                    { label: "Saturated Fat", key: "saturated_fat_g", unit: "g" },
                    { label: "Total Sugars", key: "total_sugar_g", unit: "g" },
                    { label: "Added Sugars", key: "added_sugar_g", unit: "g" },
                    { label: "Carbohydrates", key: "carbohydrates_g", unit: "g" },
                    { label: "Dietary Fibre", key: "dietary_fibre_g", unit: "g" },
                    { label: "Protein", key: "protein_g", unit: "g" },
                    { label: "Sodium", key: "sodium_mg", unit: "mg" },
                  ].map((nutrient) => {
                    const val100 = nutrition.per_100_values?.[nutrient.key];
                    const valServ = nutrition.per_serving_values?.[nutrient.key];
                    const evalObj: any = Array.isArray(nutrition.nutrient_evaluations)
                      ? (nutrition.nutrient_evaluations as any[]).find((e: any) => e.nutrient_key === nutrient.key)
                      : (nutrition.nutrient_evaluations as any)?.[nutrient.key];

                    return (
                      <tr key={nutrient.key} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30">
                        <td className="py-2 px-3 font-medium text-slate-800 dark:text-slate-200">
                          {nutrient.label}
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-slate-700 dark:text-slate-300">
                          {val100 !== null && val100 !== undefined ? `${val100} ${nutrient.unit}` : <span className="text-slate-400 italic">—</span>}
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-slate-700 dark:text-slate-300">
                          {valServ !== null && valServ !== undefined ? `${valServ} ${nutrient.unit}` : <span className="text-slate-400 italic">—</span>}
                        </td>
                        <td className="py-2 px-3 text-right text-slate-500">
                          {evalObj ? (
                            <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                              evalObj.level === "high" ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200" :
                              evalObj.level === "moderate" ? "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200" :
                              "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
                            }`}>
                              {evalObj.level_label || evalObj.level}
                            </span>
                          ) : (
                            <span className="text-slate-400 text-[11px]">Not evaluated</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="text-[11px] text-slate-400 mt-3 italic">
              Values marked with “—” are undeclared on the packaging label and are not assumed to be zero.
            </p>
          </CardContent>
        </Card>

        {/* SECTION D: Ingredient Intelligence */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-sm">
          <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
            <CardTitle className="text-lg font-bold flex items-center justify-between">
              <span>Section D: Ingredient Intelligence & Safety</span>
              {ingredients.is_available && (
                <span className="text-xs font-normal text-slate-500">
                  {ingredients.recognized_count} recognized • {ingredients.unrecognized_count} uncategorized
                </span>
              )}
            </CardTitle>
            <CardDescription className="text-xs">
              Additives, preservatives, sweeteners, and ingredient purpose identification.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            {!ingredients.is_available ? (
              <div className="p-6 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-center space-y-2">
                <AlertCircle className="h-8 w-8 text-slate-400 mx-auto" />
                <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
                  Ingredient Analysis Unavailable
                </h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  {ingredients.message || "No ingredients list could be extracted from this label image."}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Ingredient Concerns Callout */}
                {ingredients.concerns && ingredients.concerns.length > 0 && (
                  <div className="p-3.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60">
                    <h5 className="text-xs font-bold text-amber-900 dark:text-amber-200 flex items-center gap-1.5 mb-2">
                      <ShieldAlert className="h-4 w-4 text-amber-600" />
                      Ingredients to Note ({ingredients.concerns.length})
                    </h5>
                    <ul className="space-y-1 text-xs text-amber-800 dark:text-amber-300">
                      {ingredients.concerns.map((con, idx) => (
                        <li key={idx}>
                          <span className="font-semibold">{con.ingredient}:</span> {con.note}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Recognized Ingredients Table */}
                <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 uppercase font-semibold">
                      <tr>
                        <th className="py-2 px-3">Ingredient</th>
                        <th className="py-2 px-3">Category</th>
                        <th className="py-2 px-3">Functional Purpose</th>
                        <th className="py-2 px-3 text-right">Safety Level</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {ingredients.recognized.map((item, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30">
                          <td className="py-2.5 px-3">
                            <span className="font-semibold text-slate-800 dark:text-slate-200 block">
                              {item.name}
                            </span>
                            {item.ins_number && (
                              <span className="text-[10px] text-slate-400 font-mono">INS {item.ins_number}</span>
                            )}
                          </td>
                          <td className="py-2.5 px-3 text-slate-600 dark:text-slate-400">
                            {item.category}
                          </td>
                          <td className="py-2.5 px-3 text-slate-600 dark:text-slate-400">
                            {item.purpose}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                              item.concern_level === "high" ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-200" :
                              item.concern_level === "moderate" ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200" :
                              "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
                            }`}>
                              {item.concern_level}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Unrecognized Ingredients Section */}
                {ingredients.unrecognized && ingredients.unrecognized.length > 0 && (
                  <div className="p-3 bg-slate-50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800 rounded-lg">
                    <h5 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
                      <Info className="h-3.5 w-3.5 text-slate-400" />
                      Unrecognized or Complex Ingredients ({ingredients.unrecognized.length})
                    </h5>
                    <div className="flex flex-wrap gap-1.5">
                      {ingredients.unrecognized.map((unrec, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs text-slate-600 dark:text-slate-400">
                          {unrec.original_text || unrec.name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* SECTION E: Personalized Suitability */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-sm">
          <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
            <CardTitle className="text-lg font-bold flex items-center justify-between">
              <span>Section E: Personalized Dietary Suitability</span>
              {getSuitabilityBadge(suitability.status_label, suitability.badge_color)}
            </CardTitle>
            <CardDescription className="text-xs">
              {suitability.is_personalized
                ? "Checked against your configured dietary preferences, allergies, and nutrition goals."
                : "General suitability assessment. Log in to personalize against your profile."}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            {suitability.guest_notice && (
              <div className="p-3 bg-blue-50 border border-blue-200 dark:bg-blue-950/40 dark:border-blue-900/60 rounded-lg flex items-center justify-between gap-3 text-xs text-blue-800 dark:text-blue-300">
                <div className="flex items-center gap-2">
                  <Info className="h-4 w-4 text-blue-600 flex-shrink-0" />
                  <span>{suitability.guest_notice}</span>
                </div>
                <Link to="/login" className="underline font-semibold whitespace-nowrap hover:text-blue-900">
                  Log in
                </Link>
              </div>
            )}

            <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800">
              <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-1">
                Summary Evaluation
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-300">
                {suitability.summary_narrative}
              </p>
            </div>

            {/* Conflicts */}
            {suitability.conflicts && suitability.conflicts.length > 0 && (
              <div className="space-y-2">
                <h5 className="text-xs font-bold uppercase tracking-wider text-rose-600 flex items-center gap-1.5">
                  <ShieldAlert className="h-3.5 w-3.5" />
                  Direct Conflicts Detected ({suitability.conflicts.length})
                </h5>
                <div className="space-y-1.5">
                  {suitability.conflicts.map((conf, idx) => (
                    <div key={idx} className="p-2.5 rounded bg-rose-50 border border-rose-200 dark:bg-rose-950/50 dark:border-rose-900 text-xs">
                      <span className="font-semibold text-rose-900 dark:text-rose-200">{conf.title}: </span>
                      <span className="text-rose-800 dark:text-rose-300">{conf.detail}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Cautions */}
            {suitability.cautions && suitability.cautions.length > 0 && (
              <div className="space-y-2">
                <h5 className="text-xs font-bold uppercase tracking-wider text-amber-600 flex items-center gap-1.5">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Precautionary Warnings & Cautions ({suitability.cautions.length})
                </h5>
                <div className="space-y-1.5">
                  {suitability.cautions.map((caut, idx) => (
                    <div key={idx} className="p-2.5 rounded bg-amber-50 border border-amber-200 dark:bg-amber-950/50 dark:border-amber-900 text-xs">
                      <span className="font-semibold text-amber-900 dark:text-amber-200">{caut.title}: </span>
                      <span className="text-amber-800 dark:text-amber-300">{caut.detail}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Positive Observations */}
            {suitability.positive_observations && suitability.positive_observations.length > 0 && (
              <div className="space-y-2">
                <h5 className="text-xs font-bold uppercase tracking-wider text-emerald-600 flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5" />
                  Aligned Preferences
                </h5>
                <div className="space-y-1.5">
                  {suitability.positive_observations.map((pos, idx) => (
                    <div key={idx} className="p-2.5 rounded bg-emerald-50 border border-emerald-200 dark:bg-emerald-950/50 dark:border-emerald-900 text-xs">
                      <span className="font-semibold text-emerald-900 dark:text-emerald-200">{pos.title}: </span>
                      <span className="text-emerald-800 dark:text-emerald-300">{pos.detail}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Safety Warnings & Disclaimer */}
            <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
              <p className="text-[11px] text-slate-400 dark:text-slate-500 italic">
                {suitability.disclaimer || "Always verify physical packaging declarations before consumption if you have severe food allergies or medical dietary requirements."}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* SECTION F: Data Quality & Uncertainty */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-sm bg-slate-50/50 dark:bg-slate-900/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Activity className="h-4 w-4 text-slate-500" />
              Section F: OCR Quality & Uncertainty Audit
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <span className="text-slate-500">OCR Engine: </span>
                <span className="font-mono font-semibold uppercase">{quality.ocr_engine}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-slate-500">Extraction Confidence: </span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {Math.round(quality.ocr_confidence * 100)}%
                </span>
              </div>
            </div>

            {quality.uncertainty_flags && quality.uncertainty_flags.length > 0 && (
              <div className="p-2.5 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded">
                <span className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Extraction Flags & Uncertainties:
                </span>
                <ul className="list-disc list-inside text-slate-500 space-y-0.5">
                  {quality.uncertainty_flags.map((flag, idx) => (
                    <li key={idx}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}

            <p className="text-[11px] text-slate-400 italic">
              {quality.disclaimer}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // VIEW: Scanning Interface (Take Photo / Upload Image)
  // ---------------------------------------------------------------------------
  return (
    <div className="max-w-4xl mx-auto py-10 px-4 sm:px-6">
      <div className="text-center max-w-xl mx-auto mb-8 space-y-2">
        <Badge variant="secondary" className="gap-1.5 py-1 px-3">
          <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
          Automated Food Scanner
        </Badge>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
          Scan Food Label
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Point your camera or upload a package photo. NutriLens automatically extracts ingredients, calculates scores, and checks your dietary preferences.
        </p>
      </div>

      {scanError && (
        <div className="mb-6 p-4 bg-rose-50 border border-rose-200 dark:bg-rose-950/60 dark:border-rose-800 rounded-lg text-rose-800 dark:text-rose-200 text-sm">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-rose-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p>{scanError}</p>
              {(scanError.toLowerCase().includes("timeout") || scanError.toLowerCase().includes("starting up")) && queuedImage && (
                <button
                  onClick={() => executeAutomatedScan(queuedImage)}
                  disabled={isScanning}
                  className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded bg-rose-100 hover:bg-rose-200 dark:bg-rose-900 dark:hover:bg-rose-800 transition-colors disabled:opacity-50"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Try Again
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {cameraError && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 dark:bg-amber-950/60 dark:border-amber-800 rounded-lg flex items-center gap-3 text-amber-800 dark:text-amber-200 text-sm">
          <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0" />
          <span>{cameraError}</span>
        </div>
      )}

      {/* Camera Live Preview View */}
      {cameraActive ? (
        <Card className="border-emerald-300 dark:border-emerald-900 overflow-hidden shadow-md max-w-xl mx-auto">
          <div className="relative aspect-[4/3] bg-black flex items-center justify-center">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="w-full h-full object-cover"
            />
            <canvas ref={canvasRef} className="hidden" />

            <div className="absolute inset-x-0 bottom-4 flex items-center justify-center gap-4">
              <Button
                variant="destructive"
                size="sm"
                onClick={stopCamera}
                className="gap-1.5 shadow"
              >
                <X className="h-4 w-4" /> Cancel
              </Button>
              <Button
                variant="default"
                size="lg"
                onClick={capturePhoto}
                className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-full px-6 shadow-lg"
              >
                <Camera className="h-5 w-5" /> Take Photo & Analyze
              </Button>
            </div>
          </div>
        </Card>
      ) : queuedImage ? (
        /* Image Preview Before / During Submission */
        <Card className="border-slate-200 dark:border-slate-800 shadow-md max-w-md mx-auto text-center p-6 space-y-4">
          <div className="relative aspect-square max-w-xs mx-auto overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800">
            <img
              src={queuedImage.previewUrl}
              alt="Food label preview"
              className="w-full h-full object-cover"
            />
            <button
              onClick={clearSelectedImage}
              className="absolute top-2 right-2 p-1.5 bg-black/60 text-white rounded-full hover:bg-black/80 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <p className="text-xs text-slate-500">
            Image ready for automatic analysis
          </p>

          <div className="flex gap-3 justify-center">
            <Button
              variant="outline"
              size="sm"
              onClick={clearSelectedImage}
            >
              Choose Different Image
            </Button>
            <Button
              variant="default"
              size="sm"
              disabled={isScanning}
              onClick={() => executeAutomatedScan()}
              className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1.5"
            >
              <Sparkles className="h-4 w-4" /> {isScanning ? "Analyzing..." : "Analyze Label"}
            </Button>
          </div>
        </Card>
      ) : (
        /* Default Action Buttons: Take Photo or Upload Image */
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 max-w-2xl mx-auto">
          {/* Card 1: Take Photo */}
          <Card
            onClick={startCamera}
            className="border-2 border-dashed border-slate-200 hover:border-emerald-500 dark:border-slate-800 dark:hover:border-emerald-600 p-8 text-center cursor-pointer transition-all hover:shadow-md group"
          >
            <div className="w-16 h-16 rounded-full bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
              <Camera className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-1">
              Take Photo
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
              Use your device camera to capture the nutrition facts or ingredients label.
            </p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="group-hover:bg-emerald-50 group-hover:text-emerald-700 group-hover:border-emerald-300"
            >
              Open Camera
            </Button>
          </Card>

          {/* Card 2: Upload Image */}
          <Card
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-200 hover:border-emerald-500 dark:border-slate-800 dark:hover:border-emerald-600 p-8 text-center cursor-pointer transition-all hover:shadow-md group"
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
            />
            <div className="w-16 h-16 rounded-full bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
              <Upload className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-1">
              Upload Image
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
              Select an existing JPEG, PNG, or WebP photo from your computer or phone.
            </p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="group-hover:bg-blue-50 group-hover:text-blue-700 group-hover:border-blue-300"
            >
              Browse Files
            </Button>
          </Card>
        </div>
      )}

      {/* Helpful Hint */}
      <div className="mt-12 text-center text-xs text-slate-400 dark:text-slate-500 max-w-md mx-auto space-y-1">
        <p>💡 <strong>Tip for best results:</strong> Ensure good lighting and capture the ingredients list or nutrition facts table clearly.</p>
        <p>NutriLens does not require barcodes or brand search. It directly parses whatever packaging text you provide.</p>
      </div>
    </div>
  );
};
