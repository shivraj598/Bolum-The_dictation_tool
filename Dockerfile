# Bolum - Docker Build for Rust/whisper.cpp backend
# Note: MLX/Parakeet requires macOS Apple Silicon (Metal) - cannot run in Linux Docker
# This Dockerfile builds the Rust CLI version for Linux deployment

FROM rust:1.78-slim as builder

# Install system dependencies for whisper.cpp and audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    libasound2-dev \
    libpulse-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Cargo files first for caching
COPY Cargo.toml Cargo.lock* ./

# Create dummy src to cache dependencies
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release 2>&1 | tail -20

# Copy actual source
COPY src/ ./src/

# Build release binary
RUN cargo build --release --bin bolum

# ==========================================
# Runtime stage - minimal
# ==========================================
FROM debian:12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libasound2 \
    libpulse0 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash bolum

# Copy binary
COPY --from=builder /app/target/release/bolum /usr/local/bin/bolum

# Create models directory
RUN mkdir -p /home/bolum/.local/share/bolum/models && chown -R bolum:bolum /home/bolum

USER bolum
WORKDIR /home/bolum

# Default command shows help
ENTRYPOINT ["bolum"]
CMD ["--help"]