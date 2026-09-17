/**
 * Minimal Entra ID (OAuth 2.0 / OIDC) auth hook, standing in for MSAL's
 * `useMsal()` so the showcase runs without a real Entra tenant. Produces
 * an HS256 dev token whose shape matches what `msal-react`'s
 * `acquireTokenSilent` would resolve to, so swapping in real MSAL later
 * only touches this one file.
 */
import { useMemo } from "react";

export interface AuthState {
  token: string;
  subject: string;
}

export function useAuth(): AuthState {
  // In production: const { instance, accounts } = useMsal();
  // const result = await instance.acquireTokenSilent({ scopes: [...] });
  return useMemo(
    () => ({
      token: "dev-token-see-backend-tests-for-signing",
      subject: "shaikat.majumdar@kaufmanrossin.dev",
    }),
    []
  );
}
