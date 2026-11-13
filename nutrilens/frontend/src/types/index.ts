export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  environment: string;
  database: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
}

export interface UserProfile {
  id: string;
  user_id: string;
  dietary_preference: string;
  allergies: string[];
  dietary_restrictions: string[];
  nutrition_goals: string[];
  created_at?: string;
  updated_at?: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  age?: number | null;
  role?: string;
  is_admin?: boolean;
  is_active: boolean;
  profile?: UserProfile | null;
  created_at?: string;
  updated_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  age?: number;
  dietary_preference?: string;
  allergies?: string[];
  dietary_restrictions?: string[];
  nutrition_goals?: string[];
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ProfileUpdatePayload {
  full_name?: string;
  age?: number;
  dietary_preference?: string;
  allergies?: string[];
  dietary_restrictions?: string[];
  nutrition_goals?: string[];
}

// ---------------------------------------------------------------------------
// Day 3 Product Catalogue & Ingredient Knowledge Base Types
// ---------------------------------------------------------------------------

export interface Allergen {
  id: string;
  name: string;
  code?: string | null;
  description?: string | null;
}

export interface ProductAllergen {
  allergen: Allergen;
  declaration_type: "declared" | "precautionary" | string;
}

export interface NutritionFacts {
  id: string;
  energy_kcal?: number | null;
  total_fat_g?: number | null;
  saturated_fat_g?: number | null;
  trans_fat_g?: number | null;
  cholesterol_mg?: number | null;
  carbohydrates_g?: number | null;
  total_sugar_g?: number | null;
  added_sugar_g?: number | null;
  dietary_fibre_g?: number | null;
  protein_g?: number | null;
  sodium_mg?: number | null;
  calcium_mg?: number | null;
  iron_mg?: number | null;
  vitamin_c_mg?: number | null;
  serving_unit?: string | null;
  is_illustrative: boolean;
}

export interface IngredientSummary {
  id: string;
  name: string;
  category?: string | null;
  concern_level: "safe" | "moderate" | "high" | string;
  ins_number?: string | null;
  purpose?: string | null;
}

export interface ProductIngredient {
  ingredient: IngredientSummary;
  original_text?: string | null;
  order_index: number;
  is_verified: boolean;
}

export interface ProductSummary {
  id: string;
  name: string;
  brand?: string | null;
  category?: string | null;
  barcode?: string | null;
  serving_size?: number | string | null;
  image_url?: string | null;
  data_source: string;
  is_demo_data: boolean;
  is_verified: boolean;
  nutrition_facts?: NutritionFacts | null;
}

export interface ProductDetail extends ProductSummary {
  description?: string | null;
  serving_unit?: string | null;
  nutrilens_score?: number | null;
  raw_ingredients_text?: string | null;
  label_image_url?: string | null;
  verification_note?: string | null;
  product_ingredients: ProductIngredient[];
  product_allergens: ProductAllergen[];
  nutrition_analysis?: NutritionAnalysis | null;
}

export interface PaginatedProducts {
  items: ProductSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface IngredientResponse {
  id: string;
  name: string;
  normalized_name: string;
  category?: string | null;
  description?: string | null;
  aliases?: string | null;
  purpose?: string | null;
  concern_level: string;
  ins_number?: string | null;
  source_reference?: string | null;
  is_common_allergen: boolean;
  created_at?: string | null;
}

export interface PaginatedIngredients {
  items: IngredientResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CategoryItem {
  name: string;
  product_count: number;
}

export interface CategoryListResponse {
  categories: CategoryItem[];
}

// ---------------------------------------------------------------------------
// Day 4 Food Scanner Types
// ---------------------------------------------------------------------------

export interface ScanImageInfo {
  filename: string;
  saved_filename?: string;
  label_type: "front" | "ingredients" | "nutrition" | "allergens" | "other" | string;
  file_path?: string;
  url: string;
  size_bytes?: number;
}

export interface ExtractedNutritionFacts {
  energy_kcal?: number | null;
  total_fat_g?: number | null;
  saturated_fat_g?: number | null;
  trans_fat_g?: number | null;
  carbohydrates_g?: number | null;
  total_sugar_g?: number | null;
  added_sugar_g?: number | null;
  dietary_fibre_g?: number | null;
  protein_g?: number | null;
  sodium_mg?: number | null;
}

export interface ExtractedProductData {
  product_name?: string | null;
  brand?: string | null;
  category?: string | null;
  serving_size?: string | null;
  raw_ingredients_text?: string | null;
  ingredients: string[];
  nutrition_facts: ExtractedNutritionFacts;
  declared_allergens: string[];
  precautionary_allergens: string[];
  ocr_confidence: number;
  ocr_engine: string;
  uncertainty_flags: string[];
  is_verified: boolean;
}

export interface ScanSession {
  id: string;
  status: "uploaded" | "processing" | "extracted" | "corrected" | "confirmed" | "failed" | string;
  images: ScanImageInfo[];
  raw_ocr_text?: string | null;
  extracted_data?: ExtractedProductData | null;
  corrected_data?: Partial<ExtractedProductData> | null;
  product_id?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ScanCorrectionPayload {
  product_name?: string;
  brand?: string;
  category?: string;
  serving_size?: string;
  raw_ingredients_text?: string;
  ingredients?: string[];
  nutrition_facts?: ExtractedNutritionFacts;
  declared_allergens?: string[];
  precautionary_allergens?: string[];
}

export interface ScanConfirmPayload {
  product_name: string;
  brand?: string;
  category?: string;
  serving_size?: string;
  barcode?: string;
  ingredients: string[];
  raw_ingredients_text?: string;
  nutrition_facts?: ExtractedNutritionFacts;
  declared_allergens: string[];
  precautionary_allergens: string[];
}

export interface ScanConfirmResponse {
  message: string;
  scan_id: string;
  product_id: string;
  product: {
    id: string;
    name: string;
    brand?: string | null;
    category?: string | null;
    serving_size?: string | null;
    data_source: string;
    is_verified: boolean;
  };
}

// ---------------------------------------------------------------------------
// Day 5 Nutrition Scoring & Analysis Types
// ---------------------------------------------------------------------------

export interface FactorItem {
  factor: string;
  impact: string;
  severity?: "critical" | "high" | "moderate" | "low" | string;
  description: string;
}

export interface NutrientEvaluationItem {
  name: string;
  value?: number | null;
  unit: string;
  level: "low" | "moderate" | "high" | "not_declared" | string;
  badge_color: "emerald" | "green" | "amber" | "rose" | "slate" | string;
  description: string;
  thresholds?: { low: number; moderate: number; high: number };
}

export interface ServingSizeInfo {
  raw_text?: string | null;
  quantity?: number | null;
  unit: string;
  standard_reference: string;
}

export interface ScoreBreakdown {
  base_score: number;
  total_penalties: number;
  total_bonuses: number;
  penalties: Record<string, number>;
  bonuses: Record<string, number>;
  category_used: string;
}

export interface NutritionAnalysis {
  status: "complete" | "insufficient_data";
  product_id?: string | null;
  product_name?: string | null;
  score?: number | null;
  grade?: "A" | "B" | "C" | "D" | "E" | null;
  rating_label: string;
  rating_color: "emerald" | "green" | "amber" | "orange" | "rose" | "slate" | string;
  standard_unit: "per_100g" | "per_100ml" | string;
  per_100_values: Record<string, number | null>;
  per_serving_values: Record<string, number | null>;
  serving_size_info: ServingSizeInfo;
  data_completeness_pct: number;
  missing_critical_fields: string[];
  missing_optional_fields: string[];
  issues: Array<{ field: string; severity: string; message: string }>;
  nutrition_summary: string;
  score_explanation: string;
  positive_factors: FactorItem[];
  attention_factors: FactorItem[];
  nutrient_evaluations: Record<string, NutrientEvaluationItem>;
  score_breakdown?: ScoreBreakdown | null;
  scoring_rule_version: string;
  disclaimer: string;
}

// ---------------------------------------------------------------------------
// Day 6 Personalized Dietary Suitability Types
// ---------------------------------------------------------------------------

export interface SuitabilityItem {
  category: "allergen" | "dietary_preference" | "dietary_restriction" | "nutrition_goal" | "safety" | string;
  severity: "conflict" | "caution" | "aligned" | "info" | string;
  title: string;
  detail: string;
  source_ingredient?: string | null;
  is_precautionary?: boolean;
}

export interface EvaluatedPreferences {
  dietary_preference: string;
  allergies: string[];
  dietary_restrictions: string[];
  nutrition_goals: string[];
  monitored_nutrients: string[];
}

export interface PersonalSuitabilityResult {
  status:
    | "Suitable based on available information"
    | "Caution"
    | "Declared restriction conflict"
    | "Insufficient information"
    | string;
  status_label: string;
  badge_color: "emerald" | "amber" | "rose" | "slate" | string;
  is_suitable: boolean;
  product_id: string;
  product_name: string;
  summary_narrative: string;
  evaluated_preferences: EvaluatedPreferences;
  conflicts: SuitabilityItem[];
  cautions: SuitabilityItem[];
  positive_observations: SuitabilityItem[];
  safety_warnings: string[];
  rules_applied: string[];
  engine_version: string;
  disclaimer: string;
}

export interface DietaryPreferences {
  dietary_preference: string;
  allergies: string[];
  dietary_restrictions: string[];
  nutrition_goals: string[];
  monitored_nutrients: string[];
  updated_at?: string;
}


// ---------------------------------------------------------------------------
// Day 7 Product Comparison & Alternative Recommendations Types
// ---------------------------------------------------------------------------

export type ComparisonPriority =
  | "lower_sugar"
  | "lower_sodium"
  | "lower_saturated_fat"
  | "higher_protein"
  | "higher_fibre"
  | "fewer_restriction_conflicts";

export interface PriorityRanking {
  product_id: string;
  product_name: string;
  value?: number | null;
  unit: string;
  rank: number;
  note: string;
}

export interface PriorityEvaluationItem {
  priority: ComparisonPriority | string;
  priority_label: string;
  best_product_id?: string | null;
  best_product_name?: string | null;
  summary: string;
  rankings: PriorityRanking[];
}

export interface ProductComparisonItem {
  product_id: string;
  name: string;
  brand?: string | null;
  category?: string | null;
  serving_size?: string | null;
  label_image_url?: string | null;
  standard_unit: "per_100g" | "per_100ml" | string;
  score?: number | null;
  grade?: "A" | "B" | "C" | "D" | "E" | null;
  rating_label?: string | null;
  rating_color?: "emerald" | "green" | "amber" | "orange" | "rose" | "slate" | string | null;
  data_completeness_pct: number;
  nutrients_per_100: Record<string, number | null>;
  nutrients_per_serving: Record<string, number | null>;
  missing_nutrients: string[];
  ingredients: string[];
  allergens_declared: string[];
  allergens_precautionary: string[];
  suitability_status: string;
  suitability_badge: "emerald" | "amber" | "rose" | "slate" | string;
  suitability_conflicts: string[];
  price?: number | null;
  price_display: string;
}

export interface ComparisonMatrixResponse {
  products: ProductComparisonItem[];
  common_ingredients: string[];
  common_allergens: string[];
  priorities_evaluated: string[];
  priority_evaluations: PriorityEvaluationItem[];
  summary: string;
}

export interface ComparisonRequestPayload {
  product_ids: string[];
  priorities?: string[];
  user_preferences?: Partial<DietaryPreferences>;
}

export interface AlternativeRecommendationItem {
  product_id: string;
  name: string;
  brand?: string | null;
  category?: string | null;
  serving_size?: string | null;
  label_image_url?: string | null;
  score?: number | null;
  grade?: "A" | "B" | "C" | "D" | "E" | null;
  rating_label?: string | null;
  rating_color?: "emerald" | "green" | "amber" | "orange" | "rose" | "slate" | string | null;
  suitability_status: string;
  suitability_badge: "emerald" | "amber" | "rose" | "slate" | string;
  match_score: number;
  reasons: string[];
  nutritional_advantages: string[];
  nutrients_per_100: Record<string, number | null>;
  missing_nutrients: string[];
}

export interface ProductAlternativesResponse {
  target_product_id: string;
  target_product_name: string;
  target_category?: string | null;
  target_score?: number | null;
  applied_priorities: string[];
  total_candidates_evaluated: number;
  alternatives: AlternativeRecommendationItem[];
}

// ===========================================================================
// Day 8: Food Journal & Nutrition Analytics Types
// ===========================================================================

export interface JournalCalculatedNutrients {
  energy_kcal?: number | null;
  total_fat_g?: number | null;
  saturated_fat_g?: number | null;
  trans_fat_g?: number | null;
  cholesterol_mg?: number | null;
  carbohydrates_g?: number | null;
  total_sugar_g?: number | null;
  added_sugar_g?: number | null;
  dietary_fibre_g?: number | null;
  protein_g?: number | null;
  sodium_mg?: number | null;
  calcium_mg?: number | null;
  iron_mg?: number | null;
  vitamin_c_mg?: number | null;
  missing_nutrients: string[];
  scale_factor: number;
}

export interface JournalEntryItem {
  id: string;
  user_id: string;
  product_id: string;
  product_name: string;
  product_brand?: string | null;
  product_category?: string | null;
  product_image_url?: string | null;
  consumed_at: string;
  meal_type: "breakfast" | "lunch" | "dinner" | "snack" | "other" | string;
  quantity: number;
  serving_unit: string;
  serving_size_g?: number | null;
  total_weight_g: number;
  notes?: string | null;
  nutrients: JournalCalculatedNutrients;
  created_at?: string;
  updated_at?: string;
}

export interface JournalEntryCreatePayload {
  product_id: string;
  consumed_at?: string | null;
  meal_type?: string;
  quantity?: number;
  serving_unit?: string;
  serving_size_g?: number | null;
  total_weight_g?: number | null;
  notes?: string | null;
}

export interface JournalEntryUpdatePayload {
  consumed_at?: string | null;
  meal_type?: string;
  quantity?: number;
  serving_unit?: string;
  serving_size_g?: number | null;
  total_weight_g?: number | null;
  notes?: string | null;
}

export interface JournalEntryListResponse {
  items: JournalEntryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface DailyMealGroup {
  meal_type: string;
  label: string;
  entries: JournalEntryItem[];
  total_calories: number;
  total_weight_g: number;
}

export interface NutrientTotalDetail {
  total?: number | null;
  unit: string;
  declared_items: number;
  missing_items: number;
}

export interface GoalProgressItem {
  goal_key: string;
  goal_label: string;
  current_value?: number | null;
  target_benchmark?: number | null;
  unit: string;
  status: "on_track" | "caution" | "exceeded" | "info" | string;
  message: string;
}

export interface DailyJournalSummaryResponse {
  date: string;
  total_entries: number;
  total_weight_g: number;
  meals: Record<string, DailyMealGroup>;
  totals: Record<string, NutrientTotalDetail>;
  goal_progress: GoalProgressItem[];
  disclaimer: string;
}

export interface DailyTrendItem {
  date: string;
  day_name: string;
  entry_count: number;
  calories?: number | null;
  sugar_g?: number | null;
  sodium_mg?: number | null;
  protein_g?: number | null;
  fibre_g?: number | null;
  fat_g?: number | null;
  carbs_g?: number | null;
}

export interface WeeklyAnalyticsResponse {
  start_date: string;
  end_date: string;
  daily_trends: DailyTrendItem[];
  averages: Record<string, number | null>;
  active_days: number;
  total_logged_meals: number;
  disclaimer: string;
}

export interface MonthlyAnalyticsResponse {
  year: number;
  month: number;
  start_date: string;
  end_date: string;
  daily_trends: DailyTrendItem[];
  averages: Record<string, number | null>;
  active_days: number;
  total_logged_meals: number;
  disclaimer: string;
}

export interface FrequentProductItem {
  product_id: string;
  product_name: string;
  product_brand?: string | null;
  product_category?: string | null;
  product_image_url?: string | null;
  log_count: number;
  total_weight_g: number;
  last_consumed_at: string;
}

export interface FrequentProductsResponse {
  items: FrequentProductItem[];
}

// ---------------------------------------------------------------------------
// Day 9 Admin Dashboard & Knowledge Management Types
// ---------------------------------------------------------------------------

export interface AdminDashboardStats {
  total_users: number;
  total_products: number;
  total_ingredients: number;
  total_scans: number;
  verified_products: number;
  unverified_products: number;
  pending_issues: number;
  resolved_issues: number;
  total_issues: number;
  active_scoring_rule_version: string;
  category_breakdown: Record<string, number>;
}

export interface ScoringThresholds {
  sugar_low: number;
  sugar_moderate: number;
  sugar_high: number;
  sodium_low: number;
  sodium_moderate: number;
  sodium_high: number;
  sat_fat_low: number;
  sat_fat_moderate: number;
  sat_fat_high: number;
  trans_fat_low: number;
  trans_fat_moderate: number;
  trans_fat_high: number;
  fibre_low: number;
  fibre_high: number;
  protein_low: number;
  protein_high: number;
}

export interface ScoringWeights {
  sugar_weight: number;
  sodium_weight: number;
  sat_fat_weight: number;
  trans_fat_weight: number;
  fibre_weight: number;
  protein_weight: number;
}

export interface ScoringRuleVersionItem {
  id: string;
  version: string;
  name: string;
  description?: string | null;
  is_active: boolean;
  thresholds_food: ScoringThresholds;
  thresholds_beverage: ScoringThresholds;
  category_weights: Record<string, Record<string, number>>;
  general_weights: ScoringWeights;
  created_at?: string;
  updated_at?: string;
}

export interface ScoringRuleVersionCreatePayload {
  version: string;
  name: string;
  description?: string;
  is_active?: boolean;
  thresholds_food: ScoringThresholds;
  thresholds_beverage: ScoringThresholds;
  category_weights?: Record<string, Record<string, number>>;
  general_weights?: ScoringWeights;
}

export interface ProductIssueItem {
  id: string;
  user_id: string;
  product_id: string;
  issue_type: string;
  description: string;
  proposed_correction?: Record<string, any> | null;
  status: "pending" | "reviewed" | "resolved" | "rejected";
  admin_notes?: string | null;
  resolved_by?: string | null;
  created_at: string;
  updated_at?: string;
  user_email?: string;
  user_name?: string;
  product_name?: string;
  product_brand?: string;
}

export interface ProductIssueCreatePayload {
  issue_type: string;
  description: string;
  proposed_correction?: Record<string, any>;
}

export interface ProductIssueUpdatePayload {
  status: "pending" | "reviewed" | "resolved" | "rejected";
  admin_notes?: string;
}

export interface AdminProductCreatePayload {
  barcode?: string;
  name: string;
  brand?: string;
  category?: string;
  description?: string;
  serving_size?: number;
  serving_unit?: string;
  package_size?: number;
  image_url?: string;
  is_verified?: boolean;
  nutrition_facts?: Partial<NutritionFacts>;
  ingredients?: Array<{
    name: string;
    order_index?: number;
    original_text?: string;
    is_verified?: boolean;
  }>;
  allergens?: Array<{
    allergen_id?: string;
    name?: string;
    declaration_type: "declared" | "precautionary";
  }>;
}

export interface AdminProductUpdatePayload {
  barcode?: string;
  name?: string;
  brand?: string;
  category?: string;
  description?: string;
  serving_size?: number;
  serving_unit?: string;
  package_size?: number;
  image_url?: string;
  is_verified?: boolean;
  nutrition_facts?: Partial<NutritionFacts>;
  ingredients?: Array<{
    name: string;
    order_index?: number;
    original_text?: string;
    is_verified?: boolean;
  }>;
  allergens?: Array<{
    allergen_id?: string;
    name?: string;
    declaration_type: "declared" | "precautionary";
  }>;
}

export interface AdminIngredientItem {
  id: string;
  name: string;
  clean_name: string;
  category?: string | null;
  description?: string | null;
  concern_level: string;
  is_additive: boolean;
  ins_number?: string | null;
  source_evidence?: string | null;
  aliases: string[];
  created_at?: string;
  updated_at?: string;
}

export interface AdminIngredientCreatePayload {
  name: string;
  category?: string;
  description?: string;
  concern_level?: string;
  is_additive?: boolean;
  ins_number?: string;
  source_evidence?: string;
  aliases?: string[];
}

export interface AdminIngredientUpdatePayload {
  name?: string;
  category?: string;
  description?: string;
  concern_level?: string;
  is_additive?: boolean;
  ins_number?: string;
  source_evidence?: string;
  aliases?: string[];
}

