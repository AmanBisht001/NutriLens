import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Sliders,
  Plus,
  CheckCircle2,
  ChevronLeft,
  Loader2,
  Scale,
} from "lucide-react";
import { api } from "@/services/api";
import {
  ScoringRuleVersionItem,
  ScoringRuleVersionCreatePayload,
  ScoringThresholds,
  ScoringWeights,
} from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export const AdminScoringRulesPage: React.FC = () => {
  const [rules, setRules] = useState<ScoringRuleVersionItem[]>([]);
  const [selectedRule, setSelectedRule] = useState<ScoringRuleVersionItem | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState<boolean>(false);

  // New version form state
  const [newVersionForm, setNewVersionForm] = useState<{
    version: string;
    name: string;
    description: string;
    is_active: boolean;
    // Food Thresholds per 100g
    food: ScoringThresholds;
    // Beverage Thresholds per 100ml
    bev: ScoringThresholds;
    // Weights
    weights: ScoringWeights;
  }>({
    version: "",
    name: "",
    description: "",
    is_active: false,
    food: {
      sugar_low: 5.0,
      sugar_moderate: 12.5,
      sugar_high: 22.5,
      sodium_low: 120.0,
      sodium_moderate: 400.0,
      sodium_high: 600.0,
      sat_fat_low: 1.5,
      sat_fat_moderate: 5.0,
      sat_fat_high: 10.0,
      trans_fat_low: 0.1,
      trans_fat_moderate: 0.5,
      trans_fat_high: 1.0,
      fibre_low: 3.0,
      fibre_high: 6.0,
      protein_low: 5.0,
      protein_high: 10.0,
    },
    bev: {
      sugar_low: 2.5,
      sugar_moderate: 5.0,
      sugar_high: 10.0,
      sodium_low: 60.0,
      sodium_moderate: 200.0,
      sodium_high: 300.0,
      sat_fat_low: 0.75,
      sat_fat_moderate: 2.5,
      sat_fat_high: 5.0,
      trans_fat_low: 0.05,
      trans_fat_moderate: 0.25,
      trans_fat_high: 0.5,
      fibre_low: 1.5,
      fibre_high: 3.0,
      protein_low: 2.5,
      protein_high: 5.0,
    },
    weights: {
      sugar_weight: 15.0,
      sodium_weight: 15.0,
      sat_fat_weight: 15.0,
      trans_fat_weight: 15.0,
      fibre_weight: 10.0,
      protein_weight: 10.0,
    },
  });

  const fetchRules = async () => {
    try {
      setLoading(true);
      const data = await api.getAdminScoringRules();
      setRules(data);
      if (data.length > 0) {
        const active = data.find((r) => r.is_active) || data[0];
        setSelectedRule(active);
      }
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to load scoring rules.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleActivate = async (ruleId: string) => {
    try {
      setActionLoading(`activate-${ruleId}`);
      const updated = await api.activateAdminScoringRule(ruleId);
      setRules((prev) =>
        prev.map((r) => ({
          ...r,
          is_active: r.id === updated.id,
        }))
      );
      if (selectedRule?.id === updated.id) {
        setSelectedRule(updated);
      }
      alert(`Scoring rule version "${updated.version}" activated for platform scoring.`);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to activate rule version.");
    } finally {
      setActionLoading(null);
    }
  };

  const openCreateModal = () => {
    // Pre-populate with currently selected rule or default
    if (selectedRule) {
      setNewVersionForm({
        version: `${selectedRule.version}-revised`,
        name: `${selectedRule.name} (Copy)`,
        description: selectedRule.description || "",
        is_active: false,
        food: { ...selectedRule.thresholds_food },
        bev: { ...selectedRule.thresholds_beverage },
        weights: { ...selectedRule.general_weights },
      });
    }
    setModalOpen(true);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newVersionForm.version.trim() || !newVersionForm.name.trim()) {
      alert("Version code and name are required.");
      return;
    }

    // Mathematical sanity checks
    if (
      newVersionForm.food.sugar_low >= newVersionForm.food.sugar_moderate ||
      newVersionForm.food.sugar_moderate >= newVersionForm.food.sugar_high
    ) {
      alert("Food sugar thresholds must satisfy: Low < Moderate < High.");
      return;
    }

    const payload: ScoringRuleVersionCreatePayload = {
      version: newVersionForm.version.trim(),
      name: newVersionForm.name.trim(),
      description: newVersionForm.description.trim() || undefined,
      is_active: newVersionForm.is_active,
      thresholds_food: newVersionForm.food,
      thresholds_beverage: newVersionForm.bev,
      general_weights: newVersionForm.weights,
    };

    try {
      setActionLoading("creating");
      const created = await api.createAdminScoringRule(payload);
      setModalOpen(false);
      await fetchRules();
      setSelectedRule(created);
      alert(`Scoring rule version "${created.version}" created and validated.`);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to create rule version.");
    } finally {
      setActionLoading(null);
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
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">NutriLens Scoring Engine Rules</h1>
          <p className="text-slate-500 text-xs mt-0.5">
            Transparent, category-aware mathematical thresholds and weights. Historic versions are preserved immutably.
          </p>
        </div>
        <Button
          onClick={openCreateModal}
          className="bg-purple-600 hover:bg-purple-700 text-white text-xs h-9 flex items-center gap-1.5 shadow-sm"
        >
          <Plus className="h-4 w-4" /> Create New Version
        </Button>
      </div>

      {/* Main 2-column Layout: Version History on Left, Details on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: List of Versions */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="p-4 border-b bg-slate-50">
            <CardTitle className="text-sm font-bold text-slate-900">Rule Versions ({rules.length})</CardTitle>
            <CardDescription className="text-xs">
              Select a version to inspect its thresholds and weight parameters.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-2 space-y-1.5">
            {loading ? (
              <div className="p-8 text-center text-slate-400">
                <Loader2 className="h-5 w-5 animate-spin mx-auto mb-1 text-purple-600" />
                Loading rule versions...
              </div>
            ) : rules.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500">No versions configured yet.</div>
            ) : (
              rules.map((rule) => {
                const isSelected = selectedRule?.id === rule.id;
                return (
                  <button
                    key={rule.id}
                    onClick={() => setSelectedRule(rule)}
                    className={`w-full text-left p-3 rounded-lg border transition-all text-xs flex flex-col gap-1 ${
                      isSelected
                        ? "border-purple-500 bg-purple-50/50 shadow-sm"
                        : "border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 font-mono">{rule.version}</span>
                      {rule.is_active ? (
                        <Badge className="bg-emerald-600 text-white text-[10px] px-1.5 py-0">Active</Badge>
                      ) : (
                        <Badge variant="outline" className="text-slate-400 text-[10px] px-1.5 py-0">
                          Archived
                        </Badge>
                      )}
                    </div>
                    <span className="text-slate-700 font-medium">{rule.name}</span>
                    {rule.description && (
                      <span className="text-slate-400 text-[11px] line-clamp-1">{rule.description}</span>
                    )}
                  </button>
                );
              })
            )}
          </CardContent>
        </Card>

        {/* Right Column: Selected Rule Inspector */}
        <div className="lg:col-span-2 space-y-4">
          {selectedRule ? (
            <Card className="border-slate-200 shadow-sm">
              <CardHeader className="p-5 border-b bg-slate-50 flex flex-row items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-base font-bold text-slate-900 font-mono">
                      {selectedRule.version}
                    </CardTitle>
                    {selectedRule.is_active ? (
                      <Badge className="bg-emerald-600 text-white text-xs">Active Platform Version</Badge>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleActivate(selectedRule.id)}
                        disabled={actionLoading === `activate-${selectedRule.id}`}
                        className="h-7 text-xs text-emerald-700 border-emerald-300 hover:bg-emerald-50"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Set as Active Default
                      </Button>
                    )}
                  </div>
                  <CardDescription className="text-xs text-slate-600 mt-1">
                    {selectedRule.name} — {selectedRule.description || "No description provided."}
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent className="p-5 space-y-6 text-xs">
                {/* General Weights Grid */}
                <div>
                  <div className="flex items-center space-x-1.5 mb-2 font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                    <Scale className="h-4 w-4 text-purple-600" />
                    <span>General Factor Contribution Weights</span>
                  </div>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                    {selectedRule.general_weights &&
                      Object.entries(selectedRule.general_weights).map(([k, v]) => (
                        <div key={k} className="p-2.5 rounded-lg border bg-slate-50/70 text-center">
                          <span className="text-[10px] text-slate-500 uppercase block truncate">
                            {k.replace("_weight", "")}
                          </span>
                          <span className="text-sm font-bold text-purple-700">{v} pts</span>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Food Thresholds (per 100g) */}
                <div>
                  <p className="font-bold text-slate-800 uppercase tracking-wider text-[11px] mb-2">
                    Standard Food Thresholds (per 100g)
                  </p>
                  <div className="overflow-x-auto border rounded-lg">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 border-b text-[11px] uppercase text-slate-500">
                        <tr>
                          <th className="py-2 px-3">Nutrient</th>
                          <th className="py-2 px-3 text-emerald-700">Low Limit</th>
                          <th className="py-2 px-3 text-amber-700">Moderate Limit</th>
                          <th className="py-2 px-3 text-red-700">High Limit</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        <tr>
                          <td className="py-2 px-3 font-semibold">Sugar (g)</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_food?.sugar_low}g</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_food?.sugar_moderate}g</td>
                          <td className="py-2 px-3">&gt; {selectedRule.thresholds_food?.sugar_high}g</td>
                        </tr>
                        <tr>
                          <td className="py-2 px-3 font-semibold">Sodium (mg)</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_food?.sodium_low}mg</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_food?.sodium_moderate}mg</td>
                          <td className="py-2 px-3">&gt; {selectedRule.thresholds_food?.sodium_high}mg</td>
                        </tr>
                        <tr>
                          <td className="py-2 px-3 font-semibold">Saturated Fat (g)</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_food?.sat_fat_low}g</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_food?.sat_fat_moderate}g</td>
                          <td className="py-2 px-3">&gt; {selectedRule.thresholds_food?.sat_fat_high}g</td>
                        </tr>
                        <tr>
                          <td className="py-2 px-3 font-semibold">Trans Fat (g)</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_food?.trans_fat_low}g</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_food?.trans_fat_moderate}g</td>
                          <td className="py-2 px-3">&gt; {selectedRule.thresholds_food?.trans_fat_high}g</td>
                        </tr>
                        <tr>
                          <td className="py-2 px-3 font-semibold">Dietary Fibre (g)</td>
                          <td className="py-2 px-3">Low &lt; {selectedRule.thresholds_food?.fibre_low}g</td>
                          <td className="py-2 px-3">—</td>
                          <td className="py-2 px-3 text-emerald-700">High ≥ {selectedRule.thresholds_food?.fibre_high}g</td>
                        </tr>
                        <tr>
                          <td className="py-2 px-3 font-semibold">Protein (g)</td>
                          <td className="py-2 px-3">Low &lt; {selectedRule.thresholds_food?.protein_low}g</td>
                          <td className="py-2 px-3">—</td>
                          <td className="py-2 px-3 text-emerald-700">High ≥ {selectedRule.thresholds_food?.protein_high}g</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Beverage Thresholds (per 100ml) */}
                <div>
                  <p className="font-bold text-slate-800 uppercase tracking-wider text-[11px] mb-2">
                    Beverage Thresholds (per 100ml)
                  </p>
                  <div className="overflow-x-auto border rounded-lg">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 border-b text-[11px] uppercase text-slate-500">
                        <tr>
                          <th className="py-2 px-3">Nutrient</th>
                          <th className="py-2 px-3 text-emerald-700">Low Limit</th>
                          <th className="py-2 px-3 text-amber-700">Moderate Limit</th>
                          <th className="py-2 px-3 text-red-700">High Limit</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        <tr>
                          <td className="py-2 px-3 font-semibold">Sugar (g)</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_beverage?.sugar_low}g</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_beverage?.sugar_moderate}g</td>
                          <td className="py-2 px-3">&gt; {selectedRule.thresholds_beverage?.sugar_high}g</td>
                        </tr>
                        <tr>
                          <td className="py-2 px-3 font-semibold">Sodium (mg)</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_beverage?.sodium_low}mg</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_beverage?.sodium_moderate}mg</td>
                          <td className="py-2 px-3">&gt; {selectedRule.thresholds_beverage?.sodium_high}mg</td>
                        </tr>
                        <tr>
                          <td className="py-2 px-3 font-semibold">Saturated Fat (g)</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_beverage?.sat_fat_low}g</td>
                          <td className="py-2 px-3">≤ {selectedRule.thresholds_beverage?.sat_fat_moderate}g</td>
                          <td className="py-2 px-3">&gt; {selectedRule.thresholds_beverage?.sat_fat_high}g</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="p-12 text-center text-slate-400 bg-white rounded-lg border border-dashed">
              Select a version from the left panel to inspect parameters.
            </div>
          )}
        </div>
      </div>

      {/* Modal for Creating New Version */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b flex items-center justify-between bg-slate-50">
              <div className="flex items-center space-x-2">
                <Sliders className="h-5 w-5 text-purple-600" />
                <h2 className="text-base font-bold text-slate-900">Define New Scoring Rule Version</h2>
              </div>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="p-6 overflow-y-auto space-y-4 text-xs">
              <div className="p-3 bg-purple-50 text-purple-900 rounded-lg text-[11px] leading-relaxed">
                <strong>Versioning Notice:</strong> Existing product score histories retain the exact rule version under which they were generated. Creating a new version preserves historic auditability.
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Version String *</label>
                  <Input
                    required
                    value={newVersionForm.version}
                    onChange={(e) => setNewVersionForm({ ...newVersionForm, version: e.target.value })}
                    placeholder="e.g. nutrilens-score-v1.1"
                    className="h-8 text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Rule Name *</label>
                  <Input
                    required
                    value={newVersionForm.name}
                    onChange={(e) => setNewVersionForm({ ...newVersionForm, name: e.target.value })}
                    placeholder="e.g. 2026 Enhanced Sodium Stricter Cutoff"
                    className="h-8 text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Description</label>
                <textarea
                  rows={2}
                  value={newVersionForm.description}
                  onChange={(e) => setNewVersionForm({ ...newVersionForm, description: e.target.value })}
                  placeholder="Rationale for this rule version change..."
                  className="w-full p-2 border rounded-md text-xs focus:ring-1 focus:ring-purple-500"
                />
              </div>

              {/* Food Sugar Thresholds */}
              <div className="pt-2 border-t">
                <p className="font-bold text-slate-800 uppercase tracking-wider text-[11px] mb-2">
                  Food Sugar Thresholds (per 100g)
                </p>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="text-[11px] text-slate-600">Low Limit (g)</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newVersionForm.food.sugar_low}
                      onChange={(e) =>
                        setNewVersionForm({
                          ...newVersionForm,
                          food: { ...newVersionForm.food, sugar_low: Number(e.target.value) },
                        })
                      }
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600">Moderate Limit (g)</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newVersionForm.food.sugar_moderate}
                      onChange={(e) =>
                        setNewVersionForm({
                          ...newVersionForm,
                          food: { ...newVersionForm.food, sugar_moderate: Number(e.target.value) },
                        })
                      }
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600">High Limit (g)</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newVersionForm.food.sugar_high}
                      onChange={(e) =>
                        setNewVersionForm({
                          ...newVersionForm,
                          food: { ...newVersionForm.food, sugar_high: Number(e.target.value) },
                        })
                      }
                      className="h-7 text-xs"
                    />
                  </div>
                </div>
              </div>

              {/* Food Sodium Thresholds */}
              <div className="pt-2 border-t">
                <p className="font-bold text-slate-800 uppercase tracking-wider text-[11px] mb-2">
                  Food Sodium Thresholds (mg per 100g)
                </p>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="text-[11px] text-slate-600">Low Limit (mg)</label>
                    <Input
                      type="number"
                      step="1"
                      value={newVersionForm.food.sodium_low}
                      onChange={(e) =>
                        setNewVersionForm({
                          ...newVersionForm,
                          food: { ...newVersionForm.food, sodium_low: Number(e.target.value) },
                        })
                      }
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600">Moderate Limit (mg)</label>
                    <Input
                      type="number"
                      step="1"
                      value={newVersionForm.food.sodium_moderate}
                      onChange={(e) =>
                        setNewVersionForm({
                          ...newVersionForm,
                          food: { ...newVersionForm.food, sodium_moderate: Number(e.target.value) },
                        })
                      }
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600">High Limit (mg)</label>
                    <Input
                      type="number"
                      step="1"
                      value={newVersionForm.food.sodium_high}
                      onChange={(e) =>
                        setNewVersionForm({
                          ...newVersionForm,
                          food: { ...newVersionForm.food, sodium_high: Number(e.target.value) },
                        })
                      }
                      className="h-7 text-xs"
                    />
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="make_active"
                  checked={newVersionForm.is_active}
                  onChange={(e) => setNewVersionForm({ ...newVersionForm, is_active: e.target.checked })}
                  className="rounded border-slate-300 text-purple-600 focus:ring-purple-500 h-4 w-4"
                />
                <label htmlFor="make_active" className="font-semibold text-slate-800 cursor-pointer">
                  Immediately set this new version as active platform scoring engine
                </label>
              </div>

              <div className="pt-4 border-t flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={actionLoading === "creating"}
                  className="bg-purple-600 hover:bg-purple-700 text-white"
                >
                  {actionLoading === "creating" ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-1.5" />
                  ) : null}
                  Validate & Save Version
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
