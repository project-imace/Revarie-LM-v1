FROM ubuntu:24.04 AS base

# Prevent timezone and prompt hangs during apt-get
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# 1. Install system dependencies (Docker caches this heavily)
RUN apt-get update && apt-get install -y \
    curl wget build-essential cmake pkg-config libssl-dev \
    libboost-all-dev \
    python3 python3-pip python3-venv sbcl nginx supervisor git \
    && rm -rf /var/lib/apt/lists/*

# 2. HUGGING FACE MANDATORY: Create User 1000
# Ubuntu 24.04 ships with a default 'ubuntu' user at UID 1000. We must delete it first.
RUN userdel -r ubuntu || true
RUN useradd -m -u 1000 revarie
ENV HOME=/home/revarie
ENV PATH="${HOME}/.local/bin:${HOME}/.cargo/bin:${PATH}"

# Switch to root temporarily to set up logging permissions for Nginx/Supervisor
USER root
RUN mkdir -p /var/log/nginx /var/lib/nginx /var/log/supervisor /var/run/supervisor /tmp/nginx \
    && chown -R 1000:1000 /var/log/nginx /var/lib/nginx /var/log/supervisor /var/run/supervisor /etc/nginx /etc/supervisor /tmp/nginx

# Switch safely to User 1000
USER revarie
WORKDIR ${HOME}/app

# 3. Install Rust specifically for User 1000
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# 4. FAST CACHE: Copy requirements first so pip doesn't rebuild when C++ changes
COPY --chown=revarie:revarie requirements.txt ./
# FIX: Added --break-system-packages to bypass PEP 668 in Ubuntu 24.04
RUN pip3 install --break-system-packages --no-cache-dir --user -r requirements.txt

# 5. Copy the rest of the architecture
COPY --chown=revarie:revarie . .

# 6. Build the C++ Reasoner (System 2 Math)
RUN mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)

# 7. Build the Rust API Gateway (Brain Stem)
RUN cargo build --release

# 8. Install Python Namespace fix
# FIX: Added --break-system-packages here as well
RUN pip3 install --break-system-packages --no-cache-dir --user -e .

# 9. Configure Nginx and Supervisord
COPY --chown=revarie:revarie nginx.conf /etc/nginx/sites-available/default
COPY --chown=revarie:revarie supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 10. Expose Hugging Face Port
EXPOSE 7860

# Boot
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
