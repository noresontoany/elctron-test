from prometheus_client import Counter, Gauge, Histogram

HTTP_SECONDS = Histogram(
    "spoke_http_seconds",
    "HTTP response time",
    ["method", "route", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 15, 30, 65),
)
SYNC_ACTIVE = Gauge("spoke_sync_active", "Requests currently forwarded to Electric")
SYNC_WAITING = Gauge("spoke_sync_waiting", "Requests waiting for an upstream slot")
SYNC_WAIT = Histogram(
    "spoke_sync_wait_seconds",
    "Admission wait before Electric",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1),
)
SYNC_REJECTED = Counter("spoke_sync_rejected_total", "Rejected requests: no upstream slot")
SYNC_CANCELLED = Counter("spoke_sync_cancelled_total", "Disconnected clients: upstream cancelled")
SYNC_UPSTREAM = Histogram(
    "spoke_sync_upstream_seconds",
    "Electric response time including long polling",
    ["resource", "status"],
    buckets=(0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 15, 30, 65),
)
