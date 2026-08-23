import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { DebugSession, InvestigationEvent } from '../types/investigation';
import { getSession, stopSession, pauseSession, resumeSession, retrySession } from '../services/investigationApi';
import { InvestigationEventsClient } from '../services/investigationEvents';

interface DebugSessionState {
  session: DebugSession | null;
  connected: boolean;
  loading: boolean;
  error: string | null;
  loadSession: (sessionId: string) => Promise<void>;
  stop: () => Promise<void>;
  pause: () => Promise<void>;
  resume: () => Promise<void>;
  retry: () => Promise<void>;
}

const DebugSessionContext = createContext<DebugSessionState | undefined>(undefined);

export const DebugSessionProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<DebugSession | null>(null);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [eventClient, setEventClient] = useState<InvestigationEventsClient | null>(null);

  const loadSession = async (sessionId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSession(sessionId);
      setSession(data);

      if (eventClient) {
        eventClient.disconnect();
      }

      const client = new InvestigationEventsClient(sessionId);
      client.connect();
      setConnected(true);
      
      client.subscribe((event: InvestigationEvent) => {
        setSession(prev => {
          if (!prev) return prev;
          
          // Handle different event types to update the session projection
          const updatedSession = { ...prev };
          updatedSession.timeline = [...(prev.timeline || []), event];
          
          if (event.type === 'step.started' && event.step) {
            updatedSession.currentStep = event.step;
            updatedSession.currentAction = event.message;
          }
          if (event.type === 'agent.status') {
            // Assume the backend sends status updates this way
            // or we just poll or derive it
          }

          return updatedSession;
        });
      });

      setEventClient(client);

    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to load session');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    return () => {
      if (eventClient) {
        eventClient.disconnect();
      }
    };
  }, [eventClient]);

  const handleStop = async () => {
    if (!session) return;
    try {
      const updated = await stopSession(session.id);
      setSession({ ...session, status: updated.status });
    } catch (e) {
      console.error('Failed to stop', e);
    }
  };

  const handlePause = async () => {
    if (!session) return;
    try {
      const updated = await pauseSession(session.id);
      setSession({ ...session, status: updated.status });
    } catch (e) {
      console.error('Failed to pause', e);
    }
  };

  const handleResume = async () => {
    if (!session) return;
    try {
      const updated = await resumeSession(session.id);
      setSession({ ...session, status: updated.status });
    } catch (e) {
      console.error('Failed to resume', e);
    }
  };

  const handleRetry = async () => {
    if (!session) return;
    try {
      const updated = await retrySession(session.id);
      setSession({ ...session, status: updated.status, error: undefined });
    } catch (e) {
      console.error('Failed to retry', e);
    }
  };

  return (
    <DebugSessionContext.Provider
      value={{
        session,
        connected,
        loading,
        error,
        loadSession,
        stop: handleStop,
        pause: handlePause,
        resume: handleResume,
        retry: handleRetry
      }}
    >
      {children}
    </DebugSessionContext.Provider>
  );
};

export const useDebugSession = () => {
  const context = useContext(DebugSessionContext);
  if (context === undefined) {
    throw new Error('useDebugSession must be used within a DebugSessionProvider');
  }
  return context;
};
