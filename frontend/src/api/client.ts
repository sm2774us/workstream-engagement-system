/**
 * Typed fetch wrapper that attaches the Entra ID access token to every
 * request. Token acquisition itself is delegated to `useAuth` (MSAL-style
 * silent-refresh hook), keeping OAuth concerns out of the data layer.
 */
import type { Workstream, WorkstreamStatus } from "../types";

const BASE = "/api/v1";

async function request<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`WES API ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const wesApi = {
  listWorkstreams: (token: string) => request<Workstream[]>("/workstreams", {}, token),

  createWorkstream: (title: string, token: string) =>
    request<Workstream>(`/workstreams?title=${encodeURIComponent(title)}`, { method: "POST" }, token),

  updateStatus: (id: string, status: WorkstreamStatus, token: string) =>
    request<Workstream>(`/workstreams/${id}/status?status=${status}`, { method: "PATCH" }, token),

  search: (q: string, token: string) =>
    request<{ chunk_id: string; text: string }[]>(`/ai/search?q=${encodeURIComponent(q)}`, {}, token),
};
