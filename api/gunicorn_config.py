# gunicorn_config.py
# TODO: Read the CPU and memory units from env variables
# ECS Task CPU and Memory units
cpu_units = 1024
memory_mb = 2048

vcpu = cpu_units // 1024
memory_gb = memory_mb // 1024
worker_count = (cpu_units * 2) + 1
threads_per_worker = 4  # 2-4 is the recommended range

bind = "0.0.0.0:5000"
workers = workers
threads = workers * threads_per_worker
timeout = 120

# TODO: Set reload option
# reload = os.environ["FLASK_ENV"] == "development"