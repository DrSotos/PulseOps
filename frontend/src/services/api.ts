import {
  DashboardOverview,
  EndpointHealthSummary,
  Incident,
  IncidentEvent,
  LatencyStatistics,
  MonitoredEndpoint,
  MonitoringCheck,
  NotificationChannel,
  NotificationDelivery,
  UptimeStatistics,
  User,
} from "../types";

const rawBase = import.meta.env.VITE_API_BASE_URL || "";
const API_BASE = rawBase ? `${rawBase.replace(/\/$/, "")}/api/v1` : "/api/v1";

class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("pulseops_token");
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return {} as T;
  }

  if (!response.ok) {
    let errMessage = `HTTP Error ${response.status}`;
    let errData = null;
    try {
      errData = await response.json();
      errMessage = errData.detail || errMessage;
    } catch {
      // not JSON
    }
    throw new ApiError(response.status, errMessage, errData);
  }

  return response.json();
}

export const api = {
  // ── Auth ────────────────────────────────────────────────────────────────
  async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    return request("/auth/login/json", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async register(email: string, password: string, full_name?: string): Promise<{ access_token: string; user: User }> {
    return request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    });
  },

  async getMe(): Promise<User> {
    return request("/auth/me");
  },

  async logout(): Promise<void> {
    try {
      await request("/auth/logout", { method: "POST" });
    } finally {
      localStorage.removeItem("pulseops_token");
    }
  },

  // ── Dashboard ───────────────────────────────────────────────────────────
  async getDashboardOverview(): Promise<DashboardOverview> {
    return request("/dashboard/overview");
  },

  async getDashboardHealth(): Promise<EndpointHealthSummary[]> {
    return request("/dashboard/health");
  },

  // ── Endpoints ───────────────────────────────────────────────────────────
  async listEndpoints(params?: { search?: string; is_active?: boolean; page?: number; per_page?: number }): Promise<{
    items: MonitoredEndpoint[];
    total: number;
    page: number;
    per_page: number;
  }> {
    const query = new URLSearchParams();
    if (params?.search) query.set("search", params.search);
    if (params?.is_active !== undefined) query.set("is_active", String(params.is_active));
    if (params?.page) query.set("page", String(params.page));
    if (params?.per_page) query.set("per_page", String(params.per_page));

    return request(`/endpoints?${query.toString()}`);
  },

  async getEndpoint(id: string): Promise<MonitoredEndpoint> {
    return request(`/endpoints/${id}`);
  },

  async createEndpoint(data: Partial<MonitoredEndpoint>): Promise<MonitoredEndpoint> {
    return request("/endpoints", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateEndpoint(id: string, data: Partial<MonitoredEndpoint>): Promise<MonitoredEndpoint> {
    return request(`/endpoints/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async deleteEndpoint(id: string): Promise<void> {
    return request(`/endpoints/${id}`, { method: "DELETE" });
  },

  async pauseEndpoint(id: string): Promise<MonitoredEndpoint> {
    return request(`/endpoints/${id}/pause`, { method: "POST" });
  },

  async resumeEndpoint(id: string): Promise<MonitoredEndpoint> {
    return request(`/endpoints/${id}/resume`, { method: "POST" });
  },

  async triggerCheck(id: string): Promise<MonitoringCheck> {
    return request(`/endpoints/${id}/check`, { method: "POST" });
  },

  async getEndpointChecks(id: string, page = 1, per_page = 20): Promise<{ items: MonitoringCheck[]; total: number }> {
    return request(`/endpoints/${id}/checks?page=${page}&per_page=${per_page}`);
  },

  async getEndpointStatistics(id: string, period = "24h"): Promise<{
    endpoint_id: string;
    period: string;
    uptime: UptimeStatistics;
    latency: LatencyStatistics;
    current_status: string;
    last_check_at?: string;
    last_success_at?: string;
  }> {
    return request(`/endpoints/${id}/statistics?period=${period}`);
  },

  // ── Incidents ───────────────────────────────────────────────────────────
  async listIncidents(params?: { status?: string; severity?: string; endpoint_id?: string; page?: number }): Promise<{
    items: Incident[];
    total: number;
    page: number;
    per_page: number;
  }> {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.severity) query.set("severity", params.severity);
    if (params?.endpoint_id) query.set("endpoint_id", params.endpoint_id);
    if (params?.page) query.set("page", String(params.page));

    return request(`/incidents?${query.toString()}`);
  },

  async getIncident(id: string): Promise<Incident> {
    return request(`/incidents/${id}`);
  },

  async acknowledgeIncident(id: string): Promise<Incident> {
    return request(`/incidents/${id}/acknowledge`, { method: "POST" });
  },

  async getIncidentEvents(id: string): Promise<IncidentEvent[]> {
    return request(`/incidents/${id}/events`);
  },

  async getIncidentNotifications(id: string): Promise<NotificationDelivery[]> {
    return request(`/incidents/${id}/notifications`);
  },

  // ── Notifications ───────────────────────────────────────────────────────
  async listChannels(): Promise<NotificationChannel[]> {
    return request("/notifications/channels");
  },

  async createChannel(data: Partial<NotificationChannel>): Promise<NotificationChannel> {
    return request("/notifications/channels", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateChannel(id: string, data: Partial<NotificationChannel>): Promise<NotificationChannel> {
    return request(`/notifications/channels/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async deleteChannel(id: string): Promise<void> {
    return request(`/notifications/channels/${id}`, { method: "DELETE" });
  },

  async testChannel(id: string): Promise<{ success: boolean; message: string }> {
    return request(`/notifications/channels/${id}/test`, { method: "POST" });
  },

  async getNotificationHistory(page = 1, per_page = 20): Promise<{ items: NotificationDelivery[]; total: number }> {
    return request(`/notifications/history?page=${page}&per_page=${per_page}`);
  },
};

