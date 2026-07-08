# Use Python base image
FROM python:3.13-slim

# Build time arg
ARG API_PORT

# Set working directory
WORKDIR /thrombotrack-api

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
EXPOSE ${API_PORT}

# Define startup command
ENTRYPOINT ["./entrypoint.sh"]
