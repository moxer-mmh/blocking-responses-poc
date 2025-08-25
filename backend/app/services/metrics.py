"""Metrics tracking and monitoring service."""

from time import monotonic
from typing import Dict, Any, List


class MetricsTracker:
    """Track application metrics for monitoring and compliance reporting."""
    
    def __init__(self):
        self.total_requests = 0
        self.blocked_requests = 0
        self.judge_calls = 0
        self.risk_scores = []
        self.delay_times = []
        self.pattern_detections = {}
        self.presidio_detections = {}
        self.start_time = monotonic()

    def record_request(self, blocked=False, delay_ms=0, risk_score=0.0):
        """Record a request with its metrics."""
        self.total_requests += 1
        if blocked:
            self.blocked_requests += 1

        # Keep last 1000 risk scores for averaging
        self.risk_scores.append(risk_score)
        if len(self.risk_scores) > 1000:
            self.risk_scores.pop(0)

        # Keep last 1000 delay times for averaging
        self.delay_times.append(delay_ms)
        if len(self.delay_times) > 1000:
            self.delay_times.pop(0)

    def record_pattern_detection(self, pattern_name: str):
        """Record a pattern detection."""
        self.pattern_detections[pattern_name] = (
            self.pattern_detections.get(pattern_name, 0) + 1
        )

    def record_presidio_detection(self, entity_type: str):
        """Record a Presidio entity detection."""
        self.presidio_detections[entity_type] = (
            self.presidio_detections.get(entity_type, 0) + 1
        )

    def record_judge_call(self):
        """Record an LLM judge call."""
        self.judge_calls += 1

    @property
    def block_rate(self) -> float:
        """Calculate block rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.blocked_requests / self.total_requests) * 100

    @property
    def avg_risk_score(self) -> float:
        """Calculate average risk score."""
        if not self.risk_scores:
            return 0.0
        return sum(self.risk_scores) / len(self.risk_scores)

    @property
    def avg_processing_time(self) -> float:
        """Calculate average processing time in ms."""
        if not self.delay_times:
            return 0.0
        return sum(self.delay_times) / len(self.delay_times)

    @property
    def avg_response_time(self) -> float:
        """Calculate average response time (same as processing time for now)."""
        return self.avg_processing_time

    @property
    def requests_per_second(self) -> float:
        """Calculate requests per second."""
        elapsed = monotonic() - self.start_time
        if elapsed == 0:
            return 0.0
        return self.total_requests / elapsed

    @property
    def error_rate(self) -> float:
        """Calculate error rate (placeholder for now)."""
        return 0.0

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get complete metrics summary."""
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "block_rate": self.block_rate,
            "judge_calls": self.judge_calls,
            "avg_risk_score": self.avg_risk_score,
            "avg_processing_time": self.avg_processing_time,
            "avg_response_time": self.avg_response_time,
            "requests_per_second": self.requests_per_second,
            "error_rate": self.error_rate,
            "pattern_detections": self.pattern_detections.copy(),
            "presidio_detections": self.presidio_detections.copy(),
            "uptime_seconds": monotonic() - self.start_time,
        }

    def get_audit_logs(self) -> List[Dict[str, Any]]:
        """Get audit logs (placeholder - use database for real implementation)."""
        return []

    def reset(self):
        """Reset all metrics (useful for testing)."""
        self.__init__()
