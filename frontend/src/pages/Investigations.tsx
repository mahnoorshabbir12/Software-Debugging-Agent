import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Play, CheckCircle, FileText, Pause, RotateCcw, Square, List as ListIcon, Activity, Loader } from 'lucide-react';
import { useDebugSession } from '../context/DebugSessionContext';
import { fetchInvestigations, fetchTraces, fetchSessionMetrics } from '../api/client';
import type { Investigation, SpanEvent, SessionMetrics } from '../api/client';
import { useNavigate } from 'react-router-dom';
import './Investigations.css';
import { Toast } from '../components/Toast';

const formatCost = (c?: number | null) => (c == null ? '-' : c === 0 ? '$0' : `$${c.toFixed(6)}`);
const formatDuration = (ms?: number | null) => {
  if (ms == null) return '-';
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)}s` : `${Math.round(ms)}ms`;
};

export const Investigations: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { session, loadSession, stop, pause, resume, retry, loading, error } = useDebugSession();
  const [activeTab, setActiveTab] = useState('overview');
  
  // State for the list view
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loadingList, setLoadingList] = useState(false);

  // Observability tab state
  const [traces, setTraces] = useState<SpanEvent[]>([]);
  const [metrics, setMetrics] = useState<SessionMetrics | null>(null);
  // Toast notifications
  const [toastMessage, setToastMessage] = useState<string>('');
  const [toastType, setToastType] = useState<'info' | 'success' | 'error'>('info');

  useEffect(() => {
    if (sessionId) {
      if (!session || session.id !== sessionId) {
        loadSession(sessionId);
      }
    } else {
      // Load all investigations if no specific session is selected
      setLoadingList(true);
      fetchInvestigations()
        .then(setInvestigations)
        .catch(console.error)
        .finally(() => setLoadingList(false));
    }
  }, [sessionId]);

  // Effect to show toast on status changes and auto‑clear after display
  useEffect(() => {
    if (!session) return;
    let message = '';
    let type: 'info' | 'success' | 'error' = 'info';
    switch (session.status) {
      case 'running':
      case 'starting':
        message = 'Investigation started';
        type = 'info';
        break;
      case 'completed':
        message = 'Investigation completed';
        type = 'success';
        break;
      case 'failed':
        message = 'Investigation failed';
        type = 'error';
        break;
      case 'paused':
        message = 'Investigation paused';
        type = 'info';
        break;
      case 'stopped':
        message = 'Investigation stopped';
        type = 'info';
        break;
      default:
        break;
    }
    if (message) {
      setToastMessage(message);
      setToastType(type);
      // Clear toast after 4 seconds (matches Toast auto‑dismiss)
      const clearTimer = setTimeout(() => setToastMessage(''), 4000);
      return () => clearTimeout(clearTimer);
    }
  }, [session?.status]);

  // Load observability traces + metrics when the tab is open; poll while running.
  useEffect(() => {
    if (!sessionId || activeTab !== 'observability') return;
    let cancelled = false;
    const load = () => {
      fetchTraces(sessionId).then(d => { if (!cancelled) setTraces(d); }).catch(console.error);
      fetchSessionMetrics(sessionId).then(d => { if (!cancelled) setMetrics(d); }).catch(console.error);
    };
    load();
    const isRunning = session?.status === 'running' || session?.status === 'starting';
    const interval = isRunning ? window.setInterval(load, 4000) : undefined;
    return () => { cancelled = true; if (interval) window.clearInterval(interval); };
  }, [sessionId, activeTab, session?.status]);

  // Render list view if no sessionId
  if (!sessionId) {
    if (loadingList) return <div className="p-8">Loading sessions...</div>;
    return (
      <div className="investigations-list p-8">
        <h2 className="mb-6 flex items-center gap-2"><ListIcon className="w-5 h-5" /> Debug Sessions</h2>
        {investigations.length === 0 ? (
          <p className="text-muted">No debug sessions found.</p>
        ) : (
          <div className="grid gap-4">
            {investigations.map(inv => (
              <div 
                key={inv.id} 
                className="glass-panel p-4 cursor-pointer hover:border-primary transition-colors"
                onClick={() => navigate(`/investigations/${inv.id}`)}
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-lg">Session #{inv.id}</h3>
                  <span className={`badge ${inv.status === 'failed' ? 'badge-error' : inv.status === 'completed' ? 'badge-success' : 'badge-warning'}`}>
                    {inv.status.toUpperCase()}
                  </span>
                </div>
                <p className="text-secondary text-sm">{inv.bug_report || 'No details provided'}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (loading && !session) {
    return <div className="p-8">Loading session {sessionId}...</div>;
  }

  if (error && !session) {
    return <div className="p-8 text-error">Error loading session: {error}</div>;
  }

  if (!session) {
    return <div className="p-8">No session selected.</div>;
  }

  return (
    <div className="investigation-page">
      {toastMessage && <Toast message={toastMessage} type={toastType} />}
      <header className="page-header flex justify-between items-center">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`badge ${session.status === 'failed' ? 'badge-error' : session.status === 'completed' ? 'badge-success' : 'badge-warning'}`}>
              {session.status.toUpperCase()}
            </span>
            <span className="text-muted text-sm">Session #{session.id}</span>
          </div>
          <h1>{typeof session.error === 'string' ? session.error : session.error?.message || 'Investigating Repository'}</h1>
        </div>
        <div className="flex gap-2">
          {session.status === 'running' || session.status === 'starting' ? (
            <>
              <button className="btn btn-secondary flex items-center gap-2" onClick={pause}>
                <Pause className="w-4 h-4" /> Pause Agent
              </button>
              <button className="btn btn-secondary text-error flex items-center gap-2" onClick={stop}>
                <Square className="w-4 h-4" /> Stop Agent
              </button>
            </>
          ) : session.status === 'paused' ? (
            <>
              <button className="btn btn-primary flex items-center gap-2" onClick={resume}>
                <Play className="w-4 h-4" /> Resume Agent
              </button>
              <button className="btn btn-secondary text-error flex items-center gap-2" onClick={stop}>
                <Square className="w-4 h-4" /> Stop Agent
              </button>
            </>
          ) : (
            <button className="btn btn-primary flex items-center gap-2" onClick={retry}>
              <RotateCcw className="w-4 h-4" /> Retry Investigation
            </button>
          )}
        </div>
      </header>

      <div className="workspace-grid">
        {/* Main Content Area */}
        <div className="main-panel">
          <div className="tabs">
            <button className={`tab ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>Overview</button>
            <button className={`tab ${activeTab === 'evidence' ? 'active' : ''}`} onClick={() => setActiveTab('evidence')}>Evidence</button>
            <button className={`tab ${activeTab === 'patch' ? 'active' : ''}`} onClick={() => setActiveTab('patch')}>Suggested Fix</button>
            <button className={`tab ${activeTab === 'observability' ? 'active' : ''}`} onClick={() => setActiveTab('observability')}>Observability</button>
          </div>

          <div className="tab-content glass-panel p-6">
            {activeTab === 'overview' && (
              <div className="flex-col gap-6">
                {session.error ? (
                  <div>
                    <h3 className="mb-2">Error Details</h3>
                    <div className="code-block error-block">
                      {typeof session.error === 'string' ? session.error : session.error.message}
                      {typeof session.error !== 'string' && session.error.details && `\n${session.error.details}`}
                    </div>
                  </div>
                ) : (
                  <div>
                    <h3 className="mb-2">Goal</h3>
                    <p className="text-secondary">Determine the root cause of the reported issue.</p>
                  </div>
                )}
                
                {session.diagnosis && (
                  <div>
                    <h3 className="mb-2">Current Diagnosis</h3>
                    <p className="text-secondary">{session.diagnosis.rootCause}</p>
                    <div className="mt-2 text-sm text-muted">Confidence: {session.diagnosis.confidence}%</div>
                  </div>
                )}
                
                {!session.diagnosis && session.current_step && (
                  <div>
                    <h3 className="mb-2">Current Step</h3>
                    <p className="text-secondary">{session.current_step.replace('_', ' ')}</p>
                    {session.current_action && <p className="text-muted text-sm mt-1">{session.current_action}</p>}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'evidence' && (
              <div className="flex-col gap-4">
                {session.evidence && session.evidence.length > 0 ? session.evidence.map((ev, i) => (
                  <div key={i} className="evidence-item">
                    <div className="flex items-center gap-2 font-medium">
                      <FileText className="w-4 h-4 text-secondary" />
                      {ev.type}
                    </div>
                    <p className="text-muted text-sm mt-1">{ev.content}</p>
                  </div>
                )) : (
                  <p className="text-muted">No evidence collected yet.</p>
                )}
              </div>
            )}
            
            {activeTab === 'patch' && (
              <div className="flex-col gap-4">
                {session.suggestedFix ? (
                  <>
                    <h3 className="mb-2">Suggested Fix</h3>
                    <div className="code-block">
                      {session.suggestedFix.recommendation}
                    </div>
                  </>
                ) : (
                  <>
                    <p className="text-secondary">Generating patch...</p>
                    <div className="loading-bar"></div>
                  </>
                )}
              </div>
            )}

            {activeTab === 'observability' && (
              <div className="flex-col gap-6">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-primary" />
                  <h3 className="m-0">Agent Telemetry</h3>
                </div>

                <div className="obs-metrics">
                  <div className="obs-metric">
                    <span className="obs-metric-label">LLM Calls</span>
                    <span className="obs-metric-value">{metrics?.llm_calls ?? 0}</span>
                  </div>
                  <div className="obs-metric">
                    <span className="obs-metric-label">Tool Calls</span>
                    <span className="obs-metric-value">{metrics?.tool_calls ?? 0}</span>
                  </div>
                  <div className="obs-metric">
                    <span className="obs-metric-label">Total Tokens</span>
                    <span className="obs-metric-value">{metrics?.total_tokens ?? 0}</span>
                  </div>
                  <div className="obs-metric">
                    <span className="obs-metric-label">Est. Cost</span>
                    <span className="obs-metric-value">{formatCost(metrics?.total_cost_usd)}</span>
                  </div>
                  <div className="obs-metric">
                    <span className="obs-metric-label">Errors</span>
                    <span className={`obs-metric-value ${metrics && metrics.errors > 0 ? 'text-error' : ''}`}>
                      {metrics?.errors ?? 0}
                    </span>
                  </div>
                  <div className="obs-metric">
                    <span className="obs-metric-label">Duration</span>
                    <span className="obs-metric-value">{formatDuration(metrics?.total_duration_ms)}</span>
                  </div>
                </div>

                {traces.length === 0 ? (
                  <p className="text-muted">
                    No spans recorded yet. Spans appear here as the agent makes LLM calls,
                    runs tools, and transitions between graph nodes.
                  </p>
                ) : (
                  <div className="obs-table-container">
                    <table className="obs-table">
                      <thead>
                        <tr>
                          <th>Kind</th>
                          <th>Name</th>
                          <th>Node</th>
                          <th>Status</th>
                          <th>Tokens</th>
                          <th>Cost</th>
                          <th>Duration</th>
                        </tr>
                      </thead>
                      <tbody>
                        {traces.map(s => (
                          <tr key={s.id}>
                            <td><span className={`badge obs-kind obs-kind-${s.kind}`}>{s.kind}</span></td>
                            <td className="obs-mono">{s.tool_name || s.name}</td>
                            <td className="text-muted">{s.node || '-'}</td>
                            <td>
                              {s.status === 'error'
                                ? <span className="badge badge-error">error</span>
                                : <span className="badge badge-success">ok</span>}
                            </td>
                            <td>{s.total_tokens ?? '-'}</td>
                            <td>{formatCost(s.cost_usd)}</td>
                            <td>{formatDuration(s.duration_ms)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Agent Activity Panel */}
        <aside className="agent-panel glass-panel">
          <div className="agent-header">
            <h3>Agent Activity</h3>
            <span className={`badge flex items-center gap-1 ${
              session.status === 'running' || session.status === 'starting' ? 'badge-success' :
              session.status === 'completed' ? 'badge-success' :
              session.status === 'failed' ? 'badge-error' : 'badge-warning'
            }`}>
              <span className="status-dot"></span>
              {session.status === 'running' || session.status === 'starting' ? 'Active' :
               session.status === 'completed' ? 'Completed' :
               session.status === 'failed' ? 'Failed' :
               session.status === 'stopped' ? 'Stopped' :
               session.status === 'paused' ? 'Paused' : session.status}
            </span>
          </div>
          <div className="timeline">
            {session.timeline && session.timeline.map((event, idx) => (
              <div key={idx} className="timeline-item">
                <div className="timeline-icon success"><CheckCircle className="w-4 h-4" /></div>
                <div className="timeline-content">
                  <div className="time">{new Date(event.timestamp).toLocaleTimeString()}</div>
                  <div className="desc">{event.message}</div>
                </div>
              </div>
            ))}
            {(session.status === 'running' || session.status === 'starting') && (
              <div className="timeline-item active">
                <div className="timeline-icon pulse"><Play className="w-3 h-3" /></div>
                <div className="timeline-content">
                  <div className="desc text-primary font-medium">{session.current_action || 'Agent thinking...'}</div>
                </div>
              </div>
            )}
            {(!session.timeline || session.timeline.length === 0) && session.status !== 'running' && session.status !== 'starting' && (
              <p className="text-muted text-sm p-4">No events yet.</p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
};
