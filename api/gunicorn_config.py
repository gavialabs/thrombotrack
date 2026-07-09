# gunicorn_config.py

# ---------- Variables ----------
import os

# TODO: Read the CPU and memory units from env variables
# ECS Task CPU and Memory units
# cpu_units = 1024
# memory_mb = 2048
cpu_units = int(float(os.environ.get("API_RESOURCE_CPU_LIMIT_SIZE", 1)) * 1024)
memory_mb = int(os.environ.get("API_RESOURCE_MEMORY_LIMIT_MB", 1024))

vcpu = cpu_units // 1024
worker_count = (vcpu * 2) + 1
threads_per_worker = 4  # 2-4 is the recommended range

API_PORT = os.environ["API_PORT"]

# ---------- Variables for Gunicorn ----------
# Gunicorn config file documentation - https://gunicorn.org/reference/settings/#reload
bind = f"0.0.0.0:{API_PORT}"
workers = worker_count
threads = workers * threads_per_worker
timeout = 120
wsgi_app = "wsgi:app"
#reload = os.environ["FLASK_ENV"] == "development"
