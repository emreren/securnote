"""
Prometheus metrics for SecurNote monitoring
"""

from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from functools import wraps
from typing import Callable, Any

# Prometheus metrics
user_operations_total = Counter(
    'securnote_user_operations_total',
    'Total number of user operations',
    ['username', 'operation', 'status']
)

operation_duration_seconds = Histogram(
    'securnote_operation_duration_seconds',
    'Time spent on operations',
    ['operation']
)

active_users_gauge = Gauge(
    'securnote_active_users',
    'Number of currently active users'
)

notes_total = Counter(
    'securnote_notes_total',
    'Total number of notes created',
    ['username']
)

failed_operations_total = Counter(
    'securnote_failed_operations_total',
    'Total number of failed operations',
    ['operation', 'error_type']
)


class MetricsCollector:
    """Collects and exports metrics for Prometheus."""

    def __init__(self, port: int = 9090):
        self.port = port
        self.active_users = set()

    def start_server(self):
        """Start Prometheus metrics server."""
        start_http_server(self.port)
        print(f"Prometheus metrics server started on port {self.port}")

    def record_operation(self, username: str, operation: str, success: bool, error_type: str = None):
        """Record a user operation."""
        status = 'success' if success else 'failed'
        user_operations_total.labels(
            username=username,
            operation=operation,
            status=status
        ).inc()

        if not success and error_type:
            failed_operations_total.labels(
                operation=operation,
                error_type=error_type
            ).inc()

        # Track active users
        self.active_users.add(username)
        active_users_gauge.set(len(self.active_users))

    def record_note_creation(self, username: str):
        """Record note creation."""
        notes_total.labels(username=username).inc()

    def time_operation(self, operation: str):
        """Decorator to time operations."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    operation_duration_seconds.labels(operation=operation).observe(duration)
            return wrapper
        return decorator


# Global metrics collector
metrics_collector = MetricsCollector()