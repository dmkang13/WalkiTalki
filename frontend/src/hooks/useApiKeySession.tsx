import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../api/client";

type ApiKeyContextValue = {
  hasApiKey: boolean;
  isChecking: boolean;
  isConnecting: boolean;
  error: string;
  connect: (apiKey: string) => Promise<boolean>;
  disconnect: () => Promise<void>;
  refresh: () => Promise<void>;
};

const ApiKeyContext = createContext<ApiKeyContextValue | undefined>(undefined);

export function ApiKeyProvider({ children }: { children: ReactNode }) {
  const [hasApiKey, setHasApiKey] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setIsChecking(true);
    setError("");
    try {
      const status = await api.getApiKeyStatus();
      setHasApiKey(status.hasApiKey);
    } catch (caught) {
      setHasApiKey(false);
      setError(caught instanceof Error ? caught.message : "Could not check API key status.");
    } finally {
      setIsChecking(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const connect = useCallback(async (apiKey: string) => {
    setIsConnecting(true);
    setError("");
    try {
      const status = await api.validateApiKey(apiKey);
      setHasApiKey(status.hasApiKey);
      return status.hasApiKey;
    } catch (caught) {
      setHasApiKey(false);
      setError(caught instanceof Error ? caught.message : "Could not connect API key.");
      return false;
    } finally {
      setIsConnecting(false);
    }
  }, []);

  const disconnect = useCallback(async () => {
    setError("");
    const status = await api.clearApiKey();
    setHasApiKey(status.hasApiKey);
  }, []);

  const value = useMemo(
    () => ({ hasApiKey, isChecking, isConnecting, error, connect, disconnect, refresh }),
    [connect, disconnect, error, hasApiKey, isChecking, isConnecting, refresh]
  );

  return <ApiKeyContext.Provider value={value}>{children}</ApiKeyContext.Provider>;
}

export function useApiKeySession() {
  const value = useContext(ApiKeyContext);
  if (!value) {
    throw new Error("useApiKeySession must be used inside ApiKeyProvider");
  }
  return value;
}
