# Multi-stage build for production-grade container
# Stage 1: Builder
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements file
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

# Install runtime dependencies and security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r prefect -g 1000 && \
    useradd -r -u 1000 -g prefect -m -s /bin/bash prefect && \
    mkdir -p /app /var/log/prefect && \
    chown -R prefect:prefect /app /var/log/prefect

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PREFECT_LOGGING_LEVEL=INFO \
    PREFECT_API_REQUEST_TIMEOUT=30 \
    PREFECT_API_RESPONSE_TIMEOUT=30

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=prefect:prefect . .

# Remove unnecessary files
RUN rm -rf .git .github .pytest_cache __pycache__ \
    && find . -type f -name "*.pyc" -delete \
    && find . -type d -name "__pycache__" -delete

# Create VERSION file
RUN echo "$(date +%Y%m%d.%H%M%S)" > VERSION

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Switch to non-root user
USER prefect

# Expose metrics port
EXPOSE 8000

# Default command
CMD ["python", "flow.py"]