FROM ubuntu:24.04 AS base

# Prevent timezone and prompt hangs
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# 1. Install system dependencies (Removed cl-alexandria, we will use Quicklisp instead)
RUN apt-get update && apt-get install -y \
    curl wget build-essential cmake pkg-config libssl-dev \
    libboost-all-dev \
    python3 python3-pip python3-venv sbcl nginx supervisor git \
    && rm -rf /var/lib/apt/lists/*

# 2. HUGGING FACE MANDATORY: Create User 1000
RUN userdel -r ubuntu || true
RUN useradd -m -u 1000 revarie
ENV HOME=/home/revarie
ENV PATH="${HOME}/.local/bin:${HOME}/.cargo/bin:${PATH}"

# Switch to root temporarily for logging permissions
USER root
RUN mkdir -p /var/log/nginx /var/lib/nginx /var/log/supervisor /var/run/supervisor /tmp/nginx \
    && chown -R 1000:1000 /var/log/nginx /var/lib/nginx /var/log/supervisor /var/run/supervisor /etc/nginx /etc/supervisor /tmp/nginx

# Switch safely to User 1000
USER revarie
WORKDIR ${HOME}/app

# SAFETY LINK: Connect /home/revarie/app to /app
USER root
RUN ln -s /home/revarie/app /app
USER revarie

# 3. Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# 4. THE FORGE: Install Quicklisp for Common Lisp dependencies
RUN curl -O https://beta.quicklisp.org/quicklisp.lisp && \
    sbcl --non-interactive --load quicklisp.lisp --eval "(quicklisp-quickstart:install)" && \
    echo '#-quicklisp (let ((quicklisp-init (merge-pathnames "quicklisp/setup.lisp" (user-homedir-pathname)))) (when (probe-file quicklisp-init) (load quicklisp-init)))' >> ${HOME}/.sbclrc && \
    rm quicklisp.lisp

# Pre-cache Lisp Libraries (Downloads Alexandria and Serapeum instantly)
RUN sbcl --non-interactive --eval "(ql:quickload :alexandria)" --eval "(ql:quickload :serapeum)"

# 5. FAST CACHE: Python requirements
COPY --chown=revarie:revarie requirements.txt ./
RUN pip3 install --break-system-packages --no-cache-dir --user -r requirements.txt

# 6. Copy architecture
COPY --chown=revarie:revarie . .

# 7. Build C++ Reasoner
RUN mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)

# 8. Build Rust API Gateway
RUN cargo build --release

# 9. Python namespace fix
RUN pip3 install --break-system-packages --no-cache-dir --user -e .

# 10. Configs
COPY --chown=revarie:revarie nginx.conf ${HOME}/app/nginx.conf
COPY --chown=revarie:revarie supervisord.conf ${HOME}/app/supervisord.conf

EXPOSE 7860

# Boot using the local config file
CMD ["/usr/bin/supervisord", "-n", "-c", "/home/revarie/app/supervisord.conf"]
