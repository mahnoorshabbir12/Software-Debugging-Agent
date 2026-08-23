import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { ThemeToggler } from '../components/ThemeToggler';
import { Activity, GitBranch, Terminal, LayoutDashboard, Settings } from 'lucide-react';
import { useDebugSession } from '../context/DebugSessionContext';
import './AppLayout.css';

export const AppLayout: React.FC = () => {
  const { session, loading, error } = useDebugSession();
  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <Terminal className="icon-primary" />
          <h1 className="brand-title">AutoDebugger</h1>
        </div>
        
        <nav className="sidebar-nav">
          <NavLink to="/" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
            <LayoutDashboard className="icon" />
            <span>Dashboard</span>
          </NavLink>
          <NavLink to="/repositories" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
            <GitBranch className="icon" />
            <span>Repositories</span>
          </NavLink>
          <NavLink to="/investigations" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
            <Activity className="icon" />
            <span>Investigations</span>
          </NavLink>
        </nav>
        
        <div className="sidebar-footer">
          <div className="settings-link">
            <Settings className="icon" />
            <span>Settings</span>
          </div>
          <ThemeToggler />
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="main-workspace">
        {/* Topbar */}
        <header className="topbar">
          <div className="workspace-title">
            {session ? (
              <span className="flex items-center gap-2">
                <span className="font-semibold text-primary">{session.repositoryName || `Repo #${session.repositoryId}`}</span>
                <span className="text-muted">/</span>
                <span className="text-secondary">{session.branch || 'main'}</span>
                {loading && <span className="ml-2 badge badge-warning">Loading...</span>}
              </span>
            ) : (
              'Workspace'
            )}
          </div>
          <div className="status-indicators">
            {error && (
              <div className="status-item error">
                <span className="status-dot"></span>
                Connection Error
              </div>
            )}
            {!session && !error && (
              <div className="status-item muted">
                <span className="status-dot"></span>
                No Active Session
              </div>
            )}
            {session && !error && (
              <div className={`status-item ${session.status === 'running' || session.status === 'starting' ? 'success' : 'muted'}`}>
                <span className="status-dot"></span>
                {session.status === 'starting' ? 'Starting Agent...' :
                 session.status === 'running' ? 'Agent Running' :
                 session.status === 'paused' ? 'Agent Paused' :
                 session.status === 'stopping' ? 'Stopping Agent...' :
                 session.status === 'stopped' ? 'Agent Stopped' :
                 session.status === 'failed' ? 'Investigation Failed' :
                 session.status === 'completed' ? 'Investigation Complete' :
                 'Agent Idle'}
              </div>
            )}
          </div>
        </header>
        
        {/* Page Content */}
        <div className="page-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
