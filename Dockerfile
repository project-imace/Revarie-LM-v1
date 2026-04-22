FROM ubuntu:24.04 AS base
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV PATH="/usr/local/cargo/bin:${PATH}"

# Install system dependencies (Now including Boost for Crow)
RUN apt-get update && apt-get install -y \
    curl wget build-essential cmake pkg-config libssl-dev \
    libboost-all-dev \
    python3 python3-pip python3-venv sbcl nginx supervisor git \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

WORKDIR /app
COPY . .

# 4. Build the C++ Reasoner (System 2 Math)
# Now it will find Boost and compile Crow successfully
RUN mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)

# 5. Build the Rust API Gateway (Brain Stem)
RUN cargo build --release

# 6. Install Python dependencies and Namespace fix
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt
RUN pip3 install --break-system-packages -e .

# 7. Configure nginx and supervisord
COPY nginx.conf /etc/nginx/sites-available/default
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 7860
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
