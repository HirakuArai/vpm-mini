"""
VPM-Mini Metrics Module
Standard library only metrics collection with δ indicators
"""

from .collector import MetricsCollector, start_span, end_span, write_coverage, write_lag

__all__ = ["MetricsCollector", "start_span", "end_span", "write_coverage", "write_lag"]
