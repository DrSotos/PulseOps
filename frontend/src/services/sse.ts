import { useEffect } from "react";

type SSECallback = (event: { type: string; data: any }) => void;

const rawBase = import.meta.env.VITE_API_BASE_URL || "";
const API_BASE = rawBase ? `${rawBase.replace(/\/$/, "")}/api/v1` : "/api/v1";

class RealtimeStream {
  private eventSource: EventSource | null = null;
  private listeners: Set<SSECallback> = new Set();
  private reconnectTimer: any = null;

  connect() {
    const token = localStorage.getItem("pulseops_token");
    if (!token) return;

    if (this.eventSource) {
      this.eventSource.close();
    }

    const url = `${API_BASE}/events/stream?token=${encodeURIComponent(token)}`;
    this.eventSource = new EventSource(url);

    this.eventSource.onmessage = () => {
      // heartbeats/unnamed events
    };

    const eventTypes = ["check_completed", "incident_created", "incident_resolved", "connected"];
    eventTypes.forEach((type) => {
      this.eventSource?.addEventListener(type, (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          this.notify({ type, data });
        } catch {
          // ignore parse error
        }
      });
    });

    this.eventSource.onerror = () => {
      this.eventSource?.close();
      this.eventSource = null;
      clearTimeout(this.reconnectTimer);
      // Reconnect after 5 seconds
      this.reconnectTimer = setTimeout(() => this.connect(), 5000);
    };
  }

  disconnect() {
    clearTimeout(this.reconnectTimer);
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  subscribe(callback: SSECallback) {
    this.listeners.add(callback);
    return () => {
      this.listeners.delete(callback);
    };
  }

  private notify(event: { type: string; data: any }) {
    this.listeners.forEach((listener) => listener(event));
  }
}

export const realtimeStream = new RealtimeStream();

export function useRealtime(onEvent: SSECallback) {
  useEffect(() => {
    const unsubscribe = realtimeStream.subscribe(onEvent);
    return () => {
      unsubscribe();
    };
  }, [onEvent]);
}
