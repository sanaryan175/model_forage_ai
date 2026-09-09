"use client";

import { createContext, useContext, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient, clearToken, getToken, setToken as persistToken } from "@/lib/api-client";
import type { User } from "@/types/api";

interface AuthContextValue {
  user: User | undefined;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Lazy-initialized so a hard page load reads the token on the very first render
  // instead of one render late via an effect, which would otherwise cause AuthGuard
  // to briefly see "no token" and redirect to /login even when one exists.
  const [hasToken, setHasToken] = useState(() => Boolean(getToken()));
  const queryClient = useQueryClient();

  const { data: user, isLoading } = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const { data } = await apiClient.get<User>("/api/auth/me");
      return data;
    },
    enabled: hasToken,
    retry: false,
  });

  const login = (token: string) => {
    persistToken(token);
    setHasToken(true);
  };

  const logout = () => {
    clearToken();
    setHasToken(false);
    queryClient.clear();
  };

  return (
    <AuthContext.Provider
      value={{ user, isLoading: hasToken && isLoading, isAuthenticated: Boolean(user), login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
