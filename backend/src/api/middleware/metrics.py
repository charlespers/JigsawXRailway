"""
Metrics Middleware
Request/response metrics and performance monitoring
"""

import time
import logging
from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and stores metrics."""
    
    def __init__(self):
        self.request_counts: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.latencies: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
        self.start_time = time.time()
    
    def record_request(self, path: str, method: str, status_code: int, latency: float):
        """Record a request metric."""
        with self.lock:
            key = f"{method} {path}"
            self.request_counts[key] += 1
            if status_code >= 400:
                self.error_counts[key] += 1
            self.latencies[key].append(latency)
            # Keep only last 1000 latencies per endpoint
            if len(self.latencies[key]) > 1000:
                self.latencies[key] = self.latencies[key][-1000:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        with self.lock:
            uptime = time.time() - self.start_time
            metrics = {
                "uptime_seconds": uptime,
                "endpoints": {}
            }
            
            for key in self.request_counts:
                request_count = self.request_counts[key]
                error_count = self.error_counts.get(key, 0)
                latencies = self.latencies.get(key, [])
                
                avg_latency = sum(latencies) / len(latencies) if latencies else 0
                p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
                p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
                
                metrics["endpoints"][key] = {
                    "request_count": request_count,
                    "error_count": error_count,
                    "success_rate": (request_count - error_count) / request_count if request_count > 0 else 1.0,
                    "avg_latency_ms": avg_latency * 1000,
                    "p95_latency_ms": p95_latency * 1000,
                    "p99_latency_ms": p99_latency * 1000,
                    "requests_per_second": request_count / uptime if uptime > 0 else 0
                }
            
            return metrics
    
    def reset(self):
        """Reset all metrics."""
        with self.lock:
            self.request_counts.clear()
            self.error_counts.clear()
            self.latencies.clear()
            self.start_time = time.time()


# Global metrics collector
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    return _metrics_collector


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request/response metrics."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        method = request.method
        
        try:
            response = await call_next(request)
            latency = time.time() - start_time
            
            # Record metrics
            _metrics_collector.record_request(path, method, response.status_code, latency)
            
            # Add latency header
            response.headers["X-Response-Time"] = f"{latency * 1000:.2f}ms"
            
            return response
        except Exception as e:
            latency = time.time() - start_time
            _metrics_collector.record_request(path, method, 500, latency)
            raise

