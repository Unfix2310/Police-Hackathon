#!/bin/bash
set -e

echo "=== Gujarat CCTV Intelligence Platform - Setup ==="
echo ""

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker is required but not installed."; exit 1; }
command -v docker compose >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1 || { echo "ERROR: Docker Compose is required."; exit 1; }

echo "✓ Docker found"

# Create required directories
echo "Creating directories..."
mkdir -p data/{recordings,models,frames,seed,maps}

# Copy env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env from .env.example"
else
    echo "✓ .env already exists"
fi

# Download AI models (YOLOv8)
echo ""
echo "Downloading AI models..."
if [ ! -f data/models/yolov8m.pt ]; then
    pip3 install ultralytics -q 2>/dev/null || true
    python3 -c "from ultralytics import YOLO; YOLO('yolov8m.pt')" 2>/dev/null && \
    mv yolov8m.pt data/models/ 2>/dev/null || \
    echo "⚠ YOLOv8 model download skipped (will download on first run)"
else
    echo "✓ YOLOv8 model already exists"
fi

# Build and start services
echo ""
echo "Building and starting services..."
docker compose up --build -d

echo ""
echo "=== Setup Complete ==="
echo "  Backend API:  http://localhost:8000"
echo "  Frontend:     http://localhost:3000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  PostgreSQL:   localhost:5432"
echo "  Redis:        localhost:6379"
echo ""
echo "Default credentials:"
echo "  operator1    / operator123"
echo "  investigator1 / investigator123"
echo "  command1     / command123"
echo "  admin1       / admin123"
