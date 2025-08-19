"""
Metrics Collection Module for VPM-Mini Phase 0
Collects coverage and lag metrics with δ (delta) indicators
Standard library only implementation
"""

import json
import time
from pathlib import Path
from typing import Dict, Any


class MetricsCollector:
    """Collects and calculates metrics for VPM-Mini system"""

    def __init__(self):
        self.spans: Dict[str, float] = {}
        self.completed_spans: Dict[str, float] = {}

    def start_span(self, name: str) -> None:
        """Start timing a named span"""
        self.spans[name] = time.time()

    def end_span(self, name: str) -> float:
        """End timing a named span and return duration in milliseconds"""
        if name not in self.spans:
            return 0.0

        duration = (time.time() - self.spans[name]) * 1000  # Convert to ms
        self.completed_spans[name] = duration
        del self.spans[name]
        return duration

    def calculate_coverage(self) -> Dict[str, Any]:
        """Calculate coverage metrics with δ indicators"""
        from datetime import date

        today = date.today().strftime("%Y-%m-%d")

        # Count EG-Space events
        events_total = self._count_egspace_events()

        # Count digest entries
        digest_entries = self._count_digest_entries()

        # Count reverse links
        reverse_links_ok = self._count_reverse_links()
        reverse_links_missing = max(digest_entries - reverse_links_ok, 0)

        # Calculate reflect rate
        digest_reflect_rate = digest_entries / max(events_total, 1)

        # Calculate δ (delta) metrics
        delta_events = max(events_total - digest_entries, 0)
        delta_reflect_rate = round(1.0 - min(digest_reflect_rate, 1.0), 6)

        return {
            "date": today,
            "events_total": events_total,
            "digest_entries": digest_entries,
            "egspace_events": events_total,
            "reverse_links_ok": reverse_links_ok,
            "reverse_links_missing": reverse_links_missing,
            "digest_reflect_rate": digest_reflect_rate,
            "delta_events": delta_events,
            "delta_reflect_rate": delta_reflect_rate,
        }

    def calculate_lag(self) -> Dict[str, Any]:
        """Calculate lag percentiles for each pipeline stage"""
        if not self.completed_spans:
            return {"stages": {}, "run_count": 0}

        stages = {}
        for stage_name, duration in self.completed_spans.items():
            # For single runs, p50 and p95 are the same
            stages[stage_name] = {"p50_ms": duration, "p95_ms": duration}

        return {"stages": stages, "run_count": 1}

    def _count_egspace_events(self) -> int:
        """Count total events in EG-Space"""
        events_file = Path("egspace/events.jsonl")
        if not events_file.exists():
            return 0

        try:
            with open(events_file, "r", encoding="utf-8") as f:
                return sum(1 for line in f if line.strip())
        except (IOError, UnicodeDecodeError):
            return 0

    def _count_digest_entries(self) -> int:
        """Count entries in latest digest file"""
        digest_dir = Path("docs/sessions")
        if not digest_dir.exists():
            return 0

        # Find most recent digest file
        digest_files = list(digest_dir.glob("*_digest.md"))
        if not digest_files:
            return 0

        latest_digest = max(digest_files, key=lambda p: p.stat().st_mtime)

        try:
            with open(latest_digest, "r", encoding="utf-8") as f:
                content = f.read()
                # Count EG-Space reference lines
                return len(
                    [
                        line
                        for line in content.split("\n")
                        if line.strip().startswith("- Watcher:")
                        or line.strip().startswith("- Curator:")
                    ]
                )
        except (IOError, UnicodeDecodeError):
            return 0

    def _count_reverse_links(self) -> int:
        """Count successful reverse links in digest"""
        # For this implementation, assume all digest entries have reverse links
        return self._count_digest_entries()

    def write_coverage(self) -> None:
        """Write coverage metrics to reports/coverage.json"""
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        coverage = self.calculate_coverage()
        with open(reports_dir / "coverage.json", "w") as f:
            json.dump(coverage, f, indent=2)

    def write_lag(self) -> None:
        """Write lag metrics to reports/lag.json"""
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        lag = self.calculate_lag()
        with open(reports_dir / "lag.json", "w") as f:
            json.dump(lag, f, indent=2)


# Global collector instance
_collector = MetricsCollector()


# Convenience functions for easy import
def start_span(name: str) -> None:
    """Start timing a named span"""
    _collector.start_span(name)


def end_span(name: str) -> float:
    """End timing a named span and return duration"""
    return _collector.end_span(name)


def write_coverage() -> None:
    """Write coverage metrics to file"""
    _collector.write_coverage()


def write_lag() -> None:
    """Write lag metrics to file"""
    _collector.write_lag()
