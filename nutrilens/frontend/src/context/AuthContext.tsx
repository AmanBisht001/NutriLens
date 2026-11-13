import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import type {
  User,
  RegisterPayload,
  LoginPayload,
  ProfileUpdatePayload,
} from "@/types";
import {
  apiService,
  getStoredToken,
  setStoredToken,
  clearStoredToken,
} from "@/services/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  sessionExpired: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (payload: ProfileUpdatePayload) => Promise<User>;
  refreshUser: () => Promise<void>;
  clearSessionExpired: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [sessionExpired, setSessionExpired] = useState<boolean>(false);

  // Initialize and verify authentication state on app load
  const initAuth = useCallback(async () => {
    const existingToken = getStoredToken();
    if (!existingToken) {
      setUser(null);
      setToken(null);
      setIsLoading(false);
      return;
    }

    try {
      setToken(existingToken);
      const currentUser = await apiService.getMe();
      setUser(currentUser);
    } catch {
      // Token is invalid or expired
      clearStoredToken();
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    initAuth();

    // Listen for 401 interceptor session expiry
    const handleAuthExpired = () => {
      setUser(null);
      setToken(null);
      setSessionExpired(true);
    };

    window.addEventListener("nutrilens:auth_expired", handleAuthExpired);
    return () => {
      window.removeEventListener("nutrilens:auth_expired", handleAuthExpired);
    };
  }, [initAuth]);

  const login = async (payload: LoginPayload): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await apiService.login(payload);
      setStoredToken(response.access_token);
      setToken(response.access_token);
      setUser(response.user);
      setSessionExpired(false);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: RegisterPayload): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await apiService.register(payload);
      setStoredToken(response.access_token);
      setToken(response.access_token);
      setUser(response.user);
      setSessionExpired(false);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    setIsLoading(true);
    try {
      await apiService.logout();
    } finally {
      clearStoredToken();
      setUser(null);
      setToken(null);
      setIsLoading(false);
    }
  };

  const updateProfile = async (payload: ProfileUpdatePayload): Promise<User> => {
    const updatedUser = await apiService.updateProfile(payload);
    setUser(updatedUser);
    return updatedUser;
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const currentUser = await apiService.getMe();
      setUser(currentUser);
    } catch (error) {
      console.error("Failed to refresh user profile", error);
    }
  };

  const clearSessionExpired = () => {
    setSessionExpired(false);
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: Boolean(token && user),
    sessionExpired,
    login,
    register,
    logout,
    updateProfile,
    refreshUser,
    clearSessionExpired,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
