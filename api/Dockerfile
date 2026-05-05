# Use Python base image
FROM python:3.13-slim

# Set working directory
WORKDIR /ecmo-api

# Install system dependencies for PostgreSQL and psycopg2
RUN apt-get update -y && apt-get install -y postgresql-client

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy and set entrypoint script permissions
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Expose port for Flask
EXPOSE ${APP_PORT:-5000}

# Define startup command
ENTRYPOINT ["./entrypoint.sh"]