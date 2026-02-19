FROM python:3.11-slim AS base

# Install git (needed for gitpython to clone repos)
# Install Node.js 20 (needed to run JS/TS test suites like jest/vitest)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Create directories for repos and outputs
RUN mkdir -p /tmp/repos /app/outputs

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

# ── Test stage ──────────────────────────────────────────
FROM base AS test

COPY tests ./tests

CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
