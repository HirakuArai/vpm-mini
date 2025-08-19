"""
Test metrics collection including δ (delta) indicators
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from metrics.collector import (
    MetricsCollector,
    start_span,
    end_span,
    write_coverage,
    write_lag,
)


class TestMetricsCollector(unittest.TestCase):
    """Test the MetricsCollector class and δ metrics"""

    def setUp(self):
        """Set up test environment"""
        self.collector = MetricsCollector()
        self.temp_dir = Path(tempfile.mkdtemp())

        # Change working directory to temp for file operations
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)

    def create_mock_egspace_events(self, count: int = 10):
        """Create mock EG-Space events file"""
        egspace_dir = Path("egspace")
        egspace_dir.mkdir(exist_ok=True)

        events_file = egspace_dir / "events.jsonl"
        with open(events_file, "w") as f:
            for i in range(count):
                event = {
                    "vec_id": f"session_test_{i}",
                    "role": "Watcher" if i % 2 == 0 else "Curator",
                    "payload": {"input": f"test_{i}"},
                    "result": {"role": "Watcher", "output": f"output_{i}"},
                    "ts": "2025-08-19T10:00:00.000000+00:00",
                }
                f.write(json.dumps(event) + "\n")

    def create_mock_digest(self, ref_count: int = 5):
        """Create mock digest file with EG-Space references"""
        sessions_dir = Path("docs/sessions")
        sessions_dir.mkdir(parents=True, exist_ok=True)

        digest_file = sessions_dir / "2025-08-19_digest.md"
        content = "# Session Digest\n\n## EG-Space References\n\n"

        for i in range(ref_count):
            if i % 2 == 0:
                content += (
                    f"- Watcher: refs: [session_test_{i}] → logs/test.jsonl#latest\n"
                )
            else:
                content += (
                    f"- Curator: refs: [session_test_{i}] → logs/test.jsonl#latest\n"
                )

        with open(digest_file, "w") as f:
            f.write(content)

    def test_coverage_calculation_with_delta(self):
        """Test coverage calculation including δ metrics"""
        # Create test data
        self.create_mock_egspace_events(10)  # 10 events
        self.create_mock_digest(6)  # 6 digest entries

        coverage = self.collector.calculate_coverage()

        # Check standard metrics
        self.assertEqual(coverage["events_total"], 10)
        self.assertEqual(coverage["digest_entries"], 6)
        self.assertEqual(coverage["egspace_events"], 10)

        # Check δ metrics
        self.assertEqual(coverage["delta_events"], 4)  # 10 - 6 = 4
        self.assertAlmostEqual(
            coverage["delta_reflect_rate"], 0.4, places=2
        )  # 1 - 0.6 = 0.4

        # Check types and ranges
        self.assertIsInstance(coverage["delta_events"], int)
        self.assertGreaterEqual(coverage["delta_events"], 0)
        self.assertIsInstance(coverage["delta_reflect_rate"], float)
        self.assertGreaterEqual(coverage["delta_reflect_rate"], 0.0)
        self.assertLessEqual(coverage["delta_reflect_rate"], 1.0)

    def test_delta_metrics_edge_cases(self):
        """Test δ metrics with edge cases"""
        # Case 1: No events, no digest
        coverage = self.collector.calculate_coverage()
        self.assertEqual(coverage["delta_events"], 0)
        self.assertEqual(coverage["delta_reflect_rate"], 1.0)  # 1 - 0 = 1

        # Case 2: Events but no digest
        self.create_mock_egspace_events(5)
        coverage = self.collector.calculate_coverage()
        self.assertEqual(coverage["delta_events"], 5)
        self.assertEqual(coverage["delta_reflect_rate"], 1.0)  # 1 - 0 = 1

        # Case 3: Perfect reflection (all events in digest)
        self.create_mock_digest(5)
        coverage = self.collector.calculate_coverage()
        self.assertEqual(coverage["delta_events"], 0)  # 5 - 5 = 0
        self.assertEqual(coverage["delta_reflect_rate"], 0.0)  # 1 - 1 = 0

    def test_delta_events_non_negative(self):
        """Test that delta_events is never negative"""
        # Create more digest entries than events (edge case)
        self.create_mock_egspace_events(3)
        self.create_mock_digest(10)  # More digest than events

        coverage = self.collector.calculate_coverage()
        self.assertGreaterEqual(coverage["delta_events"], 0)

    def test_delta_reflect_rate_clamped(self):
        """Test that delta_reflect_rate is properly clamped"""
        # Test with high reflection rate
        self.create_mock_egspace_events(10)
        self.create_mock_digest(10)

        coverage = self.collector.calculate_coverage()
        self.assertEqual(coverage["delta_reflect_rate"], 0.0)  # Perfect reflection

    def test_span_tracking_with_delta(self):
        """Test span tracking for lag metrics"""
        # Test span operations
        self.collector.start_span("test_stage")
        import time

        time.sleep(0.001)  # Small delay for measurable duration
        duration = self.collector.end_span("test_stage")

        self.assertGreater(duration, 0)
        self.assertIn("test_stage", self.collector.completed_spans)

        # Test lag calculation
        lag = self.collector.calculate_lag()
        self.assertIn("stages", lag)
        self.assertIn("test_stage", lag["stages"])
        self.assertEqual(lag["run_count"], 1)

    def test_write_coverage_with_delta(self):
        """Test writing coverage metrics including δ to file"""
        self.create_mock_egspace_events(8)
        self.create_mock_digest(3)

        self.collector.write_coverage()

        # Check file exists
        coverage_file = Path("reports/coverage.json")
        self.assertTrue(coverage_file.exists())

        # Check content includes δ metrics
        with open(coverage_file, "r") as f:
            data = json.load(f)

        self.assertIn("delta_events", data)
        self.assertIn("delta_reflect_rate", data)
        self.assertEqual(data["delta_events"], 5)  # 8 - 3 = 5
        self.assertAlmostEqual(
            data["delta_reflect_rate"], 0.625, places=3
        )  # 1 - 0.375 = 0.625

    def test_write_lag_metrics(self):
        """Test writing lag metrics to file"""
        # Simulate some spans
        self.collector.start_span("log")
        self.collector.end_span("log")
        self.collector.start_span("summary")
        self.collector.end_span("summary")

        self.collector.write_lag()

        # Check file exists
        lag_file = Path("reports/lag.json")
        self.assertTrue(lag_file.exists())

        # Check content
        with open(lag_file, "r") as f:
            data = json.load(f)

        self.assertIn("stages", data)
        self.assertIn("run_count", data)
        self.assertIn("log", data["stages"])
        self.assertIn("summary", data["stages"])

    def test_global_functions_with_delta(self):
        """Test global convenience functions"""
        # Test span functions
        start_span("global_test")
        import time

        time.sleep(0.001)
        duration = end_span("global_test")
        self.assertGreater(duration, 0)

        # Create test data for coverage with δ
        self.create_mock_egspace_events(12)
        self.create_mock_digest(4)

        # Test write functions
        write_coverage()
        write_lag()

        # Verify files and δ metrics
        with open("reports/coverage.json", "r") as f:
            coverage = json.load(f)
        self.assertIn("delta_events", coverage)
        self.assertEqual(coverage["delta_events"], 8)  # 12 - 4 = 8

        with open("reports/lag.json", "r") as f:
            lag = json.load(f)
        self.assertIn("global_test", lag["stages"])


class TestMetricsDeltaIntegration(unittest.TestCase):
    """Integration tests for δ metrics"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)

    def test_delta_metrics_complete_workflow(self):
        """Test complete workflow with δ metrics"""
        collector = MetricsCollector()

        # Simulate pipeline stages
        collector.start_span("log")
        collector.end_span("log")
        collector.start_span("summary")
        collector.end_span("summary")
        collector.start_span("digest")
        collector.end_span("digest")

        # Create realistic test data
        egspace_dir = Path("egspace")
        egspace_dir.mkdir(exist_ok=True)

        # 15 events
        with open(egspace_dir / "events.jsonl", "w") as f:
            for i in range(15):
                event = {"vec_id": f"session_{i}", "role": "Watcher"}
                f.write(json.dumps(event) + "\n")

        # 6 digest references
        sessions_dir = Path("docs/sessions")
        sessions_dir.mkdir(parents=True, exist_ok=True)
        with open(sessions_dir / "test_digest.md", "w") as f:
            f.write("# Digest\n## EG-Space References\n")
            for i in range(6):
                f.write(f"- Watcher: refs: [session_{i}]\n")

        # Generate metrics
        collector.write_coverage()
        collector.write_lag()

        # Verify δ metrics
        with open("reports/coverage.json", "r") as f:
            coverage = json.load(f)

        self.assertEqual(coverage["events_total"], 15)
        self.assertEqual(coverage["digest_entries"], 6)
        self.assertEqual(coverage["delta_events"], 9)  # 15 - 6 = 9
        self.assertAlmostEqual(
            coverage["delta_reflect_rate"], 0.6, places=2
        )  # 1 - 0.4 = 0.6

        # Verify lag metrics
        with open("reports/lag.json", "r") as f:
            lag = json.load(f)

        self.assertIn("log", lag["stages"])
        self.assertIn("summary", lag["stages"])
        self.assertIn("digest", lag["stages"])


if __name__ == "__main__":
    unittest.main()
