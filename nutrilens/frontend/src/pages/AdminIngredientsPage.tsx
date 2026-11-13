import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Loader2,
} from "lucide-react";
import { api } from "@/services/api";
import { AdminIngredientItem, AdminIngredientCreatePayload, Allergen } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export const AdminIngredientsPage: React.FC = () => {
  const [ingredients, setIngredients] = useState<AdminIngredientItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(15);
  const [search, setSearch] = useState<string>("");
  const [concernFilter, setConcernFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Allergens drawer/modal state
  const [allergens, setAllergens] = useState<Allergen[]>([]);
  const [allergenModalOpen, setAllergenModalOpen] = useState<boolean>(false);
  const [newAllergen, setNewAllergen] = useState<{ name: string; code: string; description: string }>({
    name: "",
    code: "",
    description: "",
  });

  // Ingredient Add / Edit Modal
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [editingIngredient, setEditingIngredient] = useState<AdminIngredientItem | null>(null);
  const [formData, setFormData] = useState<{
    name: string;
    category: string;
    description: string;
    concern_level: string;
    is_additive: boolean;
    ins_number: string;
    source_evidence: string;
    aliases_str: string;
  }>({
    name: "",
    category: "",
    description: "",
    concern_level: "low",
    is_additive: false,
    ins_number: "",
    source_evidence: "",
    aliases_str: "",
  });

  const fetchIngredients = async () => {
    try {
      setLoading(true);
      const data = await api.getAdminIngredients({
        search: search.trim() || undefined,
        category: categoryFilter.trim() || undefined,
        concern_level: concernFilter.trim() || undefined,
        page,
        page_size: pageSize,
      });
      setIngredients(data.items);
      setTotal(data.total);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to load ingredients.");
    } finally {
      setLoading(false);
    }
  };

  const fetchAllergens = async () => {
    try {
      const data = await api.getAdminAllergens();
      setAllergens(data);
    } catch (err) {
      console.error("Failed to load allergens", err);
    }
  };

  useEffect(() => {
    fetchIngredients();
  }, [page, concernFilter, categoryFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchIngredients();
  };

  const handleDelete = async (ingr: AdminIngredientItem) => {
    if (!window.confirm(`Are you sure you want to delete ingredient "${ingr.name}"?`)) {
      return;
    }
    try {
      setActionLoading(`delete-${ingr.id}`);
      await api.deleteAdminIngredient(ingr.id);
      setIngredients((prev) => prev.filter((i) => i.id !== ingr.id));
      setTotal((t) => Math.max(0, t - 1));
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to delete ingredient.");
    } finally {
      setActionLoading(null);
    }
  };

  const openCreateModal = () => {
    setEditingIngredient(null);
    setFormData({
      name: "",
      category: "",
      description: "",
      concern_level: "low",
      is_additive: false,
      ins_number: "",
      source_evidence: "",
      aliases_str: "",
    });
    setModalOpen(true);
  };

  const openEditModal = (ingr: AdminIngredientItem) => {
    setEditingIngredient(ingr);
    setFormData({
      name: ingr.name,
      category: ingr.category || "",
      description: ingr.description || "",
      concern_level: ingr.concern_level || "low",
      is_additive: ingr.is_additive,
      ins_number: ingr.ins_number || "",
      source_evidence: ingr.source_evidence || "",
      aliases_str: (ingr.aliases || []).join(", "),
    });
    setModalOpen(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      alert("Ingredient name is required.");
      return;
    }

    const aliases = formData.aliases_str
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    const payload: AdminIngredientCreatePayload = {
      name: formData.name.trim(),
      category: formData.category.trim() || undefined,
      description: formData.description.trim() || undefined,
      concern_level: formData.concern_level,
      is_additive: formData.is_additive,
      ins_number: formData.ins_number.trim() || undefined,
      source_evidence: formData.source_evidence.trim() || undefined,
      aliases,
    };

    try {
      setActionLoading("submitting");
      if (editingIngredient) {
        await api.updateAdminIngredient(editingIngredient.id, payload);
      } else {
        await api.createAdminIngredient(payload);
      }
      setModalOpen(false);
      fetchIngredients();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to save ingredient.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleCreateAllergen = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAllergen.name.trim()) {
      alert("Allergen name is required.");
      return;
    }
    try {
      setActionLoading("allergen");
      const created = await api.createAdminAllergen({
        name: newAllergen.name.trim(),
        code: newAllergen.code.trim() || undefined,
        description: newAllergen.description.trim() || undefined,
      });
      setAllergens((prev) => [...prev, created]);
      setNewAllergen({ name: "", code: "", description: "" });
      alert(`Allergen "${created.name}" registered successfully.`);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to create allergen.");
    } finally {
      setActionLoading(null);
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  const getConcernBadge = (level: string) => {
    switch (level) {
      case "high":
        return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-300 text-[10px]">High Concern</Badge>;
      case "moderate":
        return <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-300 text-[10px]">Moderate</Badge>;
      default:
        return <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-300 text-[10px]">Low Concern</Badge>;
    }
  };

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
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">Ingredient Knowledge Base & Allergens</h1>
          <p className="text-slate-500 text-xs mt-0.5">
            Maintain standardized food additive safety profiles, INS numbers, aliases, and source evidence.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => {
              fetchAllergens();
              setAllergenModalOpen(true);
            }}
            className="text-xs h-9 flex items-center gap-1.5 border-slate-300"
          >
            <ShieldAlert className="h-4 w-4 text-amber-600" /> Allergen Registry
          </Button>
          <Button
            onClick={openCreateModal}
            className="bg-amber-600 hover:bg-amber-700 text-white text-xs h-9 flex items-center gap-1.5 shadow-sm"
          >
            <Plus className="h-4 w-4" /> Add Ingredient
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-4">
          <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search ingredients by name, INS number, or alias..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 h-9 text-sm"
              />
            </div>
            <div className="flex items-center gap-2 w-full md:w-auto">
              <select
                value={concernFilter}
                onChange={(e) => {
                  setConcernFilter(e.target.value);
                  setPage(1);
                }}
                className="h-9 px-3 rounded-md border border-input bg-background text-xs text-slate-700"
              >
                <option value="">All Concern Levels</option>
                <option value="low">Low Concern</option>
                <option value="moderate">Moderate Concern</option>
                <option value="high">High Concern</option>
              </select>

              <Input
                placeholder="Filter by category..."
                value={categoryFilter}
                onChange={(e) => {
                  setCategoryFilter(e.target.value);
                  setPage(1);
                }}
                className="h-9 w-36 text-xs"
              />

              <Button type="submit" size="sm" variant="secondary" className="h-9 text-xs">
                Filter
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Ingredients Table */}
      <Card className="border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b text-xs uppercase font-semibold text-slate-500">
              <tr>
                <th className="py-3 px-4">Ingredient</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">INS / E-Number</th>
                <th className="py-3 px-4">Aliases</th>
                <th className="py-3 px-4 text-center">Safety Concern</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-amber-600" />
                    Loading ingredient taxonomy...
                  </td>
                </tr>
              ) : ingredients.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No ingredients found.
                  </td>
                </tr>
              ) : (
                ingredients.map((ingr) => (
                  <tr key={ingr.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">{ingr.name}</div>
                      {ingr.description && (
                        <div className="text-xs text-slate-400 line-clamp-1 max-w-sm">{ingr.description}</div>
                      )}
                    </td>
                    <td className="py-3 px-4 capitalize text-xs">
                      {ingr.category || (ingr.is_additive ? "Food Additive" : "General Ingredient")}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs">{ingr.ins_number || "—"}</td>
                    <td className="py-3 px-4">
                      {ingr.aliases && ingr.aliases.length > 0 ? (
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {ingr.aliases.slice(0, 3).map((alias, i) => (
                            <span key={i} className="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded text-[10px]">
                              {alias}
                            </span>
                          ))}
                          {ingr.aliases.length > 3 && (
                            <span className="text-[10px] text-slate-400">+{ingr.aliases.length - 3} more</span>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-300 text-xs">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">{getConcernBadge(ingr.concern_level)}</td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => openEditModal(ingr)}
                          className="p-1.5 rounded text-blue-600 hover:bg-blue-50"
                          title="Edit ingredient"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(ingr)}
                          disabled={actionLoading === `delete-${ingr.id}`}
                          className="p-1.5 rounded text-red-600 hover:bg-red-50"
                          title="Delete ingredient"
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
            Showing {ingredients.length} of {total} ingredients
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

      {/* Ingredient Create / Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl max-w-xl w-full max-h-[90vh] flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b flex items-center justify-between bg-slate-50">
              <h2 className="text-base font-bold text-slate-900">
                {editingIngredient ? `Edit: ${editingIngredient.name}` : "Register New Ingredient"}
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
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Ingredient Name *</label>
                  <Input
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. Maltodextrin"
                    className="h-8 text-xs"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Category</label>
                  <Input
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    placeholder="e.g. Preservative, Sweetener"
                    className="h-8 text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Safety Concern Level</label>
                  <select
                    value={formData.concern_level}
                    onChange={(e) => setFormData({ ...formData, concern_level: e.target.value })}
                    className="h-8 w-full px-2 rounded-md border border-input bg-background text-xs"
                  >
                    <option value="low">Low (Generally Recognised As Safe)</option>
                    <option value="moderate">Moderate (Consume in Moderation)</option>
                    <option value="high">High (Known Adverse Effects / Strict Limits)</option>
                  </select>
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">INS / E-Number</label>
                  <Input
                    value={formData.ins_number}
                    onChange={(e) => setFormData({ ...formData, ins_number: e.target.value })}
                    placeholder="e.g. INS 150d or E150d"
                    className="h-8 text-xs font-mono"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_additive"
                  checked={formData.is_additive}
                  onChange={(e) => setFormData({ ...formData, is_additive: e.target.checked })}
                  className="rounded border-slate-300 text-amber-600 focus:ring-amber-500 h-4 w-4"
                />
                <label htmlFor="is_additive" className="font-semibold text-slate-800 cursor-pointer">
                  Classify as Food Additive / Preservative / Emulsifier
                </label>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Aliases (comma separated)</label>
                <Input
                  value={formData.aliases_str}
                  onChange={(e) => setFormData({ ...formData, aliases_str: e.target.value })}
                  placeholder="e.g. Corn Syrup Solids, Dextrin, Modified Starch"
                  className="h-8 text-xs"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Description & Health Context</label>
                <textarea
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Explain biological purpose, dietary impact, or potential side effects..."
                  className="w-full p-2 border rounded-md text-xs focus:ring-1 focus:ring-amber-500"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Scientific Source Evidence / Citations</label>
                <textarea
                  rows={2}
                  value={formData.source_evidence}
                  onChange={(e) => setFormData({ ...formData, source_evidence: e.target.value })}
                  placeholder="e.g. FSSAI Compendium 2021, WHO Technical Report, EFSA Panel Review"
                  className="w-full p-2 border rounded-md text-xs focus:ring-1 focus:ring-amber-500"
                />
              </div>

              <div className="pt-4 border-t flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={actionLoading === "submitting"}
                  className="bg-amber-600 hover:bg-amber-700 text-white"
                >
                  {actionLoading === "submitting" ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-1.5" />
                  ) : null}
                  Save Ingredient
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Allergens Registry Modal */}
      {allergenModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl max-w-xl w-full max-h-[90vh] flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b flex items-center justify-between bg-slate-50">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="h-5 w-5 text-amber-600" />
                <h2 className="text-base font-bold text-slate-900">Standard Allergen Registry</h2>
              </div>
              <button
                type="button"
                onClick={() => setAllergenModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-6 text-xs">
              {/* Form to add new allergen */}
              <form onSubmit={handleCreateAllergen} className="p-3 bg-amber-50/50 rounded-lg border border-amber-200 space-y-3">
                <p className="font-bold text-amber-900">Register New Allergen Category</p>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    required
                    placeholder="Allergen Name (e.g. Tree Nuts) *"
                    value={newAllergen.name}
                    onChange={(e) => setNewAllergen({ ...newAllergen, name: e.target.value })}
                    className="h-8 text-xs bg-white"
                  />
                  <Input
                    placeholder="Short Code (e.g. TNUT)"
                    value={newAllergen.code}
                    onChange={(e) => setNewAllergen({ ...newAllergen, code: e.target.value })}
                    className="h-8 text-xs bg-white font-mono"
                  />
                </div>
                <Input
                  placeholder="Optional description / details..."
                  value={newAllergen.description}
                  onChange={(e) => setNewAllergen({ ...newAllergen, description: e.target.value })}
                  className="h-8 text-xs bg-white"
                />
                <Button
                  type="submit"
                  size="sm"
                  disabled={actionLoading === "allergen"}
                  className="bg-amber-600 hover:bg-amber-700 text-white w-full h-8"
                >
                  Add Allergen to Registry
                </Button>
              </form>

              {/* List of current allergens */}
              <div>
                <p className="font-bold text-slate-800 mb-2">Registered Allergen Classes ({allergens.length})</p>
                <div className="divide-y divide-slate-100 border rounded-lg max-h-60 overflow-y-auto">
                  {allergens.map((alg) => (
                    <div key={alg.id} className="p-2.5 flex items-center justify-between hover:bg-slate-50">
                      <div>
                        <span className="font-semibold text-slate-800">{alg.name}</span>
                        {alg.code && <span className="ml-2 font-mono text-[10px] text-slate-400">[{alg.code}]</span>}
                        {alg.description && <p className="text-[11px] text-slate-500">{alg.description}</p>}
                      </div>
                      <Badge variant="outline" className="text-[10px] bg-slate-100 text-slate-600">
                        Active
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="p-4 border-t bg-slate-50 flex justify-end">
              <Button size="sm" variant="outline" onClick={() => setAllergenModalOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
