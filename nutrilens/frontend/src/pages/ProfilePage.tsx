import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  User,
  Shield,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Plus,
  X,
  Heart,
  AlertTriangle,
  Sparkles,
  Activity,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { apiService } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const profileSchema = z.object({
  full_name: z.string().min(2, "Full name must be at least 2 characters"),
  age: z
    .preprocess(
      (val) => (val === "" || val === undefined || val === null ? undefined : Number(val)),
      z.number().min(1, "Age must be at least 1").max(120, "Age must be less than 120").optional()
    ),
  dietary_preference: z.string(),
});

type ProfileFormData = z.infer<typeof profileSchema>;

const STANDARD_ALLERGIES = [
  "Peanuts",
  "Tree Nuts",
  "Milk / Dairy",
  "Gluten / Wheat",
  "Eggs",
  "Soy",
  "Fish",
  "Crustacean Shellfish",
  "Sesame",
  "Mustard",
  "Sulfites",
];

const STANDARD_RESTRICTIONS = [
  "Low-Sodium",
  "Low-Sugar",
  "Lactose-Free",
  "Gluten-Free",
  "Halal",
  "Kosher",
  "Palm Oil Free",
  "Vegetarian",
  "Vegan",
];

const STANDARD_GOALS = [
  "Weight Loss",
  "Muscle Building",
  "Heart Health",
  "Blood Sugar Management",
  "High Protein",
  "Clean Eating",
  "Low Calorie",
  "Gut Health",
];

const DIETARY_PREFERENCES = [
  "None",
  "Vegetarian",
  "Vegan",
  "Pescatarian",
  "Omnivore",
  "Keto",
  "Low-Carb",
  "Halal",
  "Kosher",
];

const MONITORED_NUTRIENTS = [
  "Sugar",
  "Sodium",
  "Saturated Fat",
  "Trans Fat",
  "Calories",
  "Fibre",
  "Protein",
  "Carbohydrates",
  "Total Fat",
  "Added Sugar",
];

export const ProfilePage: React.FC = () => {
  const { user, updateProfile } = useAuth();
  const [selectedAllergies, setSelectedAllergies] = useState<string[]>([]);
  const [selectedRestrictions, setSelectedRestrictions] = useState<string[]>([]);
  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
  const [customAllergyInput, setCustomAllergyInput] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedMonitoredNutrients, setSelectedMonitoredNutrients] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: user?.full_name || "",
      age: user?.age ?? undefined,
      dietary_preference: user?.profile?.dietary_preference || "None",
    },
  });

  const selectedDiet = watch("dietary_preference");

  // Sync state when user object loads or updates
  useEffect(() => {
    if (user) {
      reset({
        full_name: user.full_name,
        age: user.age ?? undefined,
        dietary_preference: user.profile?.dietary_preference || "None",
      });
      setSelectedAllergies(user.profile?.allergies || []);
      setSelectedRestrictions(user.profile?.dietary_restrictions || []);
      setSelectedGoals(user.profile?.nutrition_goals || []);
      setSelectedMonitoredNutrients((user.profile as any)?.monitored_nutrients || []);
    }
  }, [user, reset]);

  const toggleItem = (
    item: string,
    setList: React.Dispatch<React.SetStateAction<string[]>>
  ) => {
    setList((prev) =>
      prev.includes(item) ? prev.filter((i) => i !== item) : [...prev, item]
    );
  };

  const handleAddCustomAllergy = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = customAllergyInput.trim();
    if (trimmed && !selectedAllergies.includes(trimmed)) {
      setSelectedAllergies((prev) => [...prev, trimmed]);
      setCustomAllergyInput("");
    }
  };

  const removeAllergy = (allergy: string) => {
    setSelectedAllergies((prev) => prev.filter((a) => a !== allergy));
  };

  const onSubmit = async (data: ProfileFormData) => {
    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      await updateProfile({
        full_name: data.full_name,
        age: data.age,
        dietary_preference: data.dietary_preference,
        allergies: selectedAllergies,
        dietary_restrictions: selectedRestrictions,
        nutrition_goals: selectedGoals,
      });
      // Save monitored nutrients via the suitability preferences endpoint
      await apiService.updateDietaryPreferences({
        monitored_nutrients: selectedMonitoredNutrients,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err: any) {
      setSaveError(
        err.response?.data?.detail || "Failed to update profile. Please try again."
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
          My Dietary Profile
        </h1>
        <p className="text-sm text-slate-600 mt-1">
          Customize your nutritional parameters. NutriLens cross-references these preferences with
          every food product scan to flag allergens and assess diet compatibility.
        </p>
      </div>

      {/* Privacy Notice Banner */}
      <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 flex items-start space-x-3 text-emerald-900 text-sm">
        <Shield className="h-5 w-5 text-emerald-600 mt-0.5 flex-shrink-0" />
        <div>
          <span className="font-semibold">Privacy-First Nutritional Intelligence:</span> We do not collect
          unnecessary medical records. Your personal dietary attributes and allergen sensitivities are stored
          securely and used solely to analyze food suitability.
        </div>
      </div>

      {/* Status Alerts */}
      {saveSuccess && (
        <div className="p-4 rounded-xl bg-emerald-100 border border-emerald-300 flex items-center space-x-3 text-emerald-900 text-sm shadow-sm animate-in fade-in">
          <CheckCircle2 className="h-5 w-5 text-emerald-700 flex-shrink-0" />
          <span className="font-medium">Your profile and dietary settings were updated successfully!</span>
        </div>
      )}

      {saveError && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 flex items-center space-x-3 text-red-700 text-sm">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
          <span>{saveError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Account Details Card */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center space-x-2">
              <User className="h-5 w-5 text-emerald-600" />
              <CardTitle className="text-lg">Account Details</CardTitle>
            </div>
            <CardDescription>Basic account and personal identification.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Full Name */}
              <div className="space-y-1.5">
                <Label htmlFor="full_name">Full Name *</Label>
                <Input
                  id="full_name"
                  type="text"
                  {...register("full_name")}
                  className={errors.full_name ? "border-red-500" : ""}
                />
                {errors.full_name && (
                  <p className="text-xs text-red-600">{errors.full_name.message}</p>
                )}
              </div>

              {/* Email (Read-only) */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="email">Email Address</Label>
                  <span className="text-[11px] text-slate-400">Authenticated ID</span>
                </div>
                <Input
                  id="email"
                  type="email"
                  disabled
                  value={user?.email || ""}
                  className="bg-slate-100 text-slate-600 cursor-not-allowed"
                />
              </div>

              {/* Age (Optional) */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="age">Age</Label>
                  <span className="text-xs text-slate-400">Optional</span>
                </div>
                <Input
                  id="age"
                  type="number"
                  placeholder="e.g. 29"
                  {...register("age")}
                  className={errors.age ? "border-red-500" : ""}
                />
                {errors.age && (
                  <p className="text-xs text-red-600">{errors.age.message}</p>
                )}
              </div>

              {/* Account Status Badge */}
              <div className="space-y-1.5">
                <Label>Account Status</Label>
                <div className="h-10 flex items-center">
                  <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-300">
                    <CheckCircle2 className="h-3.5 w-3.5 mr-1 text-emerald-600" /> Active Member
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Dietary Preference Card */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Sparkles className="h-5 w-5 text-emerald-600" />
                <CardTitle className="text-lg">Dietary Preference</CardTitle>
              </div>
              <Badge variant="outline" className="bg-emerald-50 text-emerald-800 border-emerald-200 font-semibold">
                Current: {selectedDiet}
              </Badge>
            </div>
            <CardDescription>Select your general lifestyle eating pattern.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2.5">
              {DIETARY_PREFERENCES.map((diet) => (
                <button
                  key={diet}
                  type="button"
                  onClick={() => setValue("dietary_preference", diet, { shouldDirty: true })}
                  className={`px-3 py-2.5 rounded-lg text-sm font-medium border text-center transition-all ${
                    selectedDiet === diet
                      ? "bg-emerald-600 text-white border-emerald-600 shadow-sm ring-2 ring-emerald-600/20"
                      : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {diet}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Food Allergies Card */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
                <CardTitle className="text-lg">Food Allergies & Critical Sensitivities</CardTitle>
              </div>
              <Badge variant="secondary" className="bg-amber-100 text-amber-900 border-amber-300">
                {selectedAllergies.length} Flagged
              </Badge>
            </div>
            <CardDescription>
              Scanned foods containing or suspected to contain these ingredients will trigger high-priority warnings.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Active Allergies Badges */}
            {selectedAllergies.length > 0 && (
              <div className="p-3 bg-amber-50/70 rounded-lg border border-amber-200">
                <p className="text-xs font-semibold text-amber-900 uppercase tracking-wider mb-2">
                  Active Allergy Safeguards:
                </p>
                <div className="flex flex-wrap gap-2">
                  {selectedAllergies.map((allergy) => (
                    <Badge
                      key={allergy}
                      variant="outline"
                      className="bg-white text-amber-900 border-amber-300 pl-2.5 pr-1 py-1 flex items-center gap-1.5 shadow-xs"
                    >
                      <span>{allergy}</span>
                      <button
                        type="button"
                        onClick={() => removeAllergy(allergy)}
                        className="rounded-full hover:bg-amber-100 p-0.5 text-amber-700"
                        aria-label={`Remove ${allergy}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Toggle Common Allergies */}
            <div className="space-y-1.5">
              <p className="text-xs font-medium text-slate-600">Select Common Allergens:</p>
              <div className="flex flex-wrap gap-2">
                {STANDARD_ALLERGIES.map((allergy) => {
                  const isSelected = selectedAllergies.includes(allergy);
                  return (
                    <button
                      key={allergy}
                      type="button"
                      onClick={() => toggleItem(allergy, setSelectedAllergies)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                        isSelected
                          ? "bg-amber-600 text-white border-amber-600 shadow-xs"
                          : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                      }`}
                    >
                      {allergy}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Add Custom Allergy Input */}
            <div className="pt-2">
              <p className="text-xs font-medium text-slate-600 mb-1.5">Add Custom Allergy or Sensitivity:</p>
              <div className="flex gap-2">
                <Input
                  type="text"
                  placeholder="e.g. Lupin, Celery, Tartrazine..."
                  value={customAllergyInput}
                  onChange={(e) => setCustomAllergyInput(e.target.value)}
                  className="max-w-md"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddCustomAllergy(e);
                    }
                  }}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleAddCustomAllergy}
                  className="border-slate-300"
                >
                  <Plus className="h-4 w-4 mr-1" /> Add
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Dietary Restrictions Card */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Shield className="h-5 w-5 text-indigo-600" />
                <CardTitle className="text-lg">Dietary Restrictions & Guidelines</CardTitle>
              </div>
              <Badge variant="outline" className="text-indigo-700 border-indigo-200 bg-indigo-50">
                {selectedRestrictions.length} Selected
              </Badge>
            </div>
            <CardDescription>Religious, lifestyle, or dietary limits to verify.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {STANDARD_RESTRICTIONS.map((restriction) => {
                const isSelected = selectedRestrictions.includes(restriction);
                return (
                  <button
                    key={restriction}
                    type="button"
                    onClick={() => toggleItem(restriction, setSelectedRestrictions)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                      isSelected
                        ? "bg-indigo-600 text-white border-indigo-600 shadow-xs"
                        : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    {restriction}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Personal Nutrition Goals Card */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Heart className="h-5 w-5 text-rose-600" />
                <CardTitle className="text-lg">Personal Nutrition Goals</CardTitle>
              </div>
              <Badge variant="outline" className="text-rose-700 border-rose-200 bg-rose-50">
                {selectedGoals.length} Selected
              </Badge>
            </div>
            <CardDescription>What outcomes are you aiming to achieve with your food choices?</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {STANDARD_GOALS.map((goal) => {
                const isSelected = selectedGoals.includes(goal);
                return (
                  <button
                    key={goal}
                    type="button"
                    onClick={() => toggleItem(goal, setSelectedGoals)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                      isSelected
                        ? "bg-rose-600 text-white border-rose-600 shadow-xs"
                        : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    {goal}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Monitored Nutrients Card */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-sky-600" />
                <CardTitle className="text-lg">Nutrients to Monitor</CardTitle>
              </div>
              <Badge variant="outline" className="text-sky-700 border-sky-200 bg-sky-50">
                {selectedMonitoredNutrients.length} Selected
              </Badge>
            </div>
            <CardDescription>
              NutriLens will highlight these nutrients on every product analysis page.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {MONITORED_NUTRIENTS.map((nutrient) => {
                const isSelected = selectedMonitoredNutrients.includes(nutrient);
                return (
                  <button
                    key={nutrient}
                    type="button"
                    onClick={() => toggleItem(nutrient, setSelectedMonitoredNutrients)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                      isSelected
                        ? "bg-sky-600 text-white border-sky-600 shadow-xs"
                        : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    {nutrient}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end pt-2 pb-6">
          <Button
            type="submit"
            disabled={isSaving}
            className="bg-emerald-600 hover:bg-emerald-700 text-white px-8 py-2.5 text-base shadow-sm"
          >
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving Changes...
              </>
            ) : (
              <>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Save Profile Preferences
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
};
