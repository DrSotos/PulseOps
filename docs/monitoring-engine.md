# PulseOps Monitoring Engine & SSRF Protection

## 1. Monitored Probe Lifecycle

For every scheduled or manual check:
1. **SSRF Guard**: Target URL is resolved and checked against RFC 1918, loopbacks, link-local, and cloud metadata IPs (`169.254.169.254`).
2. **Monotonic Timing**: Timing is captured via `time.monotonic()` to eliminate drift from system clock updates.
3. **HTTP Dispatch**: Sends request with configured headers, timeout, and method (`GET`, `HEAD`, `POST`).
4. **Response Validation**:
   - Status code checked against `expected_status_codes`.
   - Content type checked against `expected_content_type` if defined.
   - Body parsed for expected text assertions (`expected_content`).
   - Latency evaluated against `performance_threshold_ms`.
5. **Persistence**: Record inserted into `monitoring_checks`.
6. **Incident Loop**: Evaluates `process_check_result` for auto-creation or auto-resolution of incidents.

## 2. Failure Classification Matrix

| Failure Type | Trigger Condition | Incident Mapping |
|--------------|-------------------|------------------|
| `connection_error` | Connection refused, reset by peer | Outage |
| `dns_error` | Failed DNS resolution via `getaddrinfo` | Outage |
| `timeout` | Connection or read timeout exceeded | Outage |
| `unexpected_status` | Status code not in expected list | Unexpected Status |
| `ssl_error` | Invalid certificate, expired cert, or TLS error | SSL Error |
| `content_mismatch` | Expected substring missing from response | Response Validation |
| `performance_threshold` | Response time > `performance_threshold_ms` | High Latency |
| `internal_error` | Probe runtime issue (excluded from uptime formula) | Ignored |

## 3. Worker Scheduling

The worker scheduler runs as an independent daemon loop (`app.workers.scheduler`):
- Scans active endpoints due for execution:
  $$(t_{\text{now}} - t_{\text{last\_checked}}) \ge \text{monitoring\_interval}$$
- Implements concurrency throttling via `asyncio.Semaphore(MAX_CONCURRENT_CHECKS)`.
- Prevents overlapping checks on the same endpoint.

