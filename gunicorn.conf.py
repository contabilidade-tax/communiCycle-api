import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('API_PORT', os.environ.get('PORT', 8080))}"
workers = multiprocessing.cpu_count()
# worker_class = "gevent"
timeout = 120
keepalive = 180
