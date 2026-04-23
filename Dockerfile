FROM ubuntu:24.04 AS base

# Prevent timezone and prompt hangs during apt-get
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# 1. Install system dependencies (ADDED cl-alexandria)
RUN apt-get update && apt-get install -y \
    curl wget build-essential cmake pkg-config libssl-dev \
    libboost-all-dev \
    python3 python3-pip python3-venv sbcl cl-alexandria nginx supervisor git \
    && rm -rf /var/lib/apt/lists/*

# 2. HUGGING FACE MANDATORY: Create User 1000
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

# SAFETY LINK: Connect /home/revarie/app to /app for legacy configs
USER root
RUN ln -s /home/revarie/app /app
USER revarie

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
RUN pip3 install --break-system-packages --no-cache-dir --user -e .

# 9. Configure Nginx and Supervisord (Using rigorous local paths)
COPY --chown=revarie:revarie nginx.conf ${HOME}/app/nginx.conf
COPY --chown=revarie:revarie supervisord.conf ${HOME}/app/supervisord.conf

# 10. Expose Hugging Face Port
EXPOSE 7860

# Boot using the local config file
CMD ["/usr/bin/supervisord", "-n", "-c", "/home/revarie/app/supervisord.conf"]
