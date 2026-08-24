import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, AlertTriangle, Cpu, Wrench, DollarSign, Hash } from 'lucide-react';
import { fetchObservabilityOverview } from '../api/client';
import type { ObservabilityOverview } from '../api/client';
import './Dashboard.css';

export const Dashboard: React.FC = () => {
  const [stats] = useState({
    sessions: 128,
    active: 4,
    resolved: 96,
    critical: 3
  });

  const [overview, setOverview] = useState<ObservabilityOverview | null>(null);

  useEffect(() => {
    fetchObservabilityOverview().then(setOverview).catch(console.error);
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
              <tr>
                <td>api-server</td>
                <td>NullPointerError</td>
                <td><span className="badge badge-success">Resolved</span></td>
              </tr>
              <tr>
                <td>frontend</td>
                <td>Build Failure</td>
                <td><span className="badge badge-warning">Investigating</span></td>
              </tr>
              <tr>
                <td>worker</td>
                <td>Timeout</td>
                <td><span className="badge badge-success">Resolved</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
