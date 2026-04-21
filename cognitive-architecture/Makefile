# REVARIE Cognitive Architecture - Unified Makefile
# Orchestrates builds across C++, Rust, Python, and Lisp.

.PHONY: all clean test test-cpp test-rust test-python test-lisp build

# Directories
CPP_BUILD_DIR = build
RUST_TARGET_DIR = target
PYTHON_VENV = .venv

all: build

# ------------------------------------------------------------------------------
# C++ Build
# ------------------------------------------------------------------------------
build-cpp:
	@echo "Building C++ modules..."
	mkdir -p $(CPP_BUILD_DIR)
	cd $(CPP_BUILD_DIR) && cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=ON
	cd $(CPP_BUILD_DIR) && make -j$(nproc)

clean-cpp:
	rm -rf $(CPP_BUILD_DIR)

test-cpp: build-cpp
	@echo "Running C++ tests..."
	cd $(CPP_BUILD_DIR) && ctest --output-on-failure

# ------------------------------------------------------------------------------
# Rust Build
# ------------------------------------------------------------------------------
build-rust:
	@echo "Building Rust modules..."
	cargo build --release

clean-rust:
	cargo clean

test-rust:
	@echo "Running Rust tests..."
	cargo test --release

# ------------------------------------------------------------------------------
# Python Setup
# ------------------------------------------------------------------------------
venv:
	@echo "Creating Python virtual environment..."
	python3 -m venv $(PYTHON_VENV)
	. $(PYTHON_VENV)/bin/activate && pip install --upgrade pip
	. $(PYTHON_VENV)/bin/activate && pip install -r requirements.txt
	. $(PYTHON_VENV)/bin/activate && pip install -r requirements-dev.txt

clean-python:
	rm -rf $(PYTHON_VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

test-python: venv
	@echo "Running Python tests..."
	. $(PYTHON_VENV)/bin/activate && pytest tests/ -v

# ------------------------------------------------------------------------------
# Lisp Setup
# ------------------------------------------------------------------------------
test-lisp:
	@echo "Running Lisp tests..."
	sbcl --eval "(require :asdf)" \
	     --eval "(asdf:load-system :revarie-cognitive-architecture/tests)" \
	     --eval "(asdf:test-system :revarie-cognitive-architecture/tests)" \
	     --eval "(quit)"

# ------------------------------------------------------------------------------
# Combined Targets
# ------------------------------------------------------------------------------
build: build-cpp build-rust venv
	@echo "All modules built successfully."

test: test-cpp test-rust test-python test-lisp
	@echo "All tests passed."

clean: clean-cpp clean-rust clean-python
	@echo "Clean complete."

# ------------------------------------------------------------------------------
# Help
# ------------------------------------------------------------------------------
help:
	@echo "Available targets:"
	@echo "  all          - Build all modules (default)"
	@echo "  build        - Build C++, Rust, and Python modules"
	@echo "  build-cpp    - Build C++ modules only"
	@echo "  build-rust   - Build Rust modules only"
	@echo "  venv         - Create Python virtual environment"
	@echo "  test         - Run all tests"
	@echo "  test-cpp     - Run C++ tests only"
	@echo "  test-rust    - Run Rust tests only"
	@echo "  test-python  - Run Python tests only"
	@echo "  test-lisp    - Run Lisp tests only"
	@echo "  clean        - Clean all build artifacts"
	@echo "  clean-cpp    - Clean C++ build artifacts"
	@echo "  clean-rust   - Clean Rust build artifacts"
	@echo "  clean-python - Clean Python artifacts"
