import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Eye, EyeOff, ShieldCheck, Loader2, AlertCircle, Sparkles, Check } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const registerSchema = z.object({
  full_name: z.string().min(2, "Full name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  age: z
    .preprocess(
      (val) => (val === "" || val === undefined ? undefined : Number(val)),
      z.number().min(1, "Age must be at least 1").max(120, "Age must be less than 120").optional()
    ),
  dietary_preference: z.string().default("None"),
});

type RegisterFormData = z.infer<typeof registerSchema>;

const COMMON_ALLERGIES = [
  "Peanuts",
  "Tree Nuts",
  "Milk / Dairy",
  "Gluten / Wheat",
  "Eggs",
  "Soy",
  "Fish",
  "Shellfish",
  "Sesame",
];

const COMMON_GOALS = [
  "Weight Loss",
  "Muscle Gain",
  "Heart Health",
  "Low Sugar",
  "High Protein",
  "Clean Eating",
];

const DIETARY_OPTIONS = [
  "None",
  "Vegetarian",
  "Vegan",
  "Pescatarian",
  "Keto",
  "Low-Carb",
  "Halal",
];

export const RegisterPage: React.FC = () => {
  const { register: registerAuth } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [selectedAllergies, setSelectedAllergies] = useState<string[]>([]);
  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      dietary_preference: "None",
    },
  });

  const selectedDiet = watch("dietary_preference");

  const toggleAllergy = (allergy: string) => {
    setSelectedAllergies((prev) =>
      prev.includes(allergy) ? prev.filter((a) => a !== allergy) : [...prev, allergy]
    );
  };

  const toggleGoal = (goal: string) => {
    setSelectedGoals((prev) =>
      prev.includes(goal) ? prev.filter((g) => g !== goal) : [...prev, goal]
    );
  };

  const onSubmit = async (data: RegisterFormData) => {
    setIsSubmitting(true);
    setServerError(null);

    try {
      await registerAuth({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        age: data.age,
        dietary_preference: data.dietary_preference,
        allergies: selectedAllergies,
        nutrition_goals: selectedGoals,
        dietary_restrictions: [],
      });
      navigate("/dashboard");
    } catch (err: any) {
      const message =
        err.response?.data?.detail || "Registration failed. Please check your details and try again.";
      setServerError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8 bg-slate-50 flex flex-col justify-center">
      <div className="sm:mx-auto sm:w-full sm:max-w-xl">
        {/* Logo and Tagline */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center space-x-2">
            <div className="h-11 w-11 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-md">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <span className="text-2xl font-bold tracking-tight text-foreground">NutriLens</span>
          </Link>
          <h2 className="mt-4 text-2xl font-extrabold text-slate-900 tracking-tight sm:text-3xl">
            Create your personalized account
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            Smart nutrition scanning tailored to your allergies, preferences, and health goals.
          </p>
        </div>

        <Card className="shadow-lg border-slate-200">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl">Registration</CardTitle>
            <CardDescription>
              Enter your credentials and optional dietary preferences below.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {serverError && (
              <div className="mb-6 p-3.5 rounded-lg bg-red-50 border border-red-200 flex items-start space-x-3 text-red-700 text-sm">
                <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
                <span>{serverError}</span>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              {/* Full Name */}
              <div className="space-y-1.5">
                <Label htmlFor="full_name">Full Name *</Label>
                <Input
                  id="full_name"
                  type="text"
                  placeholder="e.g. Maya Lin"
                  {...register("full_name")}
                  className={errors.full_name ? "border-red-500 focus-visible:ring-red-400" : ""}
                />
                {errors.full_name && (
                  <p className="text-xs text-red-600">{errors.full_name.message}</p>
                )}
              </div>

              {/* Email Address */}
              <div className="space-y-1.5">
                <Label htmlFor="email">Email Address *</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="name@example.com"
                  {...register("email")}
                  className={errors.email ? "border-red-500 focus-visible:ring-red-400" : ""}
                />
                {errors.email && (
                  <p className="text-xs text-red-600">{errors.email.message}</p>
                )}
              </div>

              {/* Password with Visibility Toggle */}
              <div className="space-y-1.5">
                <Label htmlFor="password">Password *</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="At least 6 characters"
                    {...register("password")}
                    className={errors.password ? "border-red-500 pr-10 focus-visible:ring-red-400" : "pr-10"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-slate-600"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {errors.password && (
                  <p className="text-xs text-red-600">{errors.password.message}</p>
                )}
              </div>

              {/* Age (Optional) */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <Label htmlFor="age">Age</Label>
                  <span className="text-xs text-slate-400 font-normal">Optional</span>
                </div>
                <Input
                  id="age"
                  type="number"
                  placeholder="e.g. 28"
                  {...register("age")}
                  className={errors.age ? "border-red-500 focus-visible:ring-red-400" : ""}
                />
                {errors.age && (
                  <p className="text-xs text-red-600">{errors.age.message}</p>
                )}
              </div>

              {/* Dietary Preference Selection */}
              <div className="space-y-2 pt-2 border-t">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-semibold">Primary Dietary Preference</Label>
                  <Badge variant="outline" className="text-emerald-700 bg-emerald-50 border-emerald-200">
                    {selectedDiet}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {DIETARY_OPTIONS.map((option) => (
                    <button
                      key={option}
                      type="button"
                      onClick={() => setValue("dietary_preference", option)}
                      className={`px-3 py-2 text-xs font-medium rounded-lg border transition-all text-center ${
                        selectedDiet === option
                          ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                          : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                      }`}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>

              {/* Food Allergies */}
              <div className="space-y-2 pt-2 border-t">
                <Label className="text-sm font-semibold">Food Allergies to Flag</Label>
                <p className="text-xs text-slate-500">
                  Select ingredients that NutriLens should alert you about during food analysis.
                </p>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {COMMON_ALLERGIES.map((allergy) => {
                    const isSelected = selectedAllergies.includes(allergy);
                    return (
                      <button
                        key={allergy}
                        type="button"
                        onClick={() => toggleAllergy(allergy)}
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                          isSelected
                            ? "bg-amber-100 text-amber-900 border-amber-300 shadow-xs"
                            : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                        }`}
                      >
                        {isSelected && <Check className="h-3 w-3 text-amber-800" />}
                        {allergy}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Nutrition Goals */}
              <div className="space-y-2 pt-2 border-t">
                <Label className="text-sm font-semibold">Personal Nutrition Goals</Label>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {COMMON_GOALS.map((goal) => {
                    const isSelected = selectedGoals.includes(goal);
                    return (
                      <button
                        key={goal}
                        type="button"
                        onClick={() => toggleGoal(goal)}
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                          isSelected
                            ? "bg-emerald-100 text-emerald-900 border-emerald-300 shadow-xs"
                            : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                        }`}
                      >
                        {isSelected && <Check className="h-3 w-3 text-emerald-800" />}
                        {goal}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white mt-6 py-2.5"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Create NutriLens Account
                  </>
                )}
              </Button>
            </form>

            <div className="mt-6 text-center text-sm text-slate-600">
              Already have an account?{" "}
              <Link to="/login" className="font-semibold text-emerald-600 hover:text-emerald-700 underline">
                Log in here
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
