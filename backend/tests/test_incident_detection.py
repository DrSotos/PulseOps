"""Unit tests for incident severity ranking and detection."""

from app.services.incidents.detector import (
    INCIDENT_HIGH_LATENCY,
    INCIDENT_OUTAGE,
    INCIDENT_SSL_ERROR,
    _severity_rank,
    determine_severity,
)


def test_severity_determinations():
    assert determine_severity(INCIDENT_OUTAGE, 3) == "medium"
    assert determine_severity(INCIDENT_OUTAGE, 5) == "high"
    assert determine_severity(INCIDENT_OUTAGE, 10) == "critical"

    assert determine_severity(INCIDENT_HIGH_LATENCY, 10) == "low"
    assert determine_severity(INCIDENT_SSL_ERROR, 2) == "high"


def test_severity_hierarchy():
    assert _severity_rank("low") < _severity_rank("medium")
    assert _severity_rank("medium") < _severity_rank("high")
    assert _severity_rank("high") < _severity_rank("critical")

