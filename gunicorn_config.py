"""
Fleet Management System — Gunicorn Production Configuration

Usage:
    gunicorn main:app -c gunicorn_config.py
"""

import os
import multiprocessing

# ── Server Socket ────────────────────────────────────────────
bind = f"{os.getenv('API_HOST', '0.0.0.0')}:{os.getenv('API_PORT', '8000')}"
backlog = 2048

# ── Worker Processes ─────────────────────────────────────────
# Formula: (2 * CPU cores) + 1 for I/O-bound applications
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 5000            # Restart workers after N requests (prevent memory leaks)
max_requests_jitter = 500      # Random jitter to prevent all workers restarting at once

# ── Timeouts ─────────────────────────────────────────────────
timeout = 120                  # Worker timeout (seconds)
graceful_timeout = 30          # Graceful shutdown timeout
keepalive = 5                  # Keep-alive connections timeout

# ── Logging ──────────────────────────────────────────────────
accesslog = "-"                # Access log to stdout
errorlog = "-"                 # Error log to stderr
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sμs'

# ── Process Naming ───────────────────────────────────────────
proc_name = "fleet-management"

# ── Security ─────────────────────────────────────────────────
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# ── Server Hooks ─────────────────────────────────────────────
def on_starting(server):
    """Called just before the master process is initialized."""
    print("=" * 60)
    print("  Fleet Management System — Production Server Starting")
    print(f"  Workers: {workers}")
    print(f"  Bind: {bind}")
    print("=" * 60)


def on_reload(server):
    """Called to recycle workers during a reload."""
    print("♻  Reloading Fleet Management workers...")


def worker_int(worker):
    """Called when a worker receives SIGINT."""
    print(f"⚠  Worker {worker.pid} interrupted")


def worker_abort(worker):
    """Called when a worker receives SIGABRT."""
    print(f"❌ Worker {worker.pid} aborted")
