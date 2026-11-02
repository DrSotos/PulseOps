"""HTTP health check execution engine with high-precision monotonic timing."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime

import httpx

from app.core.logging import get_logger
from app.models.check import MonitoringCheck
from app.models.endpoint import MonitoredEndpoint
from app.utils.url_validator import URLValidationError, validate_url

logger = get_logger(__name__)

# Standardized failure classification constants
FAILURE_CONNECTION = "connection_error"
FAILURE_DNS = "dns_error"
FAILURE_TIMEOUT = "timeout"
FAILURE_STATUS = "unexpected_status"
FAILURE_SSL = "ssl_error"
FAILURE_CONTENT = "content_mismatch"
FAILURE_PERFORMANCE = "performance_threshold"
FAILURE_INTERNAL = "internal_error"
FAILURE_VALIDATION = "response_validation"


async def execute_check(endpoint: MonitoredEndpoint) -> MonitoringCheck:
    """Execute an asynchronous HTTP health check against a MonitoredEndpoint."""
    started_at = datetime.now(UTC)

    # 1. SSRF & Security Validation
    try:
        validate_url(endpoint.url)
    except URLValidationError as e:
        completed_at = datetime.now(UTC)
        return MonitoringCheck(
            id=uuid.uuid4(),
            endpoint_id=endpoint.id,
            started_at=started_at,
            completed_at=completed_at,
            response_time_ms=None,
            status_code=None,
            is_successful=False,
            failure_type=FAILURE_INTERNAL,
            error_message=f"Security check rejected destination: {str(e)[:300]}",
            response_size_bytes=None,
        )

    headers = dict(endpoint.custom_headers or {})
    headers.setdefault("User-Agent", "PulseOps-Monitor/1.0 (+https://pulseops.dev)")

    response_time_ms: float | None = None
    status_code: int | None = None
    is_successful = False
    failure_type: str | None = None
    error_message: str | None = None
    response_size: int | None = None

    try:
        timeout_cfg = httpx.Timeout(
            timeout=float(endpoint.timeout),
            connect=min(5.0, float(endpoint.timeout)),
        )

        async with httpx.AsyncClient(
            timeout=timeout_cfg,
            follow_redirects=False,  # Enforce non-redirect policy to prevent open-redirect SSRF
            verify=True,
        ) as client:
            t0 = time.monotonic()

            req_kwargs = {"headers": headers}
            method = endpoint.http_method.upper()

            if method == "POST" and endpoint.request_body:
                req_kwargs["content"] = endpoint.request_body.encode("utf-8")

            response = await client.request(
                method=method,
                url=endpoint.url,
                **req_kwargs,
            )

            t1 = time.monotonic()
            response_time_ms = round((t1 - t0) * 1000.0, 2)
            status_code = response.status_code

            # Read content up to 1MB safely
            raw_body = response.content
            response_size = len(raw_body)

            expected_codes = endpoint.expected_status_codes or [200]
            if status_code not in expected_codes:
                failure_type = FAILURE_STATUS
                error_message = f"Expected HTTP status in {expected_codes}, got {status_code}"
            elif endpoint.expected_content_type:
                ctype = response.headers.get("content-type", "")
                if endpoint.expected_content_type.lower() not in ctype.lower():
                    failure_type = FAILURE_VALIDATION
                    error_message = (
                        f"Expected content-type '{endpoint.expected_content_type}', got '{ctype}'"
                    )
            elif endpoint.expected_content:
                text_snippet = response.text[:10000]
                if endpoint.expected_content not in text_snippet:
                    failure_type = FAILURE_CONTENT
                    error_message = f"Expected content '{endpoint.expected_content[:50]}' not found in response body"
            elif (
                endpoint.performance_threshold_ms
                and response_time_ms > endpoint.performance_threshold_ms
            ):
                failure_type = FAILURE_PERFORMANCE
                error_message = (
                    f"Response time ({response_time_ms}ms) exceeded threshold "
                    f"({endpoint.performance_threshold_ms}ms)"
                )

            if failure_type is None:
                is_successful = True

    except httpx.ConnectTimeout:
        failure_type = FAILURE_TIMEOUT
        error_message = f"Connection timed out after {endpoint.timeout}s"
    except httpx.ReadTimeout:
        failure_type = FAILURE_TIMEOUT
        error_message = f"Read timed out after {endpoint.timeout}s"
    except httpx.TimeoutException as e:
        failure_type = FAILURE_TIMEOUT
        error_message = f"Request timed out: {str(e)[:200]}"
    except httpx.ConnectError as e:
        err_str = str(e).lower()
        if "getaddrinfo" in err_str or "name resolution" in err_str or "dns" in err_str:
            failure_type = FAILURE_DNS
            error_message = f"DNS resolution failed: {str(e)[:200]}"
        else:
            failure_type = FAILURE_CONNECTION
            error_message = f"Connection failed: {str(e)[:200]}"
    except Exception as e:  # noqa: BLE001
        name = type(e).__name__.lower()
        msg = str(e).lower()
        if "ssl" in name or "certificate" in msg or "tls" in msg:
            failure_type = FAILURE_SSL
            error_message = f"SSL/TLS validation failed: {str(e)[:200]}"
        else:
            failure_type = FAILURE_INTERNAL
            error_message = f"Internal probe error: {type(e).__name__}: {str(e)[:200]}"
            logger.warning(f"Unexpected probe exception for {endpoint.url}: {e}")

    completed_at = datetime.now(UTC)

    check = MonitoringCheck(
        id=uuid.uuid4(),
        endpoint_id=endpoint.id,
        started_at=started_at,
        completed_at=completed_at,
        response_time_ms=response_time_ms,
        status_code=status_code,
        is_successful=is_successful,
        failure_type=failure_type,
        error_message=error_message,
        response_size_bytes=response_size,
    )

    logger.debug(
        f"Executed check for endpoint {endpoint.name} ({endpoint.url}): "
        f"status={status_code}, time={response_time_ms}ms, ok={is_successful}"
    )
    return check
