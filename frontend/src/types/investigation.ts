export type AgentStatus =
  | "idle"
  | "starting"
  | "running"
  | "paused"
  | "stopping"
  | "stopped"
  | "completed"
  | "failed";

export type InvestigationStep =
  | "initializing"
  | "parsing_error"
  | "inspecting_repository"
  | "inspecting_files"
  | "analyzing_git"
  | "correlating_evidence"
  | "diagnosing"
  | "suggesting_fix";

export interface DebugError {
  message: string;
  code?: string;
  details?: string;
}

export interface Finding {
  title: string;
  severity: "low" | "medium" | "high";
  description?: string;
}

export interface Evidence {
  type: string;
  content: string;
  isSupporting: boolean;
}

export interface InvestigationEvent {
  type: string;
  message: string;
  timestamp: string;
  step?: InvestigationStep;
}

export interface Diagnosis {
  rootCause: string;
  confidence: number;
}

export interface SuggestedFix {
  recommendation: string;
  confidence: number;
  affectedFiles?: number;
}

export interface DebugSession {
  id: string;
  repository_id: number;
  repository_name: string | null;
  branch: string;
  
  status: AgentStatus;
  
  current_step: InvestigationStep | null;
  current_action: string | null;
  
  started_at: string | null;
  completed_at: string | null;
  
  // Frontend-only fields (populated by SSE events / context)
  findings?: Finding[];
  evidence?: Evidence[];
  timeline?: InvestigationEvent[];
  
  error?: string | DebugError;
  diagnosis?: Diagnosis;
  suggestedFix?: SuggestedFix;
}
