# =============================================================================
# Dockerfile – REVARIE LM V1 Production (Project IMACE)
# =============================================================================

FROM ubuntu:24.04 AS base

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Set up paths for the Rust toolchain
ENV RUSTUP_HOME=/usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo
ENV PATH=$CARGO_HOME/bin:$PATH

# 1. Install System Dependencies (The Nervous System Core)
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

# 2. Install Rust Production Toolchain
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# 3. Prepare the Application Environment
WORKDIR /app
COPY . .

# 4. Build the C++ Reasoner (System 2 Math)
RUN mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)

# 5. Build the Rust API Gateway (Brain Stem)
RUN cargo build --release

# 6. Install Python Orchestrator (The CEO)
# We use the --break-system-packages flag for Ubuntu 24.04 compatibility
# and -e . to ensure your pyproject.toml maps the hyphenated folders correctly.
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt
RUN pip3 install --break-system-packages -e .

# 7. Configure Nginx Proxy
COPY nginx.conf /etc/nginx/sites-available/default
RUN ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

# 8. Configure Supervisor (The Heartbeat)
# Ensure this matches your deployment/docker/supervisord.conf path
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 9. Expose Hugging Face Standard Port
EXPOSE 7860

# 10. Launch the Integrated Architecture
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
