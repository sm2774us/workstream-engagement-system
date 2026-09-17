/**
 * Zustand client-state store for Workstreams (JD: "Zustand for client
 * state"). Server-fetched data itself is owned by React Query (see
 * `hooks` usage in App.tsx); this store only holds UI-local state
 * (selected filter, optimistic risk-score flash) that doesn't belong
 * in the server cache — the deliberate React Query/Zustand split the
 * JD's migration-off-Redux effort is aiming for.
 */
import { create } from "zustand";
import type { WorkstreamStatus } from "../types";

interface WorkstreamUIState {
  statusFilter: WorkstreamStatus | "all";
  flashIds: Set<string>;
  setStatusFilter: (status: WorkstreamStatus | "all") => void;
  flash: (id: string) => void;
}

export const useWorkstreamUIStore = create<WorkstreamUIState>((set) => ({
  statusFilter: "all",
  flashIds: new Set(),
  setStatusFilter: (status) => set({ statusFilter: status }),
  flash: (id) =>
    set((state) => {
      const next = new Set(state.flashIds);
      next.add(id);
      setTimeout(() => {
        useWorkstreamUIStore.setState((s) => {
          const cleared = new Set(s.flashIds);
          cleared.delete(id);
          return { flashIds: cleared };
        });
      }, 1200);
      return { flashIds: next };
    }),
}));
