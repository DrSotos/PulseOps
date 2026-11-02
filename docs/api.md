# PulseOps REST API Reference

Base prefix: `/api/v1`

## Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/auth/register` | Register new user account | No |
| `POST` | `/auth/login` | OAuth2 password form login | No |
| `POST` | `/auth/login/json` | JSON format login | No |
| `GET` | `/auth/me` | Current user profile | Bearer JWT |
| `POST` | `/auth/logout` | Session invalidation notice | Bearer JWT |

## Monitored Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/endpoints` | List monitored endpoints with filters |
| `POST` | `/endpoints` | Register a new endpoint with SSRF check |
| `GET` | `/endpoints/{id}` | Endpoint detail and configuration |
| `PATCH` | `/endpoints/{id}` | Update monitoring parameters |
| `DELETE` | `/endpoints/{id}` | Remove endpoint and cascade delete |
| `POST` | `/endpoints/{id}/pause` | Temporarily pause checks |
| `POST` | `/endpoints/{id}/resume` | Resume scheduled checks |
| `POST` | `/endpoints/{id}/check` | Immediate manual health check |
| `GET` | `/endpoints/{id}/checks` | Historical health checks pagination |
| `GET` | `/endpoints/{id}/statistics` | Combined uptime, latency, percentiles |
| `GET` | `/endpoints/{id}/uptime` | 24h / 7d / 30d uptime calculations |
| `GET` | `/endpoints/{id}/latency` | $P_{50}, P_{90}, P_{95}, P_{99}$ latency |

## Incidents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/incidents` | List incidents with status and severity filters |
| `GET` | `/incidents/{id}` | Incident detail with timeline |
| `POST` | `/incidents/{id}/acknowledge` | Acknowledge active incident |
| `GET` | `/incidents/{id}/events` | Chronological audit events |
| `GET` | `/incidents/{id}/notifications`| Notification delivery attempts |

## Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/notifications/channels` | List email and webhook destinations |
| `POST` | `/notifications/channels` | Register notification channel |
| `PATCH` | `/notifications/channels/{id}` | Update notification channel |
| `DELETE` | `/notifications/channels/{id}` | Delete notification channel |
| `POST` | `/notifications/channels/{id}/test` | Trigger live test dispatch |
| `GET` | `/notifications/history` | Audit log of all delivery attempts |

## Dashboard & Streaming

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard/overview` | High-level metrics and activity feed |
| `GET` | `/dashboard/health` | Fast status list for all services |
| `GET` | `/events/stream?token=...` | Server-Sent Events (SSE) live stream |

