export const API_BASE = '/api'; // proxied to localhost:8000

export interface Repository {
  id: number;
  name: string;
  url: string;
  default_branch: string;
}

export interface Investigation {
  id: number;
  repository_id: number;
  bug_report: string;
  status: string;
  created_at: string;
  final_patch_id: number | null;
}

export async function fetchRepositories(): Promise<Repository[]> {
  const res = await fetch(`${API_BASE}/repositories/`);
  if (!res.ok) throw new Error('Failed to fetch repositories');
  return res.json();
}

export async function createRepository(name: string, url: string): Promise<Repository> {
  const res = await fetch(`${API_BASE}/repositories/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, url })
  });
  if (!res.ok) throw new Error('Failed to create repository');
  return res.json();
}

export async function fetchInvestigations(): Promise<Investigation[]> {
  const res = await fetch(`${API_BASE}/investigations/`);
  if (!res.ok) throw new Error('Failed to fetch investigations');
  return res.json();
}

// --- Observability (Module 21) ---------------------------------------------

export interface SpanEvent {
  id: number;
  span_id: string;
  parent_span_id: string | null;
  trace_id: string | null;
  kind: string; // 'llm' | 'tool' | 'chain'
  name: string;
  node: string | null;
  status: string; // 'ok' | 'error'
  duration_ms: number | null;
  model: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  cost_usd: number | null;
  tool_name: string | null;
  error: string | null;
  created_at: string;
}

export interface SessionMetrics {
  session_id: number;
  span_count: number;
  llm_calls: number;
  tool_calls: number;
  node_transitions: number;
  errors: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
  total_duration_ms: number;
  llm_duration_ms: number;
}

export interface ObservabilityOverview {
  total_spans: number;
  traced_sessions: number;
  llm_calls: number;
  tool_calls: number;
  errors: number;
  total_tokens: number;
  total_cost_usd: number;
}

export async function fetchTraces(sessionId: string | number): Promise<SpanEvent[]> {
  const res = await fetch(`${API_BASE}/investigations/${sessionId}/traces`);
  if (!res.ok) throw new Error('Failed to fetch traces');
  return res.json();
}

export async function fetchSessionMetrics(sessionId: string | number): Promise<SessionMetrics> {
  const res = await fetch(`${API_BASE}/investigations/${sessionId}/metrics`);
  if (!res.ok) throw new Error('Failed to fetch session metrics');
  return res.json();
}

export async function fetchObservabilityOverview(): Promise<ObservabilityOverview> {
  const res = await fetch(`${API_BASE}/observability/overview`);
  if (!res.ok) throw new Error('Failed to fetch observability overview');
  return res.json();
}
