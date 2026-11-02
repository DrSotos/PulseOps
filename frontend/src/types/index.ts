export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface MonitoredEndpoint {
  id: string;
  user_id: string;
  name: string;
  url: string;
  http_method: "GET" | "HEAD" | "POST";
  monitoring_interval: number;
  timeout: number;
  expected_status_codes: number[];
  performance_threshold_ms?: number | null;
  custom_headers?: Record<string, string> | null;
  request_body?: string | null;
  expected_content?: string | null;
  expected_content_type?: string | null;
  is_active: boolean;
  last_checked_at?: string | null;
  last_success_at?: string | null;
  created_at: string;
  updated_at: string;
  current_status: "operational" | "degraded" | "down" | "paused" | "unknown";
  latest_response_time_ms?: number | null;
  uptime_percentage?: number | null;
}

export interface MonitoringCheck {
  id: string;
  endpoint_id: string;
  started_at: string;
  completed_at: string;
  response_time_ms?: number | null;
  status_code?: number | null;
  is_successful: boolean;
  failure_type?: string | null;
  error_message?: string | null;
  response_size_bytes?: number | null;
  created_at: string;
}

export interface IncidentEvent {
  id: string;
  incident_id: string;
  event_type: string;
  description: string;
  metadata_json?: Record<string, any> | null;
  created_at: string;
}

export interface Incident {
  id: string;
  endpoint_id: string;
  endpoint_name?: string | null;
  endpoint_url?: string | null;
  incident_type: string;
  severity: "low" | "medium" | "high" | "critical";
  status: "detected" | "open" | "acknowledged" | "resolved";
  description: string;
  started_at: string;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
  duration_seconds?: number | null;
  created_at: string;
  updated_at: string;
  events?: IncidentEvent[];
}

export interface NotificationChannel {
  id: string;
  user_id: string;
  name: string;
  channel_type: "email" | "webhook";
  destination: string;
  configuration?: Record<string, any> | null;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationDelivery {
  id: string;
  incident_id: string;
  channel_id: string;
  channel_name?: string | null;
  channel_type?: string | null;
  event_type: string;
  delivery_status: "pending" | "delivered" | "failed" | "retrying";
  attempts: number;
  last_attempt_at?: string | null;
  response_status?: number | null;
  error_message?: string | null;
  created_at: string;
}

export interface EndpointHealthSummary {
  id: string;
  name: string;
  url: string;
  http_method: string;
  status: "operational" | "degraded" | "down" | "paused" | "unknown";
  latest_response_time_ms?: number | null;
  uptime_percentage: number;
  last_checked_at?: string | null;
}

export interface ActivityItem {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  severity?: string | null;
}

export interface DashboardOverview {
  total_endpoints: number;
  operational_count: number;
  degraded_count: number;
  down_count: number;
  paused_count: number;
  active_incidents_count: number;
  overall_uptime_percentage: number;
  average_response_time_ms?: number | null;
  endpoint_health: EndpointHealthSummary[];
  recent_activity: ActivityItem[];
}

export interface LatencyStatistics {
  endpoint_id: string;
  period: string;
  sample_count: number;
  avg_ms?: number | null;
  min_ms?: number | null;
  max_ms?: number | null;
  p50_ms?: number | null;
  p90_ms?: number | null;
  p95_ms?: number | null;
  p99_ms?: number | null;
}

export interface UptimeStatistics {
  endpoint_id: string;
  period: string;
  total_checks: number;
  successful_checks: number;
  failed_checks: number;
  uptime_percentage: number;
  first_check_at?: string | null;
  last_check_at?: string | null;
}

