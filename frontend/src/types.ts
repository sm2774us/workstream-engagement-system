/** Domain types mirroring backend/app/models/workstream.py 1:1. */
export type WorkstreamStatus = "draft" | "in_review" | "approved" | "blocked" | "done";

export interface Workstream {
  id: string;
  title: string;
  status: WorkstreamStatus;
  risk_score: number;
  assignee: string | null;
  updated_at: string;
}

export interface WorkstreamEvent {
  event_type: string;
  workstream: Workstream;
  actor: string;
  emitted_at: string;
}
