import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Play, CheckCircle, FileText, Pause, RotateCcw, Square, List as ListIcon } from 'lucide-react';
import { useDebugSession } from '../context/DebugSessionContext';
import { fetchInvestigations } from '../api/client';
import type { Investigation } from '../api/client';
import { useNavigate } from 'react-router-dom';
import './Investigations.css';

export const Investigations: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { session, loadSession, stop, pause, resume, retry, loading, error } = useDebugSession();
  const [activeTab, setActiveTab] = useState('overview');
  
  // State for the list view
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loadingList, setLoadingList] = useState(false);

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
