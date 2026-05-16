"use client";

import {
  QueryClient,
  QueryClientProvider,
  onlineManager
} from "@tanstack/react-query";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";
import { api, clearTokens, getStoredTokens, storeTokens } from "@/lib/api";
import type { AuthResponse, User } from "@/lib/types";

type SessionContextValue = {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isBooting: boolean;
  setSession: (auth: AuthResponse) => void;
  setUser: (user: User | null) => void;
  logout: () => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

function SessionProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isBooting, setIsBooting] = useState(true);

  useEffect(() => {
    const stored = getStoredTokens();
    setAccessToken(stored.accessToken);
    setRefreshToken(stored.refreshToken);

    if (!stored.accessToken) {
      setIsBooting(false);
      return;
    }

    api
      .me()
      .then(setUser)
      .catch(() => {
        clearTokens();
        setAccessToken(null);
        setRefreshToken(null);
        setUser(null);
      })
      .finally(() => setIsBooting(false));
  }, []);

  const setSession = useCallback((auth: AuthResponse) => {
    storeTokens(auth.access_token, auth.refresh_token);
    setAccessToken(auth.access_token);
    setRefreshToken(auth.refresh_token);
    setUser(auth.user);
  }, []);

  const logout = useCallback(async () => {
    const tokenToSend = getStoredTokens().refreshToken;

    try {
      if (tokenToSend) {
        await api.logout(tokenToSend);
      }
    } catch {
      // Local logout should still clear the client if the token is expired.
    } finally {
      clearTokens();
      setAccessToken(null);
      setRefreshToken(null);
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({
      accessToken,
      refreshToken,
      user,
      isBooting,
      setSession,
      setUser,
      logout
    }),
    [accessToken, refreshToken, isBooting, logout, refreshToken, setSession, user]
  );

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);

  if (!context) {
    throw new Error("useSession must be used inside AppProviders");
  }

  return context;
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 15_000,
      refetchOnWindowFocus: false
    }
  }
});

if (typeof window !== "undefined") {
  onlineManager.setOnline(window.navigator.onLine);
}

export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <SessionProvider>{children}</SessionProvider>
    </QueryClientProvider>
  );
}
