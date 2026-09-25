# Autonomous AI Company - 24/7 Cloud Dockerfile (Phase 5B)
# Runs independently of the owner's laptop with persistent database and automated daily reporting.

FROM python:3.12-slim

# Prevent Python from writing pyc files and buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HOST=0.0.0.0

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure data and reports directories exist for persistent volume mounting
RUN mkdir -p /app/data /app/reports/daily /app/data/outbox

# Volume declarations to guarantee zero data loss
VOLUME ["/app/data", "/app/reports"]

# Expose HTTP port
EXPOSE 8000

# Healthcheck probe using the 9-component heartbeat endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/cloud/heartbeat || exit 1

# Start the unified 24/7 company server, scheduler, and worker
CMD ["python", "main.py"]
