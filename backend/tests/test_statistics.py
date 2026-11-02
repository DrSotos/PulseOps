"""Unit tests for statistical distributions and percentile calculations."""

import pytest

from app.services.statistics.calculator import _calculate_percentile, parse_period


def test_percentile_calculations():
    # Odd sequence
    data = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert _calculate_percentile(data, 50) == 30.0

    # Large uniform distribution
    data_100 = [float(x) for x in range(1, 101)]
    assert _calculate_percentile(data_100, 50) == 50.5
    assert _calculate_percentile(data_100, 90) == pytest.approx(90.1, abs=0.5)
    assert _calculate_percentile(data_100, 95) == pytest.approx(95.05, abs=0.5)
    assert _calculate_percentile(data_100, 99) == pytest.approx(99.01, abs=0.5)

    # Empty
    assert _calculate_percentile([], 50) is None

    # Single item
    assert _calculate_percentile([42.5], 90) == 42.5


def test_period_parsing():
    assert parse_period("1h").total_seconds() == 3600
    assert parse_period("24h").total_seconds() == 86400
    assert parse_period("7d").total_seconds() == 86400 * 7
    assert parse_period("30d").total_seconds() == 86400 * 30
    assert parse_period("unknown").total_seconds() == 86400

