# PulseOps Incident Management & Alerting

## 1. Incident Lifecycle

```text
[Healthy]
   │
   │  3 Consecutive Failures
   ▼
[OPEN] ─── (Operator Acknowledges) ───► [ACKNOWLEDGED]
   │                                          │
   │  2 Consecutive Successes                 │  2 Consecutive Successes
   ▼                                          ▼
[RESOLVED] ◄──────────────────────────────────┘
```

### Lifecycle States
- **Detected/Open**: Failure threshold reached. Alerts dispatched to enabled notification channels.
- **Acknowledged**: SRE / operator acknowledges ownership via UI or API.
- **Resolved**: Monitored service satisfies recovery threshold (consecutive successes).

## 2. Notification Dispatch Channels

1. **Email (SMTP)**:
   - Delivers HTML and plain-text summaries formatted with severity colors.
   - Includes affected service URL, timestamp, error description, and direct link.

2. **Webhooks (JSON)**:
   - Delivers structured JSON payloads containing event ID, incident state, and endpoint metadata.
   - Records delivery status (`delivered`, `failed`), HTTP response codes, and retry counts.

