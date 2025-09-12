"""
Unit tests for hello-ai metrics
"""

from prometheus_client import REGISTRY
from metrics import REQUEST_COUNT, REQUEST_DURATION, APP_UP, BUILD_INFO, get_metrics


def test_metrics_exist():
    """Test that all required metrics are registered"""
    # Check that metrics are in the registry by generating output and checking content
    from prometheus_client import generate_latest

    output = generate_latest(REGISTRY).decode()

    assert "hello_ai_requests_total" in output
    assert "hello_ai_request_duration_seconds" in output
    assert "hello_ai_up" in output
    assert "hello_ai_build_info" in output


def test_request_count_labels():
    """Test request count metric has correct labels"""
    REQUEST_COUNT.labels(route="test", method="GET", code="200").inc()

    # Check that the metric was incremented
    samples = list(REQUEST_COUNT.collect())[0].samples
    assert len(samples) > 0

    # Find our test sample
    test_sample = next((s for s in samples if "test" in str(s.labels)), None)
    assert test_sample is not None
    assert test_sample.labels["route"] == "test"
    assert test_sample.labels["method"] == "GET"
    assert test_sample.labels["code"] == "200"


def test_request_duration_labels():
    """Test request duration metric has correct labels"""
    REQUEST_DURATION.labels(route="test", method="GET").observe(0.1)

    samples = list(REQUEST_DURATION.collect())[0].samples
    assert len(samples) > 0

    # Check for histogram samples (bucket, sum, count)
    bucket_samples = [s for s in samples if s.name.endswith("_bucket")]
    assert len(bucket_samples) > 0


def test_app_up_gauge():
    """Test app up gauge is set to 1"""
    samples = list(APP_UP.collect())[0].samples
    assert len(samples) == 1
    assert samples[0].value == 1.0


def test_build_info():
    """Test build info contains version and commit"""
    samples = list(BUILD_INFO.collect())[0].samples
    assert len(samples) == 1

    labels = samples[0].labels
    assert "version" in labels
    assert "commit" in labels


def test_metrics_format():
    """Test that metrics can be exported in Prometheus format"""
    response = get_metrics()

    # Check content type
    assert "application/openmetrics-text" in response.media_type

    # Check content contains our metrics
    content = response.body.decode()
    assert "hello_ai_requests_total" in content
    assert "hello_ai_request_duration_seconds" in content
    assert "hello_ai_up" in content
    assert "hello_ai_build_info" in content
