import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Plus,
  Search,
  CheckCircle2,
  XCircle,
  Edit2,
  Trash2,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Loader2,
} from "lucide-react";
import { api } from "@/services/api";
import { ProductDetail, AdminProductCreatePayload } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export const AdminProductsPage: React.FC = () => {
  const [products, setProducts] = useState<ProductDetail[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [search, setSearch] = useState<string>("");
  const [category, setCategory] = useState<string>("");
  const [verificationFilter, setVerificationFilter] = useState<string>("all");
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [_error, setError] = useState<string | null>(null);

  // Modal State for Add / Edit
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [editingProduct, setEditingProduct] = useState<ProductDetail | null>(null);
  const [formData, setFormData] = useState<{
    name: string;
    brand: string;
    category: string;
    barcode: string;
    description: string;
    serving_size: number | "";
    serving_unit: string;
    is_verified: boolean;
    image_url: string;
    // Nutrition Facts per 100g
    energy_kcal: number | "";
    total_fat_g: number | "";
    saturated_fat_g: number | "";
    trans_fat_g: number | "";
    carbohydrates_g: number | "";
    total_sugar_g: number | "";
    added_sugar_g: number | "";
    dietary_fibre_g: number | "";
    protein_g: number | "";
    sodium_mg: number | "";
    // Comma-separated raw strings for simplicity
    ingredients_str: string;
    allergens_str: string;
  }>({
    name: "",
    brand: "",
    category: "packaged_food",
    barcode: "",
    description: "",
    serving_size: 100,
    serving_unit: "g",
    is_verified: false,
    image_url: "",
    energy_kcal: "",
    total_fat_g: "",
    saturated_fat_g: "",
    trans_fat_g: "",
    carbohydrates_g: "",
    total_sugar_g: "",
    added_sugar_g: "",
    dietary_fibre_g: "",
    protein_g: "",
    sodium_mg: "",
    ingredients_str: "",
    allergens_str: "",
  });

  const fetchProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      const isVerifiedParam =
        verificationFilter === "verified"
          ? true
          : verificationFilter === "unverified"
          ? false
          : undefined;

      const data = await api.getAdminProducts({
        search: search.trim() || undefined,
        category: category.trim() || undefined,
        is_verified: isVerifiedParam,
        page,
        page_size: pageSize,
      });

      setProducts(data.items);
      setTotal(data.total);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load products.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [page, category, verificationFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchProducts();
  };

  const handleToggleVerify = async (product: ProductDetail) => {
    try {
      setActionLoading(`verify-${product.id}`);
      const updated = await api.verifyAdminProduct(product.id, !product.is_verified);
      setProducts((prev) =>
        prev.map((p) => (p.id === product.id ? { ...p, is_verified: updated.is_verified } : p))
      );
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to update verification status.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (product: ProductDetail) => {
    if (!window.confirm(`Are you sure you want to permanently delete "${product.name}"?`)) {
      return;
    }
    try {
      setActionLoading(`delete-${product.id}`);
      await api.deleteAdminProduct(product.id);
      setProducts((prev) => prev.filter((p) => p.id !== product.id));
      setTotal((prev) => Math.max(0, prev - 1));
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to delete product.");
    } finally {
      setActionLoading(null);
    }
  };

  const openCreateModal = () => {
    setEditingProduct(null);
    setFormData({
      name: "",
      brand: "",
      category: "packaged_food",
      barcode: "",
      description: "",
      serving_size: 100,
      serving_unit: "g",
      is_verified: false,
      image_url: "",
      energy_kcal: "",
      total_fat_g: "",
      saturated_fat_g: "",
      trans_fat_g: "",
      carbohydrates_g: "",
      total_sugar_g: "",
      added_sugar_g: "",
      dietary_fibre_g: "",
      protein_g: "",
      sodium_mg: "",
      ingredients_str: "",
      allergens_str: "",
    });
    setModalOpen(true);
  };

  const openEditModal = (product: ProductDetail) => {
    setEditingProduct(product);
    const nf = product.nutrition_facts;
    const ingrNames = (product.product_ingredients || []).map((pi) => pi.ingredient?.name || pi.original_text).filter(Boolean);
    const allergenNames = (product.product_allergens || []).map((pa) => pa.allergen?.name).filter(Boolean);

    setFormData({
      name: product.name,
      brand: product.brand || "",
      category: product.category || "packaged_food",
      barcode: product.barcode || "",
      description: product.description || "",
      serving_size: product.serving_size ? (typeof product.serving_size === "number" ? product.serving_size : Number(product.serving_size) || 100) : 100,
      serving_unit: product.serving_unit || "g",
      is_verified: product.is_verified,
      image_url: product.label_image_url || "",
      energy_kcal: nf?.energy_kcal ?? "",
      total_fat_g: nf?.total_fat_g ?? "",
      saturated_fat_g: nf?.saturated_fat_g ?? "",
      trans_fat_g: nf?.trans_fat_g ?? "",
      carbohydrates_g: nf?.carbohydrates_g ?? "",
      total_sugar_g: nf?.total_sugar_g ?? "",
      added_sugar_g: nf?.added_sugar_g ?? "",
      dietary_fibre_g: nf?.dietary_fibre_g ?? "",
      protein_g: nf?.protein_g ?? "",
      sodium_mg: nf?.sodium_mg ?? "",
      ingredients_str: ingrNames.join(", "),
      allergens_str: allergenNames.join(", "),
    });
    setModalOpen(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      alert("Product name is required.");
      return;
    }

    const nutrition_facts: any = {};
    if (formData.energy_kcal !== "") nutrition_facts.energy_kcal = Number(formData.energy_kcal);
    if (formData.total_fat_g !== "") nutrition_facts.total_fat_g = Number(formData.total_fat_g);
    if (formData.saturated_fat_g !== "") nutrition_facts.saturated_fat_g = Number(formData.saturated_fat_g);
    if (formData.trans_fat_g !== "") nutrition_facts.trans_fat_g = Number(formData.trans_fat_g);
    if (formData.carbohydrates_g !== "") nutrition_facts.carbohydrates_g = Number(formData.carbohydrates_g);
    if (formData.total_sugar_g !== "") nutrition_facts.total_sugar_g = Number(formData.total_sugar_g);
    if (formData.added_sugar_g !== "") nutrition_facts.added_sugar_g = Number(formData.added_sugar_g);
    if (formData.dietary_fibre_g !== "") nutrition_facts.dietary_fibre_g = Number(formData.dietary_fibre_g);
    if (formData.protein_g !== "") nutrition_facts.protein_g = Number(formData.protein_g);
    if (formData.sodium_mg !== "") nutrition_facts.sodium_mg = Number(formData.sodium_mg);

    const ingredients = formData.ingredients_str
      .split(",")
      .map((s, idx) => ({ name: s.trim(), order_index: idx }))
      .filter((item) => item.name.length > 0);

    const allergens = formData.allergens_str
      .split(",")
      .map((s) => ({ name: s.trim(), declaration_type: "declared" as const }))
      .filter((item) => item.name.length > 0);

    const payload: AdminProductCreatePayload = {
      name: formData.name.trim(),
      brand: formData.brand.trim() || undefined,
      category: formData.category.trim() || undefined,
      barcode: formData.barcode.trim() || undefined,
      description: formData.description.trim() || undefined,
      serving_size: formData.serving_size !== "" ? Number(formData.serving_size) : 100,
      serving_unit: formData.serving_unit || "g",
      is_verified: formData.is_verified,
      image_url: formData.image_url.trim() || undefined,
      nutrition_facts,
      ingredients,
      allergens,
    };

    try {
      setActionLoading("submitting");
      if (editingProduct) {
        await api.updateAdminProduct(editingProduct.id, payload);
      } else {
        await api.createAdminProduct(payload);
      }
      setModalOpen(false);
      fetchProducts();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to save product.");
    } finally {
      setActionLoading(null);
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <Link to="/admin" className="text-xs text-purple-600 hover:underline font-semibold flex items-center">
              <ChevronLeft className="h-3 w-3 mr-0.5" /> Admin Dashboard
            </Link>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">Product Catalog Management</h1>
          <p className="text-slate-500 text-xs mt-0.5">
            Administer verified packaging entries, nutrient facts per 100g/ml, and ingredients.
          </p>
        </div>
        <Button onClick={openCreateModal} className="bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-1.5 shadow-sm">
          <Plus className="h-4 w-4" /> Add New Product
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-4">
          <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search products by title, brand, or barcode..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 h-9 text-sm"
              />
            </div>
            <div className="flex items-center gap-2 w-full md:w-auto">
              <select
                value={category}
                onChange={(e) => {
                  setCategory(e.target.value);
                  setPage(1);
                }}
                className="h-9 px-3 rounded-md border border-input bg-background text-xs text-slate-700"
              >
                <option value="">All Categories</option>
                <option value="packaged_food">Packaged Food</option>
                <option value="beverages">Beverages</option>
                <option value="snacks">Snacks</option>
                <option value="dairy">Dairy</option>
                <option value="cereals">Cereals</option>
                <option value="confectionery">Confectionery</option>
              </select>

              <select
                value={verificationFilter}
                onChange={(e) => {
                  setVerificationFilter(e.target.value);
                  setPage(1);
                }}
                className="h-9 px-3 rounded-md border border-input bg-background text-xs text-slate-700"
              >
                <option value="all">All Status</option>
                <option value="verified">Verified Only</option>
                <option value="unverified">Unverified Only</option>
              </select>

              <Button type="submit" size="sm" variant="secondary" className="h-9 text-xs">
                Filter
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Product List Table */}
      <Card className="border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b text-xs uppercase font-semibold text-slate-500">
              <tr>
                <th className="py-3 px-4">Product</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Barcode</th>
                <th className="py-3 px-4 text-center">Score</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-emerald-600" />
                    Loading products...
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No products found matching the criteria.
                  </td>
                </tr>
              ) : (
                products.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">{p.name}</div>
                      <div className="text-xs text-slate-400">{p.brand || "Unknown Brand"}</div>
                    </td>
                    <td className="py-3 px-4 capitalize text-xs">{p.category || "General"}</td>
                    <td className="py-3 px-4 font-mono text-xs">{p.barcode || "—"}</td>
                    <td className="py-3 px-4 text-center font-bold">
                      {p.nutrition_analysis?.score !== null && p.nutrition_analysis?.score !== undefined ? (
                        <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-xs border border-emerald-200">
                          {p.nutrition_analysis.score}/100
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleToggleVerify(p)}
                        disabled={actionLoading === `verify-${p.id}`}
                        className="inline-flex items-center gap-1 cursor-pointer transition-opacity hover:opacity-80"
                        title="Click to toggle verified status"
                      >
                        {p.is_verified ? (
                          <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-300 text-[11px]">
                            <CheckCircle2 className="h-3 w-3 mr-1 text-emerald-600" /> Verified
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-300 text-[11px]">
                            <XCircle className="h-3 w-3 mr-1 text-amber-600" /> Unverified
                          </Badge>
                        )}
                      </button>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Link
                          to={`/catalogue/${p.id}`}
                          className="p-1.5 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100"
                          title="View public details"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Link>
                        <button
                          onClick={() => openEditModal(p)}
                          className="p-1.5 rounded text-blue-600 hover:bg-blue-50"
                          title="Edit product"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(p)}
                          disabled={actionLoading === `delete-${p.id}`}
                          className="p-1.5 rounded text-red-600 hover:bg-red-50"
                          title="Delete product"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3 bg-slate-50 border-t flex items-center justify-between text-xs text-slate-500">
          <span>
            Showing {products.length} of {total} products
          </span>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="h-8 text-xs"
            >
              <ChevronLeft className="h-3.5 w-3.5 mr-1" /> Previous
            </Button>
            <span className="font-semibold text-slate-700">
              Page {page} of {totalPages}
            </span>
            <Button
              size="sm"
              variant="outline"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="h-8 text-xs"
            >
              Next <ChevronRight className="h-3.5 w-3.5 ml-1" />
            </Button>
          </div>
        </div>
      </Card>

      {/* Modal for Add / Edit Product */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b flex items-center justify-between bg-slate-50">
              <h2 className="text-base font-bold text-slate-900">
                {editingProduct ? `Edit Product: ${editingProduct.name}` : "Create New Catalogue Product"}
              </h2>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleFormSubmit} className="p-6 overflow-y-auto space-y-4 text-xs">
              {/* Basic Fields */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Product Name *</label>
                  <Input
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. Organic Almond Milk"
                    className="h-8 text-xs"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Brand</label>
                  <Input
                    value={formData.brand}
                    onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                    placeholder="e.g. PureHealth"
                    className="h-8 text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Category</label>
                  <Input
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    placeholder="e.g. packaged_food, beverages"
                    className="h-8 text-xs"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Barcode (GTIN/EAN)</label>
                  <Input
                    value={formData.barcode}
                    onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                    placeholder="e.g. 8901234567890"
                    className="h-8 text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Serving Size</label>
                  <div className="flex gap-1">
                    <Input
                      type="number"
                      value={formData.serving_size}
                      onChange={(e) => setFormData({ ...formData, serving_size: e.target.value ? Number(e.target.value) : "" })}
                      className="h-8 text-xs w-2/3"
                    />
                    <Input
                      value={formData.serving_unit}
                      onChange={(e) => setFormData({ ...formData, serving_unit: e.target.value })}
                      className="h-8 text-xs w-1/3"
                      placeholder="g"
                    />
                  </div>
                </div>
              </div>

              {/* Verified Checkbox */}
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="is_verified"
                  checked={formData.is_verified}
                  onChange={(e) => setFormData({ ...formData, is_verified: e.target.checked })}
                  className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500 h-4 w-4"
                />
                <label htmlFor="is_verified" className="font-semibold text-slate-800 cursor-pointer">
                  Mark as Verified Product Record
                </label>
              </div>

              {/* Nutrition Facts per 100g */}
              <div className="pt-2 border-t">
                <p className="font-bold text-slate-800 mb-2 uppercase tracking-wider text-[11px]">
                  Nutrition Facts (Standardized per 100g / 100ml)
                </p>
                <div className="grid grid-cols-5 gap-2">
                  <div>
                    <label className="text-[11px] text-slate-600">Energy (kcal)</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={formData.energy_kcal}
                      onChange={(e) => setFormData({ ...formData, energy_kcal: e.target.value ? Number(e.target.value) : "" })}
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600">Total Fat (g)</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={formData.total_fat_g}
                      onChange={(e) => setFormData({ ...formData, total_fat_g: e.target.value ? Number(e.target.value) : "" })}
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600">Sat Fat (g)</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={formData.saturated_fat_g}
                      onChange={(e) => setFormData({ ...formData, saturated_fat_g: e.target.value ? Number(e.target.value) : "" })}
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600">Trans Fat (g)</label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.trans_fat_g}
                      onChange={(e) => setFormData({ ...formData, trans_fat_g: e.target.value ? Number(e.target.value) : "" })}
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600">Carbs (g)</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={formData.carbohydrates_g}
                      onChange={(e) => setFormData({ ...formData, carbohydrates_g: e.target.value ? Number(e.target.value) : "" })}
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600">Total Sugar (g)</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={formData.total_sugar_g}
                      onChange={(e) => setFormData({ ...formData, total_sugar_g: e.target.value ? Number(e.target.value) : "" })}
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600">Added Sugar (g)</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={formData.added_sugar_g}
                      onChange={(e) => setFormData({ ...formData, added_sugar_g: e.target.value ? Number(e.target.value) : "" })}
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600">Fibre (g)</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={formData.dietary_fibre_g}
                      onChange={(e) => setFormData({ ...formData, dietary_fibre_g: e.target.value ? Number(e.target.value) : "" })}
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600">Protein (g)</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={formData.protein_g}
                      onChange={(e) => setFormData({ ...formData, protein_g: e.target.value ? Number(e.target.value) : "" })}
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600">Sodium (mg)</label>
                    <Input
                      type="number"
                      step="1"
                      value={formData.sodium_mg}
                      onChange={(e) => setFormData({ ...formData, sodium_mg: e.target.value ? Number(e.target.value) : "" })}
                      className="h-7 text-xs"
                    />
                  </div>
                </div>
              </div>

              {/* Ingredients & Allergens */}
              <div className="pt-2 border-t space-y-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Ingredients (comma separated)
                  </label>
                  <textarea
                    rows={2}
                    value={formData.ingredients_str}
                    onChange={(e) => setFormData({ ...formData, ingredients_str: e.target.value })}
                    placeholder="e.g. Rolled Oats, Cane Sugar, Palm Oil, Cocoa Powder"
                    className="w-full p-2 border rounded-md text-xs focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Declared Allergens (comma separated)
                  </label>
                  <Input
                    value={formData.allergens_str}
                    onChange={(e) => setFormData({ ...formData, allergens_str: e.target.value })}
                    placeholder="e.g. Milk, Soy, Tree Nuts"
                    className="h-8 text-xs"
                  />
                </div>
              </div>

              <div className="pt-4 border-t flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={actionLoading === "submitting"}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  {actionLoading === "submitting" ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-1.5" />
                  ) : null}
                  Save Product
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
