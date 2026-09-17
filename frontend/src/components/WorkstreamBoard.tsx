/**
 * Primary Workstream board: React Query owns server state (list +
 * mutations, with cache invalidation), Zustand owns local UI state
 * (filter, flash animation), and `useRealtimeWorkstreams` pushes
 * SignalR/WebSocket events straight into the React Query cache —
 * the exact "React Query for server state, Zustand for client state"
 * split called out in the JD.
 */
import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { wesApi } from "../api/client";
import { useAuth } from "../hooks/useAuth";
import { useRealtimeWorkstreams } from "../hooks/useRealtimeWorkstreams";
import { useWorkstreamUIStore } from "../store/workstreamStore";
import type { Workstream, WorkstreamEvent, WorkstreamStatus } from "../types";

const STATUS_COLORS: Record<WorkstreamStatus, string> = {
  draft: "bg-slate-600",
  in_review: "bg-amber-500",
  approved: "bg-wes-accent",
  blocked: "bg-wes-risk",
  done: "bg-wes-ok",
};

export function WorkstreamBoard() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const { statusFilter, setStatusFilter, flashIds, flash } = useWorkstreamUIStore();

  const { data: workstreams = [], isLoading } = useQuery({
    queryKey: ["workstreams"],
    queryFn: () => wesApi.listWorkstreams(token),
  });

  const createMutation = useMutation({
    mutationFn: (title: string) => wesApi.createWorkstream(title, token),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workstreams"] }),
  });

  const onRealtimeEvent = useCallback(
    (event: WorkstreamEvent) => {
      queryClient.setQueryData<Workstream[]>(["workstreams"], (prev = []) => {
        const others = prev.filter((w) => w.id !== event.workstream.id);
        return [...others, event.workstream];
      });
      flash(event.workstream.id);
    },
    [queryClient, flash]
  );
  const { connected } = useRealtimeWorkstreams(onRealtimeEvent);

  const filtered =
    statusFilter === "all" ? workstreams : workstreams.filter((w) => w.status === statusFilter);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">WES · Workstreams</h1>
        <span className={`text-xs px-2 py-1 rounded ${connected ? "bg-wes-ok/20 text-wes-ok" : "bg-slate-700"}`}>
          {connected ? "● live" : "○ connecting"}
        </span>
      </header>

      <div className="flex gap-2 mb-4 flex-wrap">
        {(["all", "draft", "in_review", "approved", "blocked", "done"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`text-xs px-3 py-1 rounded-full border border-slate-700 ${
              statusFilter === s ? "bg-wes-accent text-white" : "text-slate-300"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      <button
        onClick={() => createMutation.mutate(`New Workstream ${Date.now()}`)}
        className="mb-4 text-sm px-3 py-2 rounded bg-wes-accent hover:opacity-90"
      >
        + New Workstream
      </button>

      {isLoading ? (
        <p className="text-slate-400">Loading…</p>
      ) : (
        <ul className="space-y-2">
          {filtered.map((w) => (
            <li
              key={w.id}
              className={`p-3 rounded bg-wes-panel border border-slate-800 flex items-center justify-between transition ${
                flashIds.has(w.id) ? "ring-2 ring-wes-accent" : ""
              }`}
            >
              <div>
                <p className="font-medium">{w.title}</p>
                <span className={`inline-block text-[10px] px-2 py-0.5 rounded ${STATUS_COLORS[w.status]}`}>
                  {w.status}
                </span>
              </div>
              <span className="text-sm font-mono text-slate-300">{w.risk_score.toFixed(1)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
