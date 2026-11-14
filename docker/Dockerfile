# Multi-stage build for production
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime image
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY app/ ./app/
COPY requirements.txt .

# Data volume mount point
RUN mkdir -p /data
VOLUME ["/data"]

ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/data
ENV REDIS_URL=redis://redis:6379

EXPOSE 8000

# Default command is the API; worker overrides it
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
