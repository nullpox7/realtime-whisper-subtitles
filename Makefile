# Real-time Whisper Subtitles - Makefile

.PHONY: help build up down logs clean install dev test format lint

# Default target
help:
	@echo "Real-time Whisper Subtitles - Available commands:"
	@echo ""
	@echo "  build    - Build Docker images (GPU version)"
	@echo "  up       - Start the application with Docker Compose (GPU)"
	@echo "  up-cpu   - Start the application (CPU-only version)"
	@echo "  down     - Stop and remove containers"
	@echo "  logs     - Show application logs"
	@echo "  clean    - Clean up Docker resources"
	@echo "  install  - Install Python dependencies locally"
	@echo "  dev      - Start development server locally"
	@echo "  test     - Run tests"
	@echo "  format   - Format code with black"
	@echo "  lint     - Run code linting"
	@echo "  gpu      - Check GPU status"
	@echo "  dirs     - Create necessary directories"
	@echo ""

# Docker commands
build:
	@echo "Building Docker images (GPU version)..."
	docker-compose build

build-cpu:
	@echo "Building Docker images (CPU version)..."
	docker-compose -f docker-compose.cpu.yml build

up: dirs
	@echo "Starting Real-time Whisper Subtitles (GPU version)..."
	docker-compose up -d
	@echo "Application started at http://localhost:8000"

up-cpu: dirs
	@echo "Starting Real-time Whisper Subtitles (CPU version)..."
	docker-compose -f docker-compose.cpu.yml up -d
	@echo "CPU-only application started at http://localhost:8000"

down:
	@echo "Stopping application..."
	docker-compose down
	docker-compose -f docker-compose.cpu.yml down

logs:
	@echo "Showing application logs..."
	docker-compose logs -f

logs-cpu:
	@echo "Showing CPU application logs..."
	docker-compose -f docker-compose.cpu.yml logs -f

clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker-compose -f docker-compose.cpu.yml down -v --remove-orphans
	docker system prune -f

# Local development
install:
	@echo "Installing Python dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt

install-cpu:
	@echo "Installing CPU-only Python dependencies..."
	pip install --upgrade pip
	pip install -r requirements-cpu.txt

dev:
	@echo "Starting development server..."
	python src/web_interface.py

# Code quality
test:
	@echo "Running tests..."
	python test_system.py
	pytest tests/ -v

format:
	@echo "Formatting code with black..."
	black src/
	black tests/ --exclude="tests/data"

lint:
	@echo "Running code linting..."
	flake8 src/
	flake8 tests/

# Utility commands
gpu:
	@echo "Checking GPU status..."
	@if command -v nvidia-smi >/dev/null 2>&1; then \
		nvidia-smi; \
	else \
		echo "nvidia-smi not found. Is NVIDIA driver installed?"; \
	fi

dirs:
	@echo "Creating necessary directories..."
	@mkdir -p outputs models static/css static/js templates

# Development workflow
setup: dirs install
	@echo "Setting up development environment..."
	@echo "Development setup complete!"

setup-cpu: dirs install-cpu
	@echo "Setting up CPU-only development environment..."
	@echo "CPU-only development setup complete!"

start: up
	@echo "Application is starting..."
	@sleep 3
	@echo "Opening browser..."
	@if command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:8000; \
	elif command -v open >/dev/null 2>&1; then \
		open http://localhost:8000; \
	else \
		echo "Please open http://localhost:8000 in your browser"; \
	fi

start-cpu: up-cpu
	@echo "CPU-only application is starting..."
	@sleep 3
	@echo "Opening browser..."
	@if command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:8000; \
	elif command -v open >/dev/null 2>&1; then \
		open http://localhost:8000; \
	else \
		echo "Please open http://localhost:8000 in your browser"; \
	fi

# Monitoring
status:
	@echo "Checking application status..."
	@docker-compose ps

status-cpu:
	@echo "Checking CPU application status..."
	@docker-compose -f docker-compose.cpu.yml ps

restart: down up
	@echo "Application restarted"

restart-cpu: down up-cpu
	@echo "CPU application restarted"

# Data management
backup:
	@echo "Creating backup of outputs..."
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	tar -czf "backup_outputs_$$timestamp.tar.gz" outputs/
	@echo "Backup created: backup_outputs_*.tar.gz"

clear-outputs:
	@echo "Clearing output files..."
	@read -p "Are you sure you want to delete all output files? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		rm -rf outputs/*; \
		echo "Output files cleared"; \
	else \
		echo "Operation cancelled"; \
	fi

# Model management
download-models:
	@echo "Pre-downloading Whisper models..."
	@echo "This may take a while..."
	docker-compose run --rm whisper-subtitles python -c "\
	from faster_whisper import WhisperModel; \
	models = ['tiny', 'base', 'small']; \
	[WhisperModel(m, device='cpu') for m in models]; \
	print('Models downloaded successfully')"

download-models-cpu:
	@echo "Pre-downloading Whisper models (CPU)..."
	@echo "This may take a while..."
	docker-compose -f docker-compose.cpu.yml run --rm whisper-subtitles-cpu python -c "\
	from faster_whisper import WhisperModel; \
	models = ['tiny', 'base', 'small']; \
	[WhisperModel(m, device='cpu') for m in models]; \
	print('Models downloaded successfully')"

# Production deployment
prod-up:
	@echo "Starting production deployment..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down:
	@echo "Stopping production deployment..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Health check
health:
	@echo "Checking application health..."
	@curl -f http://localhost:8000/api/status || echo "Application not responding"

# Quick commands
quick-start: build up
	@echo "Quick start completed!"

quick-start-cpu: build-cpu up-cpu
	@echo "CPU quick start completed!"

quick-stop: down clean
	@echo "Quick stop completed!"

# Documentation
docs:
	@echo "Opening documentation..."
	@if command -v xdg-open >/dev/null 2>&1; then \
		xdg-open README.md; \
	elif command -v open >/dev/null 2>&1; then \
		open README.md; \
	else \
		echo "Please read README.md for documentation"; \
	fi

# Troubleshooting
fix-cuda:
	@echo "Trying to fix CUDA issues..."
	@echo "Switching to CUDA 11.8 version..."
	@sed -i 's/cuda:12.2-devel/cuda:11.8-devel/g' Dockerfile
	@echo "CUDA version changed. Try: make build up"

fix-cpu:
	@echo "Switching to CPU-only mode..."
	@echo "Use: make up-cpu"