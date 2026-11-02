"""Unit tests for URL and SSRF validation logic."""

import pytest

from app.utils.url_validator import URLValidationError, validate_url


def test_valid_urls():
    assert validate_url("https://httpbin.org/get") == "https://httpbin.org/get"
    assert validate_url("http://example.com/status") == "http://example.com/status"


def test_reject_schemes():
    with pytest.raises(URLValidationError, match="Invalid URL scheme"):
        validate_url("ftp://ftp.example.com/file")

    with pytest.raises(URLValidationError, match="Invalid URL scheme"):
        validate_url("file:///etc/passwd")

    with pytest.raises(URLValidationError, match="Invalid URL scheme"):
        validate_url("gopher://example.com")


def test_reject_cloud_metadata():
    with pytest.raises(URLValidationError, match="cloud metadata"):
        validate_url("http://169.254.169.254/latest/meta-data/")

    with pytest.raises(URLValidationError, match="cloud metadata"):
        validate_url("http://metadata.google.internal/computeMetadata/v1/")


def test_reject_private_ranges():
    with pytest.raises(URLValidationError):
        validate_url("http://127.0.0.1:8080/metrics")

    with pytest.raises(URLValidationError):
        validate_url("http://localhost:5432")

    with pytest.raises(URLValidationError):
        validate_url("http://10.0.0.1/admin")

    with pytest.raises(URLValidationError):
        validate_url("http://192.168.1.1/router")

    with pytest.raises(URLValidationError):
        validate_url("http://172.16.0.5/api")

