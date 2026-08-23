import type { DebugSession } from '../types/investigation';
import { API_BASE } from '../api/client';

export async function createSession(repositoryId: string, branch: string = 'main'): Promise<{ id: string, status: string }> {
  const res = await fetch(`${API_BASE}/investigations/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_id: parseInt(repositoryId, 10), branch })
  });
  if (!res.ok) throw new Error('Failed to create session');
  return res.json();
}

export async function getSession(sessionId: string): Promise<DebugSession> {
  const res = await fetch(`${API_BASE}/investigations/${sessionId}`);
  if (!res.ok) throw new Error('Failed to fetch session');
  return res.json();
}

export async function stopSession(sessionId: string): Promise<DebugSession> {
  const res = await fetch(`${API_BASE}/investigations/${sessionId}/stop`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to stop session');
  return res.json();
}

export async function pauseSession(sessionId: string): Promise<DebugSession> {
  const res = await fetch(`${API_BASE}/investigations/${sessionId}/pause`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to pause session');
  return res.json();
}

export async function resumeSession(sessionId: string): Promise<DebugSession> {
  const res = await fetch(`${API_BASE}/investigations/${sessionId}/resume`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to resume session');
  return res.json();
}

export async function retrySession(sessionId: string): Promise<DebugSession> {
  const res = await fetch(`${API_BASE}/investigations/${sessionId}/retry`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to retry session');
  return res.json();
}
