import React, { useState } from 'react';
import { Activity, CheckCircle, AlertTriangle } from 'lucide-react';
import './Dashboard.css';

export const Dashboard: React.FC = () => {
  const [stats] = useState({
    sessions: 128,
    active: 4,
    resolved: 96,
    critical: 3
  });

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
