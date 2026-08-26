import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, AlertTriangle, Cpu, Wrench, DollarSign, Hash } from 'lucide-react';
import { fetchObservabilityOverview, fetchInvestigations, fetchRepositories } from '../api/client';
import type { ObservabilityOverview, Investigation, Repository } from '../api/client';
import './Dashboard.css';

interface EnrichedInvestigation extends Investigation {
  repoName: string;
}

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({
    sessions: 0,
    active: 0,
    resolved: 0,
    critical: 0
  });

  const [overview, setOverview] = useState<ObservabilityOverview | null>(null);
  const [recentSessions, setRecentSessions] = useState<EnrichedInvestigation[]>([]);

  useEffect(() => {
    fetchObservabilityOverview().then(setOverview).catch(console.error);
    
    Promise.all([fetchInvestigations(), fetchRepositories()])
      .then(([invs, repos]) => {
        setStats({
          sessions: invs.length,
          active: invs.filter(i => i.status === 'investigating' || i.status === 'starting' || i.status === 'running').length,
          resolved: invs.filter(i => i.status === 'resolved' || i.status === 'completed').length,
          critical: invs.filter(i => i.status === 'failed' || i.status === 'error').length
        });
        
        const repoMap = new Map(repos.map(r => [r.id, r.name]));
        const enriched = invs.map(inv => ({
          ...inv,
          repoName: repoMap.get(inv.repository_id) || `Repo #${inv.repository_id}`
        }));
        
        setRecentSessions(enriched.slice(-5).reverse());
      })
      .catch(console.error);
  }, []);

  const fmtCost = (c?: number) => (c == null ? '$0' : `$${c.toFixed(6)}`);

  return (
    <div className="dashboard-page">
      <header className="page-header">
        <h1>Dashboard</h1>
        <p className="text-secondary">Your debugging overview</p>
      </header>

      <section className="stats-grid">
        <div className="stat-card glass-panel">
          <div className="stat-header">
            <h3 className="text-muted">Sessions</h3>
            <Activity className="icon-small text-primary" />
          </div>
          <div className="stat-value">{stats.sessions}</div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-header">
            <h3 className="text-muted">Active</h3>
            <Activity className="icon-small text-accent" />
          </div>
          <div className="stat-value">{stats.active}</div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-header">
            <h3 className="text-muted">Resolved</h3>
            <CheckCircle className="icon-small text-success" />
          </div>
          <div className="stat-value">{stats.resolved}</div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-header">
            <h3 className="text-muted">Critical</h3>
            <AlertTriangle className="icon-small text-error" />
          </div>
          <div className="stat-value">{stats.critical}</div>
        </div>
      </section>

      <section className="observability-overview">
        <h2>Agent Observability</h2>
        <div className="stats-grid">
          <div className="stat-card glass-panel">
            <div className="stat-header">
              <h3 className="text-muted">LLM Calls</h3>
              <Cpu className="icon-small text-primary" />
            </div>
            <div className="stat-value">{overview?.llm_calls ?? 0}</div>
          </div>
          <div className="stat-card glass-panel">
            <div className="stat-header">
              <h3 className="text-muted">Tool Calls</h3>
              <Wrench className="icon-small text-accent" />
            </div>
            <div className="stat-value">{overview?.tool_calls ?? 0}</div>
          </div>
          <div className="stat-card glass-panel">
            <div className="stat-header">
              <h3 className="text-muted">Total Tokens</h3>
              <Hash className="icon-small text-secondary" />
            </div>
            <div className="stat-value">{overview?.total_tokens ?? 0}</div>
          </div>
          <div className="stat-card glass-panel">
            <div className="stat-header">
              <h3 className="text-muted">Est. Cost</h3>
              <DollarSign className="icon-small text-success" />
            </div>
            <div className="stat-value">{fmtCost(overview?.total_cost_usd)}</div>
          </div>
          <div className="stat-card glass-panel">
            <div className="stat-header">
              <h3 className="text-muted">Agent Errors</h3>
              <AlertTriangle className="icon-small text-error" />
            </div>
            <div className="stat-value">{overview?.errors ?? 0}</div>
          </div>
        </div>
      </section>

      <section className="recent-sessions">
        <h2>Recent Debugging Sessions</h2>
        <div className="table-container glass-panel">
          <table className="data-table">
            <thead>
              <tr>
                <th>Repository</th>
                <th>Issue</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {recentSessions.map(session => (
                <tr key={session.id}>
                  <td>{session.repoName}</td>
                  <td>{session.bug_report.length > 50 ? session.bug_report.substring(0, 50) + '...' : session.bug_report}</td>
                  <td>
                    <span className={`badge ${session.status === 'resolved' ? 'badge-success' : session.status === 'failed' ? 'badge-error' : 'badge-warning'}`}>
                      {session.status.charAt(0).toUpperCase() + session.status.slice(1)}
                    </span>
                  </td>
                </tr>
              ))}
              {recentSessions.length === 0 && (
                <tr>
                  <td colSpan={3} className="text-center text-muted">No recent sessions found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
