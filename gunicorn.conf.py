"""Gunicorn configuration for the Curated Travel Platform."""

import multiprocessing

# Server socket
bind = "0.0.0.0:5000"

# Worker processes (2 * CPU cores + 1)
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = "sync"

# Timeout for worker processes (seconds)
timeout = 120

# Graceful timeout for worker restart
graceful_timeout = 30

# Maximum requests per worker before recycling (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "travel_platform"

# Preload app for faster worker startup
preload_app = True
