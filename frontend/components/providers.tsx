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
import { api, clearTokens, getStoredTokens, setApiLocale, storeTokens } from "@/lib/api";
import {
  type Locale,
  makeTranslator,
  readStoredLocale,
  type TranslationKey,
  writeStoredLocale
} from "@/lib/i18n";
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
type LocaleContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
};

const LocaleContext = createContext<LocaleContextValue | null>(null);

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

function LocaleProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => readStoredLocale());

  useEffect(() => {
    setApiLocale(locale);
  }, [locale]);

  const setLocale = useCallback((nextLocale: Locale) => {
    writeStoredLocale(nextLocale);
    setApiLocale(nextLocale);
    setLocaleState(nextLocale);
    void queryClient.invalidateQueries();
  }, []);

  const value = useMemo(
    () => ({ locale, setLocale, t: makeTranslator(locale) }),
    [locale, setLocale],
  );

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useI18n() {
  const context = useContext(LocaleContext);

  if (!context) {
    throw new Error("useI18n must be used inside AppProviders");
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
      <LocaleProvider>
        <SessionProvider>{children}</SessionProvider>
      </LocaleProvider>
    </QueryClientProvider>
  );
}
