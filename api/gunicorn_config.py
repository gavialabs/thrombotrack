# gunicorn_config.py
import os

# ---------- Variables ----------
# ECS Task CPU and Memory units
cpu_units = int(os.environ.get("API_RESOURCE_CPU_LIMIT_UNIT", 2048))
memory_mb = int(os.environ.get("API_RESOURCE_MEMORY_LIMIT_MB", 4096))
worker_per_vcpu = int(os.environ.get("API_RESOURCE_WORKER_PER_VCPU", 2))
thread_per_worker = int(os.environ.get("API_RESOURCE_THREAD_PER_WORKER", 4))
api_port = os.environ["API_PORT"]

# ---------- Variable calculations
vcpu = int(cpu_units // 1024)
worker_count = int((vcpu * worker_per_vcpu) + 1)
threads = worker_count * thread_per_worker

# ---------- Variables for Gunicorn ----------
# Gunicorn config file documentation - https://gunicorn.org/reference/settings/#reload
bind = f"0.0.0.0:{api_port}"
workers = worker_count
threads=threads
timeout = 120
wsgi_app = "wsgi:app"
#reload = os.environ["FLASK_ENV"] == "development"
