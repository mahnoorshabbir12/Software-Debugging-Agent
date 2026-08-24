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
