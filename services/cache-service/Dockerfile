#–– Planner: cache dependency resolution ––
FROM rust:slim-trixie AS planner
WORKDIR /app

# 1) Copy just the manifest so Docker can cache this layer
COPY Cargo.toml ./

# 2) Create a dummy main.rs so Cargo sees a binary
RUN mkdir src \
 && echo "fn main() {}" > src/main.rs

# 3) Generate Cargo.lock and pre-fetch deps
RUN cargo generate-lockfile \
 && cargo fetch

# 4) Clean up dummy sources
RUN rm -rf src

#–– Builder: compile your real code ––
FROM rust:slim-trixie AS builder
WORKDIR /app

# 5) Bring in lockfile + manifest from planner
COPY --from=planner /app/Cargo.toml /app/Cargo.lock ./

# 6) Copy your actual source tree
COPY src ./src

# 7) Produce optimized binary
RUN cargo build --release

#–– Runtime: slim production image ––
FROM debian:trixie-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
  && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1001 appuser

# Copy the compiled binary
COPY --from=builder /app/target/release/cache-service /app/cache-service

# Fix permissions & switch user
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8082
ENV RUST_LOG=info \
    CACHE_SERVICE_HOST=0.0.0.0 \
    CACHE_SERVICE_PORT=8082

CMD ["./cache-service"]
