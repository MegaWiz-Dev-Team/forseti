FROM python:3.12-slim

WORKDIR /app

# System deps for Playwright + curl (healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy everything first (hatchling needs README.md + src/)
COPY . .

# Install package + dashboard deps
RUN pip install --no-cache-dir . flask gunicorn

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Data directory for SQLite
RUN mkdir -p /app/data

# Expose dashboard + API
EXPOSE 5555

# Default: run dashboard
CMD ["python", "dashboard.py"]
