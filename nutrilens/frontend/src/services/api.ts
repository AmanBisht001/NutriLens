import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import type {
  HealthStatus,
  User,
  AuthResponse,
  RegisterPayload,
  LoginPayload,
  ProfileUpdatePayload,
  ProductDetail,
  PaginatedProducts,
  CategoryListResponse,
  PaginatedIngredients,
  IngredientResponse,
  ScanSession,
  ScanCorrectionPayload,
  ScanConfirmPayload,
  ScanConfirmResponse,
  NutritionAnalysis,
  AdminDashboardStats,
  AdminProductCreatePayload,
  AdminProductUpdatePayload,
  AdminIngredientItem,
  AdminIngredientCreatePayload,
  AdminIngredientUpdatePayload,
  ScoringRuleVersionItem,
  ScoringRuleVersionCreatePayload,
  ProductIssueItem,
  ProductIssueCreatePayload,
  ProductIssueUpdatePayload,
  Allergen,
} from "@/types";

const TOKEN_KEY = "nutrilens_auth_token";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const getStoredToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

export const setStoredToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

export const clearStoredToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

// Request interceptor: attach Authorization Bearer token if present
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getStoredToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle expired/invalid tokens (401 Unauthorized)
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear stored token on 401 to prevent repeated invalid calls
      const hadToken = Boolean(getStoredToken());
      clearStoredToken();

      // Dispatch custom event for expired sessions so AuthContext handles state reset
      if (hadToken && typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("nutrilens:auth_expired"));
      }
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  checkHealth: async (): Promise<HealthStatus> => {
    const response = await apiClient.get<HealthStatus>("/api/health");
    return response.data;
  },

  register: async (payload: RegisterPayload): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/api/auth/register", payload);
    return response.data;
  },

  login: async (payload: LoginPayload): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/api/auth/login", payload);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>("/api/auth/me");
    return response.data;
  },

  updateProfile: async (payload: ProfileUpdatePayload): Promise<User> => {
    const response = await apiClient.put<User>("/api/auth/profile", payload);
    return response.data;
  },

  logout: async (): Promise<void> => {
    try {
      await apiClient.post("/api/auth/logout");
    } catch {
      // Even if network fails during logout, local session will be wiped
    } finally {
      clearStoredToken();
    }
  },

  // -------------------------------------------------------------------------
  // Day 3 Product Catalogue & Ingredient Knowledge Base API
  // -------------------------------------------------------------------------

  getProducts: async (params?: {
    search?: string;
    category?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedProducts> => {
    const response = await apiClient.get<PaginatedProducts>("/api/products", { params });
    return response.data;
  },

  getProduct: async (id: string): Promise<ProductDetail> => {
    const response = await apiClient.get<ProductDetail>(`/api/products/${id}`);
    return response.data;
  },

  getCategories: async (): Promise<CategoryListResponse> => {
    const response = await apiClient.get<CategoryListResponse>("/api/categories");
    return response.data;
  },

  getIngredients: async (params?: {
    search?: string;
    category?: string;
    concern_level?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedIngredients> => {
    const response = await apiClient.get<PaginatedIngredients>("/api/ingredients", { params });
    return response.data;
  },

  getIngredient: async (id: string): Promise<IngredientResponse> => {
    const response = await apiClient.get<IngredientResponse>(`/api/ingredients/${id}`);
    return response.data;
  },

  // -------------------------------------------------------------------------
  // Day 4 Food Scanner API
  // -------------------------------------------------------------------------
  scanFoodImages: async (files: File[], labelTypes: string[]): Promise<ScanSession> => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });
    labelTypes.forEach((type) => {
      formData.append("label_types", type);
    });

    const response = await apiClient.post<ScanSession>("/api/products/scan", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      timeout: 30000,
    });
    return response.data;
  },

  getScanSession: async (id: string): Promise<ScanSession> => {
    const response = await apiClient.get<ScanSession>(`/api/scans/${id}`);
    return response.data;
  },

  updateScanCorrection: async (
    id: string,
    data: ScanCorrectionPayload
  ): Promise<ScanSession> => {
    const response = await apiClient.put<ScanSession>(`/api/scans/${id}/correction`, data);
    return response.data;
  },

  confirmScan: async (
    id: string,
    data: ScanConfirmPayload
  ): Promise<ScanConfirmResponse> => {
    const response = await apiClient.post<ScanConfirmResponse>(`/api/scans/${id}/confirm`, data);
    return response.data;
  },

  // -------------------------------------------------------------------------
  // Day 5 Nutrition Analysis & Scoring API
  // -------------------------------------------------------------------------
  getProductAnalysis: async (productId: string): Promise<NutritionAnalysis> => {
    const response = await apiClient.get<NutritionAnalysis>(`/api/products/${productId}/analysis`);
    return response.data;
  },

  calculateCustomScore: async (payload: {
    nutrients: Record<string, number | null>;
    category?: string;
    serving_size?: string;
  }): Promise<NutritionAnalysis> => {
    const response = await apiClient.post<NutritionAnalysis>("/api/analysis/score", payload);
    return response.data;
  },

  // -------------------------------------------------------------------------
  // Day 6 Personalized Dietary Suitability API
  // -------------------------------------------------------------------------
  checkProductSuitability: async (
    productId: string,
    preferences?: Partial<import("@/types").DietaryPreferences>
  ): Promise<import("@/types").PersonalSuitabilityResult> => {
    const response = await apiClient.post<import("@/types").PersonalSuitabilityResult>(
      `/api/products/${productId}/suitability`,
      preferences ?? {}
    );
    return response.data;
  },

  getDietaryPreferences: async (): Promise<import("@/types").DietaryPreferences> => {
    const response = await apiClient.get<import("@/types").DietaryPreferences>(
      "/api/profile/dietary-preferences"
    );
    return response.data;
  },

  updateDietaryPreferences: async (
    data: Partial<import("@/types").DietaryPreferences>
  ): Promise<import("@/types").DietaryPreferences> => {
    const response = await apiClient.put<import("@/types").DietaryPreferences>(
      "/api/profile/dietary-preferences",
      data
    );
    return response.data;
  },

  // -------------------------------------------------------------------------
  // Day 7 Product Comparison & Alternative Recommendations API
  // -------------------------------------------------------------------------
  compareProducts: async (
    productIds: string[],
    priorities?: string[],
    userPreferences?: Partial<import("@/types").DietaryPreferences>
  ): Promise<import("@/types").ComparisonMatrixResponse> => {
    const response = await apiClient.post<import("@/types").ComparisonMatrixResponse>(
      "/api/products/compare",
      {
        product_ids: productIds,
        priorities: priorities ?? [],
        user_preferences: userPreferences,
      }
    );
    return response.data;
  },

  getProductAlternatives: async (
    productId: string,
    priorities?: string[],
    limit: number = 5
  ): Promise<import("@/types").ProductAlternativesResponse> => {
    const params: Record<string, any> = { limit };
    if (priorities && priorities.length > 0) {
      params.priorities = priorities.join(",");
    }
    const response = await apiClient.get<import("@/types").ProductAlternativesResponse>(
      `/api/products/${productId}/alternatives`,
      { params }
    );
    return response.data;
  },

  // -------------------------------------------------------------------------
  // Day 8 Food Journal & Nutrition Analytics API
  // -------------------------------------------------------------------------
  createJournalEntry: async (
    payload: import("@/types").JournalEntryCreatePayload
  ): Promise<import("@/types").JournalEntryItem> => {
    const response = await apiClient.post<import("@/types").JournalEntryItem>("/api/journal", payload);
    return response.data;
  },

  getJournalEntries: async (params?: {
    date?: string;
    start_date?: string;
    end_date?: string;
    meal_type?: string;
    page?: number;
    page_size?: number;
  }): Promise<import("@/types").JournalEntryListResponse> => {
    const response = await apiClient.get<import("@/types").JournalEntryListResponse>("/api/journal", {
      params,
    });
    return response.data;
  },

  getJournalEntry: async (entryId: string): Promise<import("@/types").JournalEntryItem> => {
    const response = await apiClient.get<import("@/types").JournalEntryItem>(`/api/journal/${entryId}`);
    return response.data;
  },

  updateJournalEntry: async (
    entryId: string,
    payload: import("@/types").JournalEntryUpdatePayload
  ): Promise<import("@/types").JournalEntryItem> => {
    const response = await apiClient.put<import("@/types").JournalEntryItem>(`/api/journal/${entryId}`, payload);
    return response.data;
  },

  deleteJournalEntry: async (entryId: string): Promise<{ message: string; id: string }> => {
    const response = await apiClient.delete<{ message: string; id: string }>(`/api/journal/${entryId}`);
    return response.data;
  },

  getDailyJournalSummary: async (date?: string): Promise<import("@/types").DailyJournalSummaryResponse> => {
    const response = await apiClient.get<import("@/types").DailyJournalSummaryResponse>(
      "/api/journal/summary/daily",
      {
        params: date ? { date } : undefined,
      }
    );
    return response.data;
  },

  getWeeklyAnalytics: async (endDate?: string): Promise<import("@/types").WeeklyAnalyticsResponse> => {
    const response = await apiClient.get<import("@/types").WeeklyAnalyticsResponse>(
      "/api/journal/analytics/weekly",
      {
        params: endDate ? { end_date: endDate } : undefined,
      }
    );
    return response.data;
  },

  getMonthlyAnalytics: async (
    year?: number,
    month?: number
  ): Promise<import("@/types").MonthlyAnalyticsResponse> => {
    const response = await apiClient.get<import("@/types").MonthlyAnalyticsResponse>(
      "/api/journal/analytics/monthly",
      {
        params: { year, month },
      }
    );
    return response.data;
  },

  getFrequentProducts: async (limit: number = 10): Promise<import("@/types").FrequentProductsResponse> => {
    const response = await apiClient.get<import("@/types").FrequentProductsResponse>(
      "/api/journal/analytics/frequent",
      {
        params: { limit },
      }
    );
    return response.data;
  },

  // --- User Report Issue ---
  reportProductIssue: async (
    productId: string,
    payload: ProductIssueCreatePayload
  ): Promise<ProductIssueItem> => {
    const response = await apiClient.post<ProductIssueItem>(`/api/products/${productId}/report-issue`, payload);
    return response.data;
  },

  // --- Day 9 Admin APIs ---
  getAdminStats: async (): Promise<AdminDashboardStats> => {
    const response = await apiClient.get<AdminDashboardStats>("/api/admin/dashboard/stats");
    return response.data;
  },

  // Admin Products
  getAdminProducts: async (params?: {
    search?: string;
    category?: string;
    is_verified?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<{ items: ProductDetail[]; total: number; page: number; page_size: number }> => {
    const response = await apiClient.get<{ items: ProductDetail[]; total: number; page: number; page_size: number }>(
      "/api/admin/products",
      { params }
    );
    return response.data;
  },

  createAdminProduct: async (payload: AdminProductCreatePayload): Promise<ProductDetail> => {
    const response = await apiClient.post<ProductDetail>("/api/admin/products", payload);
    return response.data;
  },

  updateAdminProduct: async (productId: string, payload: AdminProductUpdatePayload): Promise<ProductDetail> => {
    const response = await apiClient.put<ProductDetail>(`/api/admin/products/${productId}`, payload);
    return response.data;
  },

  verifyAdminProduct: async (productId: string, is_verified: boolean = true): Promise<ProductDetail> => {
    const response = await apiClient.patch<ProductDetail>(`/api/admin/products/${productId}/verify`, { is_verified });
    return response.data;
  },

  deleteAdminProduct: async (productId: string): Promise<{ message: string; id: string }> => {
    const response = await apiClient.delete<{ message: string; id: string }>(`/api/admin/products/${productId}`);
    return response.data;
  },

  // Admin Ingredients
  getAdminIngredients: async (params?: {
    search?: string;
    category?: string;
    concern_level?: string;
    page?: number;
    page_size?: number;
  }): Promise<{ items: AdminIngredientItem[]; total: number; page: number; page_size: number }> => {
    const response = await apiClient.get<{ items: AdminIngredientItem[]; total: number; page: number; page_size: number }>(
      "/api/admin/ingredients",
      { params }
    );
    return response.data;
  },

  createAdminIngredient: async (payload: AdminIngredientCreatePayload): Promise<AdminIngredientItem> => {
    const response = await apiClient.post<AdminIngredientItem>("/api/admin/ingredients", payload);
    return response.data;
  },

  updateAdminIngredient: async (
    ingredientId: string,
    payload: AdminIngredientUpdatePayload
  ): Promise<AdminIngredientItem> => {
    const response = await apiClient.put<AdminIngredientItem>(`/api/admin/ingredients/${ingredientId}`, payload);
    return response.data;
  },

  deleteAdminIngredient: async (ingredientId: string): Promise<{ message: string; id: string }> => {
    const response = await apiClient.delete<{ message: string; id: string }>(`/api/admin/ingredients/${ingredientId}`);
    return response.data;
  },

  // Admin Allergens
  getAdminAllergens: async (): Promise<Allergen[]> => {
    const response = await apiClient.get<Allergen[]>("/api/admin/allergens");
    return response.data;
  },

  createAdminAllergen: async (payload: { name: string; code?: string; description?: string }): Promise<Allergen> => {
    const response = await apiClient.post<Allergen>("/api/admin/allergens", payload);
    return response.data;
  },

  // Admin Scoring Rules
  getAdminScoringRules: async (): Promise<ScoringRuleVersionItem[]> => {
    const response = await apiClient.get<ScoringRuleVersionItem[]>("/api/admin/scoring-rules");
    return response.data;
  },

  getAdminScoringRule: async (versionOrId: string): Promise<ScoringRuleVersionItem> => {
    const response = await apiClient.get<ScoringRuleVersionItem>(`/api/admin/scoring-rules/${versionOrId}`);
    return response.data;
  },

  createAdminScoringRule: async (payload: ScoringRuleVersionCreatePayload): Promise<ScoringRuleVersionItem> => {
    const response = await apiClient.post<ScoringRuleVersionItem>("/api/admin/scoring-rules", payload);
    return response.data;
  },

  activateAdminScoringRule: async (id: string): Promise<ScoringRuleVersionItem> => {
    const response = await apiClient.put<ScoringRuleVersionItem>(`/api/admin/scoring-rules/${id}/activate`);
    return response.data;
  },

  // Admin Issues
  getAdminIssues: async (status?: string): Promise<ProductIssueItem[]> => {
    const response = await apiClient.get<ProductIssueItem[]>("/api/admin/issues", {
      params: status ? { status } : undefined,
    });
    return response.data;
  },

  updateAdminIssue: async (issueId: string, payload: ProductIssueUpdatePayload): Promise<ProductIssueItem> => {
    const response = await apiClient.put<ProductIssueItem>(`/api/admin/issues/${issueId}`, payload);
    return response.data;
  },
};

export const api = apiService;
