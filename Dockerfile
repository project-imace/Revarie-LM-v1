# =============================================================================
# Dockerfile – Revarie LM v1.0 Multi‑Service Cognitive Architecture
# =============================================================================
# Builds a single container running Rust, C++, Python, and Lisp services
# managed by supervisord and exposed via nginx on port 7860.
# =============================================================================

FROM ubuntu:24.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV RUSTUP_HOME=/usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo
ENV PATH=$CARGO_HOME/bin:$PATH

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    build-essential \
    cmake \
    pkg-config \
    libssl-dev \
    python3 \
    python3-pip \
    python3-venv \
    sbcl \
    nginx \
    supervisor \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --break-system-packages --no-cache-dir -r /tmp/requirements.txt

# Create app directory
WORKDIR /app

# Copy source code
COPY . .

# Build Rust services
RUN cargo build --release

# Build C++ services
RUN mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)

# Configure nginx
COPY deployment/docker/nginx.conf /etc/nginx/sites-available/default
RUN ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

# Configure supervisord
COPY deployment/docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose HF Spaces standard port
EXPOSE 7860

# Start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
