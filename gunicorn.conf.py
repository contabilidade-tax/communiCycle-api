import os
import multiprocessing

bind = "0.0.0.0:" + f"{os.environ.get('PORT', 8000)}"
workers = multiprocessing.cpu_count()
timeout = 120
keepalive = 180

