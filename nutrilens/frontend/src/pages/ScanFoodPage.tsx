import React, { useState, useRef, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Camera,
  Upload,
  X,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Plus,
  Trash2,
  Sparkles,
  ShieldAlert,
  Check,
  ImageIcon,
  Maximize2,
  ArrowLeft,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/services/api";
import type {
  ScanSession,
  ExtractedNutritionFacts,
  ScanCorrectionPayload,
  ScanConfirmPayload,
  ExtractedProductData,
} from "@/types";

interface QueuedImage {
  id: string;
  file: File;
  previewUrl: string;
  labelType: "front" | "ingredients" | "nutrition" | "allergens" | "other";
}

const CATEGORIES = [
  "Biscuits & Cookies",
  "Breakfast Cereals",
  "Dairy & Milks",
  "Snacks & Namkeen",
  "Chocolates & Sweets",
  "Beverages",
  "Instant Foods & Noodles",
  "Condiments & Sauces",
  "Staples & Grains",
];

export const ScanFoodPage: React.FC = () => {
  const navigate = useNavigate();

  // Upload & Camera State
  const [images, setImages] = useState<QueuedImage[]>([]);
  const [cameraActive, setCameraActive] = useState<boolean>(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [selectedCaptureType, setSelectedCaptureType] = useState<
    "front" | "ingredients" | "nutrition" | "allergens" | "other"
  >("ingredients");

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Scan execution & review state
  const [scanLoading, setScanLoading] = useState<boolean>(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [scanSession, setScanSession] = useState<ScanSession | null>(null);
  const [showRawOcr, setShowRawOcr] = useState<boolean>(false);

  // Form edit state for manual correction & confirmation
  const [productName, setProductName] = useState<string>("");
  const [brand, setBrand] = useState<string>("");
  const [category, setCategory] = useState<string>("Snacks & Namkeen");
  const [servingSize, setServingSize] = useState<string>("100g");
  const [barcode, setBarcode] = useState<string>("");
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [newIngredient, setNewIngredient] = useState<string>("");
  const [rawIngredientsText, setRawIngredientsText] = useState<string>("");
  const [nutritionFacts, setNutritionFacts] = useState<ExtractedNutritionFacts>({});
  const [declaredAllergens, setDeclaredAllergens] = useState<string[]>([]);
  const [newDeclaredAllergen, setNewDeclaredAllergen] = useState<string>("");
  const [precautionaryAllergens, setPrecautionaryAllergens] = useState<string[]>([]);
  const [newPrecautionaryAllergen, setNewPrecautionaryAllergen] = useState<string>("");

  const [savingCorrection, setSavingCorrection] = useState<boolean>(false);
  const [confirmingProduct, setConfirmingProduct] = useState<boolean>(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // Camera Capture Management
  // ---------------------------------------------------------------------------
  const startCamera = async () => {
    setCameraError(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Browser camera access is not supported by your browser or environment.");
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
        err.message || "Failed to access device camera. Please verify camera permissions."
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
        const file = new File([blob], `camera_scan_${Date.now()}.jpg`, {
          type: "image/jpeg",
        });
        const previewUrl = URL.createObjectURL(blob);
        const newImg: QueuedImage = {
          id: String(Date.now()),
          file,
          previewUrl,
          labelType: selectedCaptureType,
        };
        setImages((prev) => [...prev, newImg]);
        stopCamera();
      },
      "image/jpeg",
      0.92
    );
  };

  // ---------------------------------------------------------------------------
  // File Upload Handlers
  // ---------------------------------------------------------------------------
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newQueued: QueuedImage[] = Array.from(files).map((file, idx) => {
      const previewUrl = URL.createObjectURL(file);
      return {
        id: `${Date.now()}_${idx}`,
        file,
        previewUrl,
        labelType: selectedCaptureType,
      };
    });

    setImages((prev) => [...prev, ...newQueued]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const removeImage = (id: string) => {
    setImages((prev) => {
      const filtered = prev.filter((img) => img.id !== id);
      const target = prev.find((img) => img.id === id);
      if (target) {
        URL.revokeObjectURL(target.previewUrl);
      }
      return filtered;
    });
  };

  const clearAllImages = () => {
    images.forEach((img) => URL.revokeObjectURL(img.previewUrl));
    setImages([]);
    setScanError(null);
  };

  const updateImageLabelType = (id: string, labelType: QueuedImage["labelType"]) => {
    setImages((prev) =>
      prev.map((img) => (img.id === id ? { ...img, labelType } : img))
    );
  };

  // ---------------------------------------------------------------------------
  // Execute OCR Scan
  // ---------------------------------------------------------------------------
  const handleExecuteScan = async () => {
    if (images.length === 0) {
      setScanError("Please upload or capture at least one label image to scan.");
      return;
    }

    setScanLoading(true);
    setScanError(null);
    setSaveSuccessMsg(null);

    try {
      const fileList = images.map((img) => img.file);
      const typeList = images.map((img) => img.labelType);

      const session = await api.scanFoodImages(fileList, typeList);
      setScanSession(session);

      // Populate editable fields from extraction results
      const extracted: Partial<ExtractedProductData> = session.extracted_data || {};
      setProductName(extracted.product_name || "");
      setBrand(extracted.brand || "");
      setCategory(extracted.category || "Snacks & Namkeen");
      setServingSize(extracted.serving_size || "100g");
      setBarcode("");
      setRawIngredientsText(extracted.raw_ingredients_text || "");
      setIngredients(extracted.ingredients || []);
      setNutritionFacts(extracted.nutrition_facts || {});
      setDeclaredAllergens(extracted.declared_allergens || []);
      setPrecautionaryAllergens(extracted.precautionary_allergens || []);
    } catch (err: any) {
      const msg =
        err.response?.data?.detail || err.message || "Failed to process food label image.";
      setScanError(msg);
    } finally {
      setScanLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Ingredient & Allergen Tag Management
  // ---------------------------------------------------------------------------
  const addIngredientTag = () => {
    if (!newIngredient.trim()) return;
    setIngredients((prev) => [...prev, newIngredient.trim()]);
    setNewIngredient("");
  };

  const removeIngredientTag = (index: number) => {
    setIngredients((prev) => prev.filter((_, i) => i !== index));
  };

  const addDeclaredAllergenTag = () => {
    if (!newDeclaredAllergen.trim()) return;
    setDeclaredAllergens((prev) => [...prev, newDeclaredAllergen.trim()]);
    setNewDeclaredAllergen("");
  };

  const removeDeclaredAllergenTag = (index: number) => {
    setDeclaredAllergens((prev) => prev.filter((_, i) => i !== index));
  };

  const addPrecautionaryAllergenTag = () => {
    if (!newPrecautionaryAllergen.trim()) return;
    setPrecautionaryAllergens((prev) => [...prev, newPrecautionaryAllergen.trim()]);
    setNewPrecautionaryAllergen("");
  };

  const removePrecautionaryAllergenTag = (index: number) => {
    setPrecautionaryAllergens((prev) => prev.filter((_, i) => i !== index));
  };

  // ---------------------------------------------------------------------------
  // Save Manual Corrections
  // ---------------------------------------------------------------------------
  const handleSaveCorrections = async () => {
    if (!scanSession) return;
    setSavingCorrection(true);
    setSaveSuccessMsg(null);
    setScanError(null);

    const payload: ScanCorrectionPayload = {
      product_name: productName.trim() || undefined,
      brand: brand.trim() || undefined,
      category,
      serving_size: servingSize.trim() || undefined,
      raw_ingredients_text: rawIngredientsText || undefined,
      ingredients,
      nutrition_facts: nutritionFacts,
      declared_allergens: declaredAllergens,
      precautionary_allergens: precautionaryAllergens,
    };

    try {
      const updated = await api.updateScanCorrection(scanSession.id, payload);
      setScanSession(updated);
      setSaveSuccessMsg("Corrections saved successfully!");
      setTimeout(() => setSaveSuccessMsg(null), 3000);
    } catch (err: any) {
      setScanError(err.response?.data?.detail || "Failed to save corrections.");
    } finally {
      setSavingCorrection(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Confirm and Commit to Catalogue
  // ---------------------------------------------------------------------------
  const handleConfirmProduct = async () => {
    if (!scanSession) return;
    if (!productName.trim()) {
      setScanError("Product name is required to confirm and commit to the catalogue.");
      return;
    }

    setConfirmingProduct(true);
    setScanError(null);

    const payload: ScanConfirmPayload = {
      product_name: productName.trim(),
      brand: brand.trim() || undefined,
      category,
      serving_size: servingSize.trim() || "100g",
      barcode: barcode.trim() || undefined,
      ingredients,
      raw_ingredients_text: rawIngredientsText,
      nutrition_facts: nutritionFacts,
      declared_allergens: declaredAllergens,
      precautionary_allergens: precautionaryAllergens,
    };

    try {
      const res = await api.confirmScan(scanSession.id, payload);
      // Navigate to the newly created product in catalogue
      navigate(`/catalogue/${res.product_id}`);
    } catch (err: any) {
      setScanError(
        err.response?.data?.detail || "Failed to confirm and save product to catalogue."
      );
    } finally {
      setConfirmingProduct(false);
    }
  };

  const handleResetForNewScan = () => {
    clearAllImages();
    setScanSession(null);
    setScanError(null);
    setSaveSuccessMsg(null);
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-sm text-slate-500 mb-1">
            <Link to="/dashboard" className="hover:text-emerald-600 flex items-center gap-1">
              <ArrowLeft className="h-4 w-4" /> Dashboard
            </Link>
            <span>/</span>
            <span className="text-slate-800 font-medium">Food Scanner</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            Scan Food Label
            <Badge variant="outline" className="text-emerald-700 bg-emerald-50 border-emerald-300 ml-2">
              <Sparkles className="h-3 w-3 mr-1 text-emerald-600" /> Day 4 Pipeline
            </Badge>
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Capture food package labels to automatically extract ingredients, nutrition facts, and declared allergens.
          </p>
        </div>

        {scanSession && (
          <Button
            variant="outline"
            onClick={handleResetForNewScan}
            className="self-start sm:self-auto border-slate-300"
          >
            <RefreshCw className="h-4 w-4 mr-1.5" /> Scan Another Product
          </Button>
        )}
      </div>

      {/* Global Alerts */}
      {scanError && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Scan Error</p>
            <p className="mt-0.5">{scanError}</p>
          </div>
          <button onClick={() => setScanError(null)} className="text-rose-500 hover:text-rose-700">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {saveSuccessMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center gap-2">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0" />
          <span>{saveSuccessMsg}</span>
        </div>
      )}

      {/* =========================================================================
          SECTION 1: UPLOAD & CAMERA CAPTURE (Shown when not reviewing or to add more)
          ========================================================================= */}
      {!scanSession && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Capture Controls Column */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="border-slate-200 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Camera className="h-5 w-5 text-emerald-600" />
                  Capture or Upload Label Photos
                </CardTitle>
                <CardDescription>
                  Upload one or multiple images of the product: front packaging, ingredients list, or nutrition table.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Active label tag selector for next upload */}
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 pt-1">
                  <Label className="text-xs font-semibold text-slate-700">Image Type Tag:</Label>
                  <select
                    value={selectedCaptureType}
                    onChange={(e: any) => setSelectedCaptureType(e.target.value)}
                    className="text-xs rounded-md border-slate-300 bg-slate-50 py-1.5 px-2.5 focus:border-emerald-500 focus:ring-emerald-500 font-medium text-slate-800"
                  >
                    <option value="ingredients">Ingredients List</option>
                    <option value="nutrition">Nutrition Facts Table</option>
                    <option value="front">Product Front / Packaging</option>
                    <option value="allergens">Allergen Declaration</option>
                    <option value="other">General / Other</option>
                  </select>
                </div>

                {/* Live Camera View (when active) */}
                {cameraActive ? (
                  <div className="relative rounded-2xl overflow-hidden bg-black border border-slate-700 aspect-video flex items-center justify-center">
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      className="w-full h-full object-cover"
                    />
                    <canvas ref={canvasRef} className="hidden" />

                    <div className="absolute bottom-4 inset-x-0 flex items-center justify-center gap-4">
                      <Button
                        type="button"
                        onClick={capturePhoto}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-full px-6 py-2 shadow-lg flex items-center gap-2"
                      >
                        <Camera className="h-5 w-5" /> Capture Photo
                      </Button>
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={stopCamera}
                        className="bg-slate-800/80 hover:bg-slate-900 text-white rounded-full px-4 py-2"
                      >
                        <X className="h-4 w-4 mr-1" /> Close Camera
                      </Button>
                    </div>
                  </div>
                ) : (
                  /* Upload / Camera Launch Area */
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* File Upload Box */}
                    <div
                      onClick={() => fileInputRef.current?.click()}
                      className="border-2 border-dashed border-slate-300 hover:border-emerald-500 hover:bg-emerald-50/30 rounded-2xl p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center space-y-2"
                    >
                      <div className="h-12 w-12 rounded-full bg-emerald-100/60 text-emerald-700 flex items-center justify-center">
                        <Upload className="h-6 w-6" />
                      </div>
                      <p className="text-sm font-semibold text-slate-800">
                        Choose Label Images
                      </p>
                      <p className="text-xs text-slate-500">
                        JPEG, PNG, WebP (Max 10MB per image)
                      </p>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        multiple
                        onChange={handleFileUpload}
                        className="hidden"
                      />
                    </div>

                    {/* Camera Trigger Box */}
                    <div
                      onClick={startCamera}
                      className="border-2 border-dashed border-slate-300 hover:border-emerald-500 hover:bg-emerald-50/30 rounded-2xl p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center space-y-2"
                    >
                      <div className="h-12 w-12 rounded-full bg-emerald-100/60 text-emerald-700 flex items-center justify-center">
                        <Camera className="h-6 w-6" />
                      </div>
                      <p className="text-sm font-semibold text-slate-800">
                        Use Device Camera
                      </p>
                      <p className="text-xs text-slate-500">
                        Snap food label directly in your browser
                      </p>
                    </div>
                  </div>
                )}

                {cameraError && (
                  <p className="text-xs text-rose-600 bg-rose-50 p-2.5 rounded-lg border border-rose-200">
                    {cameraError}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Queued Images List */}
            {images.length > 0 && (
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="pb-3 flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-semibold">
                      Attached Images ({images.length})
                    </CardTitle>
                    <CardDescription>
                      Review attached label images before triggering the OCR pipeline.
                    </CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearAllImages}
                    className="text-slate-500 hover:text-rose-600 text-xs"
                  >
                    <Trash2 className="h-3.5 w-3.5 mr-1" /> Clear All
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                    {images.map((img) => (
                      <div
                        key={img.id}
                        className="relative rounded-xl border border-slate-200 overflow-hidden bg-slate-50 flex flex-col group shadow-2xs"
                      >
                        <div className="aspect-4/3 w-full overflow-hidden bg-slate-100 relative">
                          <img
                            src={img.previewUrl}
                            alt="Scan label preview"
                            className="w-full h-full object-cover"
                          />
                          <button
                            type="button"
                            onClick={() => removeImage(img.id)}
                            className="absolute top-2 right-2 p-1.5 rounded-full bg-rose-600 text-white shadow-md hover:bg-rose-700 transition"
                            title="Remove image"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </div>
                        <div className="p-2.5 bg-white space-y-1.5 flex-1 flex flex-col justify-between">
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] text-slate-500 truncate max-w-[120px]">
                              {img.file.name}
                            </span>
                            <span className="text-[10px] text-slate-400">
                              {(img.file.size / 1024).toFixed(0)} KB
                            </span>
                          </div>
                          <select
                            value={img.labelType}
                            onChange={(e: any) =>
                              updateImageLabelType(img.id, e.target.value)
                            }
                            className="text-[11px] w-full rounded border-slate-200 bg-slate-50 py-1 px-1.5 text-slate-700 font-medium"
                          >
                            <option value="ingredients">Ingredients List</option>
                            <option value="nutrition">Nutrition Table</option>
                            <option value="front">Front Label</option>
                            <option value="allergens">Allergen Notice</option>
                            <option value="other">Other</option>
                          </select>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Scan Trigger Button */}
                  <div className="pt-6">
                    <Button
                      onClick={handleExecuteScan}
                      disabled={scanLoading}
                      className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-6 rounded-xl text-base font-semibold shadow-md flex items-center justify-center gap-2"
                    >
                      {scanLoading ? (
                        <>
                          <RefreshCw className="h-5 w-5 animate-spin" />
                          Running OpenCV Preprocessing & OCR Extraction...
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-5 w-5" />
                          Run Food Scanner ({images.length} {images.length === 1 ? "Image" : "Images"})
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Scanner Instructions & Guidelines Sidebar */}
          <div className="space-y-6">
            <Card className="border-emerald-100 bg-emerald-50/40 shadow-xs">
              <CardHeader className="pb-3">
                <CardTitle className="text-base text-emerald-900 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  Tips for Best OCR Accuracy
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs text-emerald-800/90 leading-relaxed">
                <div className="flex items-start gap-2">
                  <span className="font-bold text-emerald-700">1.</span>
                  <span>Ensure bright, uniform lighting without glare or strong shadows.</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="font-bold text-emerald-700">2.</span>
                  <span>Capture the ingredients and nutrition table flat and in sharp focus.</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="font-bold text-emerald-700">3.</span>
                  <span>
                    Upload separate photos for front packaging and rear nutrition tables for multi-angle parsing.
                  </span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="font-bold text-emerald-700">4.</span>
                  <span>
                    OCR results are automatically flagged for manual review before saving to the catalogue.
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 shadow-xs">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold text-slate-800">
                  Data Verification Notice
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-slate-600 space-y-2">
                <p>
                  NutriLens never treats automated OCR outputs as verified product truth. All scanned data is presented for user review and marked with <code>data_source="scan"</code>.
                </p>
                <p>
                  Any missing or ambiguous values will be highlighted with uncertainty flags.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* =========================================================================
          SECTION 2: REVIEW & MANUAL CORRECTION WORKFLOW (Active after OCR scan)
          ========================================================================= */}
      {scanSession && (
        <div className="space-y-6">
          {/* Status & Uncertainty Banner */}
          <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Badge
                  variant="outline"
                  className="bg-emerald-50 text-emerald-700 border-emerald-300 font-medium"
                >
                  Status: {scanSession.status.toUpperCase()}
                </Badge>
                <span className="text-xs text-slate-500">
                  Scan ID: <code className="font-mono">{scanSession.id.slice(0, 8)}...</code>
                </span>
                <span className="text-xs text-slate-500">
                  Confidence:{" "}
                  <strong>
                    {((scanSession.extracted_data?.ocr_confidence || 0) * 100).toFixed(0)}%
                  </strong>
                </span>
              </div>
              <p className="text-xs text-slate-600">
                Please verify all extracted fields below. Correct any OCR misreadings, review allergens, and confirm to add to your food catalogue.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowRawOcr(!showRawOcr)}
                className="text-xs flex items-center gap-1.5"
              >
                <FileText className="h-3.5 w-3.5" />
                {showRawOcr ? "Hide Raw OCR" : "Inspect Raw OCR"}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleSaveCorrections}
                disabled={savingCorrection}
                className="text-xs flex items-center gap-1.5"
              >
                {savingCorrection ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
                Save Corrections
              </Button>
              <Button
                size="sm"
                onClick={handleConfirmProduct}
                disabled={confirmingProduct}
                className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs flex items-center gap-1.5"
              >
                {confirmingProduct ? (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                )}
                Confirm & Add to Catalogue
              </Button>
            </div>
          </div>

          {/* Uncertainty Warnings if any */}
          {scanSession.extracted_data?.uncertainty_flags &&
            scanSession.extracted_data.uncertainty_flags.length > 0 && (
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-1.5">
                <div className="flex items-center gap-1.5 font-semibold text-amber-800">
                  <AlertTriangle className="h-4 w-4 text-amber-600" />
                  <span>Uncertainty & Review Flags:</span>
                </div>
                <ul className="list-disc list-inside space-y-0.5 text-amber-800/90 pl-1">
                  {scanSession.extracted_data.uncertainty_flags.map((flag, idx) => (
                    <li key={idx}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}

          {/* Raw OCR Text Drawer (toggleable) */}
          {showRawOcr && (
            <Card className="border-slate-200 bg-slate-900 text-slate-100 font-mono text-xs shadow-md">
              <CardHeader className="py-2.5 px-4 border-b border-slate-800 flex flex-row items-center justify-between">
                <CardTitle className="text-xs text-slate-300 font-normal">
                  Raw OCR Stream (OpenCV Preprocessed & Extracted)
                </CardTitle>
                <Badge variant="outline" className="text-slate-400 border-slate-700 text-[10px]">
                  Engine: {scanSession.extracted_data?.ocr_engine || "PaddleOCR / Fallback"}
                </Badge>
              </CardHeader>
              <CardContent className="p-4 max-h-64 overflow-y-auto whitespace-pre-wrap leading-relaxed text-slate-200">
                {scanSession.raw_ocr_text || "No raw text was recognized."}
              </CardContent>
            </Card>
          )}

          {/* Main Review Form */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: Editable Form */}
            <div className="lg:col-span-2 space-y-6">
              {/* Basic Product Info */}
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base font-semibold text-slate-900">
                    Product Identity
                  </CardTitle>
                  <CardDescription>
                    Verify product name, brand, category, and serving portion size.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <Label htmlFor="product-name" className="text-xs font-semibold">
                        Product Name <span className="text-rose-500">*</span>
                      </Label>
                      <Input
                        id="product-name"
                        value={productName}
                        onChange={(e) => setProductName(e.target.value)}
                        placeholder="e.g. NutriChoice Digestive"
                        className="text-sm font-medium"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <Label htmlFor="brand" className="text-xs font-semibold">
                        Brand
                      </Label>
                      <Input
                        id="brand"
                        value={brand}
                        onChange={(e) => setBrand(e.target.value)}
                        placeholder="e.g. Britannia"
                        className="text-sm"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="space-y-1.5">
                      <Label htmlFor="category" className="text-xs font-semibold">
                        Category
                      </Label>
                      <select
                        id="category"
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        className="w-full text-xs rounded-md border border-slate-300 bg-white py-2 px-3 focus:border-emerald-500 focus:ring-emerald-500 font-medium text-slate-800"
                      >
                        {CATEGORIES.map((cat) => (
                          <option key={cat} value={cat}>
                            {cat}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="space-y-1.5">
                      <Label htmlFor="serving-size" className="text-xs font-semibold">
                        Serving Size
                      </Label>
                      <Input
                        id="serving-size"
                        value={servingSize}
                        onChange={(e) => setServingSize(e.target.value)}
                        placeholder="e.g. 30g / 2 biscuits"
                        className="text-sm"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <Label htmlFor="barcode" className="text-xs font-semibold">
                        Barcode (optional)
                      </Label>
                      <Input
                        id="barcode"
                        value={barcode}
                        onChange={(e) => setBarcode(e.target.value)}
                        placeholder="e.g. 8901063012345"
                        className="text-sm font-mono"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Ingredients Section */}
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="pb-3 flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-semibold text-slate-900">
                      Ingredients List ({ingredients.length})
                    </CardTitle>
                    <CardDescription>
                      Review recognized ingredients. Add missing items or remove OCR errors.
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Ingredient Tags Display */}
                  <div className="flex flex-wrap gap-2 min-h-12 p-3 bg-slate-50 border border-slate-200 rounded-xl">
                    {ingredients.length === 0 ? (
                      <span className="text-xs text-slate-400 italic">
                        No individual ingredients parsed yet. Add below or paste from raw text.
                      </span>
                    ) : (
                      ingredients.map((ing, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-emerald-50 text-emerald-900 border border-emerald-200 group"
                        >
                          <span>{ing}</span>
                          <button
                            type="button"
                            onClick={() => removeIngredientTag(idx)}
                            className="text-emerald-500 hover:text-rose-600 ml-1 transition"
                            title="Remove ingredient"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </span>
                      ))
                    )}
                  </div>

                  {/* Add New Ingredient Input */}
                  <div className="flex gap-2">
                    <Input
                      value={newIngredient}
                      onChange={(e) => setNewIngredient(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addIngredientTag();
                        }
                      }}
                      placeholder="Add an ingredient (e.g. Whole Wheat Flour)..."
                      className="text-xs"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={addIngredientTag}
                      className="text-xs flex items-center gap-1"
                    >
                      <Plus className="h-3.5 w-3.5" /> Add
                    </Button>
                  </div>

                  {/* Raw Ingredients Text Field */}
                  <div className="space-y-1.5 pt-2">
                    <Label className="text-xs font-semibold text-slate-600">
                      Raw Ingredients Label Text (Original OCR)
                    </Label>
                    <textarea
                      value={rawIngredientsText}
                      onChange={(e) => setRawIngredientsText(e.target.value)}
                      rows={3}
                      className="w-full text-xs font-mono rounded-lg border border-slate-300 p-2.5 focus:border-emerald-500 focus:ring-emerald-500 text-slate-700 bg-white"
                      placeholder="Original raw label text for reference..."
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Nutrition Facts Table */}
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base font-semibold text-slate-900">
                    Nutrition Facts (Per 100g)
                  </CardTitle>
                  <CardDescription>
                    Verify detected macronutrient values. Leave blank if not declared on label.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                    <div className="space-y-1">
                      <Label className="text-[11px] text-slate-600">Calories (kcal)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={nutritionFacts.energy_kcal ?? ""}
                        onChange={(e) =>
                          setNutritionFacts({
                            ...nutritionFacts,
                            energy_kcal: e.target.value ? parseFloat(e.target.value) : null,
                          })
                        }
                        className="text-xs font-semibold"
                        placeholder="kcal"
                      />
                    </div>

                    <div className="space-y-1">
                      <Label className="text-[11px] text-slate-600">Total Fat (g)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={nutritionFacts.total_fat_g ?? ""}
                        onChange={(e) =>
                          setNutritionFacts({
                            ...nutritionFacts,
                            total_fat_g: e.target.value ? parseFloat(e.target.value) : null,
                          })
                        }
                        className="text-xs"
                        placeholder="g"
                      />
                    </div>

                    <div className="space-y-1">
                      <Label className="text-[11px] text-slate-600">Sat Fat (g)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={nutritionFacts.saturated_fat_g ?? ""}
                        onChange={(e) =>
                          setNutritionFacts({
                            ...nutritionFacts,
                            saturated_fat_g: e.target.value ? parseFloat(e.target.value) : null,
                          })
                        }
                        className="text-xs"
                        placeholder="g"
                      />
                    </div>

                    <div className="space-y-1">
                      <Label className="text-[11px] text-slate-600">Trans Fat (g)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={nutritionFacts.trans_fat_g ?? ""}
                        onChange={(e) =>
                          setNutritionFacts({
                            ...nutritionFacts,
                            trans_fat_g: e.target.value ? parseFloat(e.target.value) : null,
                          })
                        }
                        className="text-xs"
                        placeholder="g"
                      />
                    </div>

                    <div className="space-y-1">
                      <Label className="text-[11px] text-slate-600">Carbs (g)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={nutritionFacts.carbohydrates_g ?? ""}
                        onChange={(e) =>
                          setNutritionFacts({
                            ...nutritionFacts,
                            carbohydrates_g: e.target.value ? parseFloat(e.target.value) : null,
                          })
                        }
                        className="text-xs"
                        placeholder="g"
                      />
                    </div>

                    <div className="space-y-1">
                      <Label className="text-[11px] text-slate-600">Total Sugar (g)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={nutritionFacts.total_sugar_g ?? ""}
                        onChange={(e) =>
                          setNutritionFacts({
                            ...nutritionFacts,
                            total_sugar_g: e.target.value ? parseFloat(e.target.value) : null,
                          })
                        }
                        className="text-xs"
                        placeholder="g"
                      />
                    </div>

                    <div className="space-y-1">
                      <Label className="text-[11px] text-slate-600">Added Sugar (g)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={nutritionFacts.added_sugar_g ?? ""}
                        onChange={(e) =>
                          setNutritionFacts({
                            ...nutritionFacts,
                            added_sugar_g: e.target.value ? parseFloat(e.target.value) : null,
                          })
                        }
                        className="text-xs"
                        placeholder="g"
                      />
                    </div>

                    <div className="space-y-1">
                      <Label className="text-[11px] text-slate-600">Dietary Fibre (g)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={nutritionFacts.dietary_fibre_g ?? ""}
                        onChange={(e) =>
                          setNutritionFacts({
                            ...nutritionFacts,
                            dietary_fibre_g: e.target.value ? parseFloat(e.target.value) : null,
                          })
                        }
                        className="text-xs"
                        placeholder="g"
                      />
                    </div>

                    <div className="space-y-1">
                      <Label className="text-[11px] text-slate-600">Protein (g)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={nutritionFacts.protein_g ?? ""}
                        onChange={(e) =>
                          setNutritionFacts({
                            ...nutritionFacts,
                            protein_g: e.target.value ? parseFloat(e.target.value) : null,
                          })
                        }
                        className="text-xs"
                        placeholder="g"
                      />
                    </div>

                    <div className="space-y-1">
                      <Label className="text-[11px] text-slate-600">Sodium (mg)</Label>
                      <Input
                        type="number"
                        step="1"
                        value={nutritionFacts.sodium_mg ?? ""}
                        onChange={(e) =>
                          setNutritionFacts({
                            ...nutritionFacts,
                            sodium_mg: e.target.value ? parseFloat(e.target.value) : null,
                          })
                        }
                        className="text-xs"
                        placeholder="mg"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Allergens Section */}
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base font-semibold text-slate-900 flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 text-amber-600" />
                    Allergen Declarations
                  </CardTitle>
                  <CardDescription>
                    Declared allergens ("Contains: ...") and precautionary cross-contact statements ("May contain: ...").
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Declared Allergens */}
                  <div className="space-y-2">
                    <Label className="text-xs font-semibold text-slate-700">
                      Declared Allergens (Contains)
                    </Label>
                    <div className="flex flex-wrap gap-2 p-2.5 bg-rose-50/50 border border-rose-200 rounded-lg min-h-10">
                      {declaredAllergens.length === 0 ? (
                        <span className="text-xs text-slate-400 italic">None declared.</span>
                      ) : (
                        declaredAllergens.map((alg, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-100 text-rose-800"
                          >
                            <span>{alg}</span>
                            <button
                              type="button"
                              onClick={() => removeDeclaredAllergenTag(idx)}
                              className="text-rose-500 hover:text-rose-800"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </span>
                        ))
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Input
                        value={newDeclaredAllergen}
                        onChange={(e) => setNewDeclaredAllergen(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            addDeclaredAllergenTag();
                          }
                        }}
                        placeholder="Add declared allergen (e.g. Wheat, Soy)..."
                        className="text-xs"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={addDeclaredAllergenTag}
                        className="text-xs"
                      >
                        Add
                      </Button>
                    </div>
                  </div>

                  {/* Precautionary Allergens */}
                  <div className="space-y-2 pt-2">
                    <Label className="text-xs font-semibold text-slate-700">
                      Precautionary Allergens (May Contain / Processed in Facility)
                    </Label>
                    <div className="flex flex-wrap gap-2 p-2.5 bg-amber-50/50 border border-amber-200 rounded-lg min-h-10">
                      {precautionaryAllergens.length === 0 ? (
                        <span className="text-xs text-slate-400 italic">None declared.</span>
                      ) : (
                        precautionaryAllergens.map((alg, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-900"
                          >
                            <span>{alg}</span>
                            <button
                              type="button"
                              onClick={() => removePrecautionaryAllergenTag(idx)}
                              className="text-amber-600 hover:text-amber-900"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </span>
                        ))
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Input
                        value={newPrecautionaryAllergen}
                        onChange={(e) => setNewPrecautionaryAllergen(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            addPrecautionaryAllergenTag();
                          }
                        }}
                        placeholder="Add precautionary allergen (e.g. Tree Nuts, Milk)..."
                        className="text-xs"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={addPrecautionaryAllergenTag}
                        className="text-xs"
                      >
                        Add
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Right Column: Source Images & Actions */}
            <div className="space-y-6">
              {/* Source Images Review */}
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                    <ImageIcon className="h-4 w-4 text-emerald-600" />
                    Source Scan Images
                  </CardTitle>
                  <CardDescription>
                    Reference original uploaded photos during review.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {scanSession.images && scanSession.images.length > 0 ? (
                    <div className="space-y-3">
                      {scanSession.images.map((img: any, idx: number) => {
                        const imgUrl = img.url?.startsWith("http")
                          ? img.url
                          : `${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}${img.url}`;
                        return (
                          <div
                            key={idx}
                            className="rounded-xl border border-slate-200 overflow-hidden bg-slate-50"
                          >
                            <div className="aspect-4/3 overflow-hidden bg-slate-100 relative group">
                              <img
                                src={imgUrl}
                                alt={`Scan source ${idx + 1}`}
                                className="w-full h-full object-cover"
                              />
                              <a
                                href={imgUrl}
                                target="_blank"
                                rel="noreferrer"
                                className="absolute bottom-2 right-2 p-1.5 rounded-lg bg-slate-900/80 text-white text-[11px] opacity-0 group-hover:opacity-100 transition flex items-center gap-1"
                              >
                                <Maximize2 className="h-3 w-3" /> Full View
                              </a>
                            </div>
                            <div className="p-2 bg-white flex items-center justify-between text-[11px] text-slate-600">
                              <span className="font-medium capitalize">
                                {img.label_type} Label
                              </span>
                              <span className="text-slate-400">Image #{idx + 1}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic">No image reference available.</p>
                  )}
                </CardContent>
              </Card>

              {/* Action Buttons Box */}
              <Card className="border-emerald-200 bg-emerald-50/30 shadow-sm">
                <CardContent className="p-5 space-y-3">
                  <Button
                    onClick={handleConfirmProduct}
                    disabled={confirmingProduct}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-5 rounded-xl text-sm font-semibold shadow-md flex items-center justify-center gap-2"
                  >
                    {confirmingProduct ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        Saving to Catalogue...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="h-4 w-4" />
                        Confirm & Save to Catalogue
                      </>
                    )}
                  </Button>

                  <Button
                    variant="outline"
                    onClick={handleSaveCorrections}
                    disabled={savingCorrection}
                    className="w-full text-xs border-slate-300"
                  >
                    {savingCorrection ? "Saving..." : "Save Corrections (Draft)"}
                  </Button>

                  <Button
                    variant="ghost"
                    onClick={handleResetForNewScan}
                    className="w-full text-xs text-slate-500 hover:text-slate-800"
                  >
                    Discard & Scan New Image
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
