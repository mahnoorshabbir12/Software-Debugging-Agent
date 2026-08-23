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
  repositoryId: string;
  repositoryName: string;
  branch: string;
  
  status: AgentStatus;
  
  currentStep: InvestigationStep | null;
  currentAction: string | null;
  
  startedAt: string | null;
  completedAt: string | null;
  
  findings: Finding[];
  evidence: Evidence[];
  timeline: InvestigationEvent[];
  
  error?: DebugError;
  diagnosis?: Diagnosis;
  suggestedFix?: SuggestedFix;
}
