import React, { useEffect, useState } from 'react';
import { fetchRepositories, createRepository } from '../api/client';
import type { Repository } from '../api/client';
import { createSession } from '../services/investigationApi';
import { useNavigate } from 'react-router-dom';
import { Plus, Book, CheckCircle, Loader } from 'lucide-react';
import './Repositories.css';

export const Repositories: React.FC = () => {
  const navigate = useNavigate();
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newRepo, setNewRepo] = useState({ name: '', url: '' });
  
  // Connection Progress State
  const [connectionStep, setConnectionStep] = useState<'idle' | 'validating' | 'connecting' | 'creating_session' | 'completed' | 'failed'>('idle');
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [investigatingId, setInvestigatingId] = useState<number | null>(null);

  useEffect(() => {
    fetchRepositories()
      .then(setRepos)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setConnectionError(null);
    setConnectionStep('validating');
    
    try {
      // Step 1: Validate (Mocked by frontend required fields for now)
      if (!newRepo.name || !newRepo.url) throw new Error("Missing required fields");
      
      // Step 2: Connect Repository
      setConnectionStep('connecting');
      const repo = await createRepository(newRepo.name, newRepo.url);
      setRepos([...repos, repo]);
      
      // Step 3: Create Debug Session
      setConnectionStep('creating_session');
      const session = await createSession(repo.id.toString());
      
      // Step 4: Complete
      setConnectionStep('completed');
      
      // Navigate to the live session UI
      navigate(`/investigations/${session.id}`);
      
    } catch (err: any) {
      console.error(err);
      setConnectionError(err.message || 'An error occurred during connection');
      setConnectionStep('failed');
    }
  };

  const handleInvestigate = async (repoId: number) => {
    setInvestigatingId(repoId);
    try {
      const session = await createSession(repoId.toString());
      navigate(`/investigations/${session.id}`);
    } catch (err: any) {
      console.error(err);
      alert('Failed to start investigation: ' + (err.message || 'Unknown error'));
    } finally {
      setInvestigatingId(null);
    }
  };

  return (
    <div className="repositories-page">
      <header className="page-header flex justify-between items-center">
        <div>
          <h1>Repositories</h1>
          <p className="text-secondary">Manage connected codebases</p>
        </div>
        <button className="btn btn-primary flex items-center gap-2" onClick={() => setShowAdd(!showAdd)}>
          <Plus className="w-4 h-4" /> Add Repository
        </button>
      </header>

      {showAdd && (
        <form className="glass-panel p-6 flex-col gap-4" onSubmit={handleAdd}>
          <h2>Connect Repository</h2>
          {connectionStep === 'idle' || connectionStep === 'failed' ? (
            <>
              {connectionStep === 'failed' && (
                <div className="error-block p-4 rounded text-error border border-error bg-error/10">
                  ✕ Repository connection failed: {connectionError}
                </div>
              )}
              <div className="form-group">
                <label>Name</label>
                <input 
                  type="text" 
                  value={newRepo.name} 
                  onChange={e => setNewRepo({...newRepo, name: e.target.value})} 
                  placeholder="e.g. backend-api"
                  required 
                />
              </div>
              <div className="form-group">
                <label>URL</label>
                <input 
                  type="text" 
                  value={newRepo.url} 
                  onChange={e => setNewRepo({...newRepo, url: e.target.value})} 
                  placeholder="https://github.com/org/repo"
                  required 
                />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAdd(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Connect</button>
              </div>
            </>
          ) : (
            <div className="connection-progress flex-col gap-4 py-4">
              <div className="progress-step flex items-center gap-3">
                {connectionStep === 'validating' ? <Loader className="w-5 h-5 animate-spin text-primary" /> : <CheckCircle className="w-5 h-5 text-success" />}
                <span className={connectionStep === 'validating' ? 'font-medium' : 'text-muted'}>Validating input</span>
              </div>
              <div className="progress-step flex items-center gap-3">
                {['idle', 'validating'].includes(connectionStep) ? <div className="w-5 h-5 rounded-full border-2 border-muted" /> :
                 connectionStep === 'connecting' ? <Loader className="w-5 h-5 animate-spin text-primary" /> : <CheckCircle className="w-5 h-5 text-success" />}
                <span className={connectionStep === 'connecting' ? 'font-medium' : 'text-muted'}>Connecting repository</span>
              </div>
              <div className="progress-step flex items-center gap-3">
                {['idle', 'validating', 'connecting'].includes(connectionStep) ? <div className="w-5 h-5 rounded-full border-2 border-muted" /> :
                 connectionStep === 'creating_session' ? <Loader className="w-5 h-5 animate-spin text-primary" /> : <CheckCircle className="w-5 h-5 text-success" />}
                <span className={connectionStep === 'creating_session' ? 'font-medium' : 'text-muted'}>Creating debug session</span>
              </div>
            </div>
          )}
        </form>
      )}

      {loading ? (
        <p>Loading repositories...</p>
      ) : repos.length === 0 ? (
        <div className="empty-state glass-panel">
          <Book className="w-12 h-12 text-muted mb-4" />
          <h3>No repositories connected</h3>
          <p className="text-secondary mb-4">Connect a repository to start debugging.</p>
          <button className="btn btn-primary" onClick={() => setShowAdd(true)}>Connect Repository</button>
        </div>
      ) : (
        <div className="repo-grid">
          {repos.map(repo => (
            <div key={repo.id} className="repo-card glass-panel">
              <div className="repo-card-header">
                <h3>{repo.name}</h3>
                <Book className="w-5 h-5 text-secondary" />
              </div>
              <p className="text-muted text-sm">{repo.url}</p>
              <div className="repo-card-footer mt-4 flex justify-between items-center text-sm">
                <div className="flex gap-2">
                  <span className="badge badge-success">Indexed</span>
                  <span className="text-muted">Branch: {repo.default_branch || 'main'}</span>
                </div>
                <button 
                  className="btn btn-primary text-xs py-1 px-3"
                  onClick={() => handleInvestigate(repo.id)}
                  disabled={investigatingId === repo.id}
                >
                  {investigatingId === repo.id ? 'Starting...' : 'Investigate'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
