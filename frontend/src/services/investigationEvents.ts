import type { InvestigationEvent } from '../types/investigation';
import { API_BASE } from '../api/client';

type EventCallback = (event: InvestigationEvent) => void;

export class InvestigationEventsClient {
  private eventSource: EventSource | null = null;
  private sessionId: string;
  private callbacks: EventCallback[] = [];

  constructor(sessionId: string) {
    this.sessionId = sessionId;
  }

  connect() {
    if (this.eventSource) return;

    this.eventSource = new EventSource(`${API_BASE}/investigations/${this.sessionId}/events`);

    this.eventSource.onmessage = (e) => {
      try {
        const data: InvestigationEvent = JSON.parse(e.data);
        this.callbacks.forEach(cb => cb(data));
      } catch (err) {
        console.error('Failed to parse SSE message', err);
      }
    };

    this.eventSource.onerror = (err) => {
      console.error('SSE connection error:', err);
      this.eventSource?.close();
      this.eventSource = null;
      // Reconnect after 3 seconds
      setTimeout(() => this.connect(), 3000);
    };
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  subscribe(callback: EventCallback) {
    this.callbacks.push(callback);
    return () => {
      this.callbacks = this.callbacks.filter(cb => cb !== callback);
    };
  }
}
