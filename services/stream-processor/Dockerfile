# -------------------------
# Builder stage
# -------------------------
FROM python:3.13.7-alpine3.22 AS builder

WORKDIR /app

# Upgrade pip/setuptools/wheel first
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# -------------------------
# Runtime stage (Distroless)
# -------------------------
FROM gcr.io/distroless/python3:nonroot

# Set working directory
WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application
COPY --from=builder /app /app

# Set non-root user (distroless already runs as non-root)
USER nonroot

# Expose port if needed (for uvicorn or HTTP server)
EXPOSE 8000

# Run your application
CMD ["python3", "/app/stream_processor.py"]
