# 7. Docker & Deployment Configuration

## 1. Overview and Service Topology

This document outlines the deployment configuration for the Gujarat CCTV Intelligence Platform Hackathon MVP. 

```mermaid
graph TD
    User([User / Investigator]) -->|HTTPS:80/443| Nginx[Nginx Reverse Proxy]
    
    Nginx -->|:80| Frontend[Frontend: React + Leaflet]
    Nginx -->|:8000| Backend[Backend: FastAPI]
    
    Backend -->|:5432| Postgres[(PostgreSQL + PostGIS)]
    Backend -->|:6379| Redis[(Redis Pub/Sub & Cache)]
    Backend -->|Volumes| Files[Recordings & Models]
    
    Processor[AI Processor Worker] -->|:5432| Postgres
    Processor -->|:6379| Redis
    Processor -->|Volumes| Files
```

## 2. Resource Requirements (Hackathon MVP)

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **CPU** | 4 Cores | 8+ Cores | Required for parallel processing if GPU unavailable. |
| **RAM** | 16 GB | 32 GB | FAISS, NetworkX, and AI models reside in memory. |
| **Disk** | 50 GB | 100 GB SSD | PostgreSQL data, model weights, and video recordings. |
| **GPU** | Optional | NVIDIA 8GB+ VRAM | Enables real-time processing (YOLOv8, RT-DETR). |
| **OS** | Linux/macOS | Ubuntu 22.04 | Native Docker support with NVIDIA Container Toolkit. |

## 3. Port Mapping Table

| Service | Container Port | Host Port | Protocol | Purpose |
|---------|----------------|-----------|----------|---------|
| Frontend | 80 | 3000 | HTTP | React UI access |
| Backend | 8000 | 8000 | HTTP | FastAPI REST API endpoints |
| Postgres | 5432 | 5432 | TCP | Direct DB access (development) |
| Redis | 6379 | 6379 | TCP | Direct Redis access (development) |
| Nginx | 80 | 8080 | HTTP | Production-like unified access |

## 4. Volume Mapping Table

| Volume Name / Path | Container Mount Path | Purpose |
|--------------------|----------------------|---------|
| `postgres_data` | `/var/lib/postgresql/data` | Persists relational data (Entities, Ops, Cases) |
| `redis_data` | `/data` | Persists Redis snapshot data |
| `./data/recordings` | `/app/data/recordings` | Stores 50 test CCTV video files |
| `./data/models` | `/app/data/models` | AI model weights (YOLO, PaddleOCR) |
| `./data/frames` | `/app/data/frames` | Processed keyframes and object crops |

## 5. `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:16-3.4
    container_name: cctv_postgres
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER:-cctv_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-cctv_pass}
      POSTGRES_DB: ${DB_NAME:-cctv_db}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/01_init.sql:/docker-entrypoint-initdb.d/01_init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cctv_user -d cctv_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: cctv_redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: cctv_backend
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://cctv_user:cctv_pass@postgres:5432/cctv_db
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=${JWT_SECRET:-hackathon_secret}
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - RECORDINGS_PATH=/app/data/recordings
      - MODELS_PATH=/app/data/models
      - FRAMES_OUTPUT_PATH=/app/data/frames
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=http://localhost:3000,http://localhost:8080
    ports:
      - "8000:8000"
    volumes:
      - ./data/recordings:/app/data/recordings
      - ./data/models:/app/data/models
      - ./data/frames:/app/data/frames
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  processor:
    build:
      context: ./processor
      dockerfile: Dockerfile
    container_name: cctv_processor
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://cctv_user:cctv_pass@postgres:5432/cctv_db
      - REDIS_URL=redis://redis:6379/0
      - DETECTION_CONFIDENCE_THRESHOLD=${DETECTION_CONFIDENCE_THRESHOLD:-0.6}
      - ANPR_CONFIDENCE_THRESHOLD=${ANPR_CONFIDENCE_THRESHOLD:-0.7}
      - FRAME_SAMPLE_RATE=${FRAME_SAMPLE_RATE:-1}
      - RECORDINGS_PATH=/app/data/recordings
      - MODELS_PATH=/app/data/models
      - FRAMES_OUTPUT_PATH=/app/data/frames
    volumes:
      - ./data/recordings:/app/data/recordings
      - ./data/models:/app/data/models
      - ./data/frames:/app/data/frames
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: cctv_frontend
    restart: always
    depends_on:
      - backend
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  nginx:
    image: nginx:alpine
    container_name: cctv_nginx
    restart: always
    ports:
      - "8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
  redis_data:
```

## 6. `.env.example`

```env
# Database Config
DB_USER=cctv_user
DB_PASSWORD=cctv_pass
DB_NAME=cctv_db
DATABASE_URL=postgresql://cctv_user:cctv_pass@postgres:5432/cctv_db

# Redis Config
REDIS_URL=redis://redis:6379/0

# Backend Config
JWT_SECRET=super_secret_jwt_key_hackathon
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
LOG_LEVEL=INFO

# AI Processing Config
DETECTION_CONFIDENCE_THRESHOLD=0.6
ANPR_CONFIDENCE_THRESHOLD=0.7
FRAME_SAMPLE_RATE=1

# Volume Paths (Inside container)
RECORDINGS_PATH=/app/data/recordings
MODELS_PATH=/app/data/models
FRAMES_OUTPUT_PATH=/app/data/frames
```

## 7. Dockerfiles

### 7.1 `backend/Dockerfile`

```dockerfile
# Multi-stage build for FastAPI backend
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY src/ ./src/

# Run the FastAPI app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 `frontend/Dockerfile`

```dockerfile
# Build stage
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
# Custom nginx config if needed for React router fallback
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 7.3 `processor/Dockerfile`

```dockerfile
# Base image with CUDA support
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Install Python 3.11 and dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY src/ ./src/

CMD ["python3", "src/worker.py"]
```

## 8. Database Initialization (`scripts/01_init.sql`)

```sql
-- Enable PostGIS extension for spatial queries
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Base schemas
CREATE TABLE cameras (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cam_id VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    location GEOMETRY(Point, 4326),
    status VARCHAR(50) DEFAULT 'ONLINE'
);

-- Note: Actual schema source logic and seed data generation will go here
-- \i schema.sql;
-- \i seed.sql;
```

## 9. Setup Script (`scripts/setup.sh`)

```bash
#!/bin/bash
set -e

echo "Setting up Gujarat CCTV Intelligence Platform (MVP)..."

# 1. Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "Docker could not be found. Please install Docker."
    exit 1
fi

# 2. Create required directories
mkdir -p data/recordings data/models data/frames
mkdir -p postgres_data redis_data

# 3. Setup environment variables
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

# 4. Download AI Models (Placeholder for actual download commands)
echo "Downloading AI models..."
# curl -o data/models/yolov8n.pt https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

# 5. Build and start containers
echo "Starting Docker Compose..."
docker-compose up --build -d

echo "Setup complete! Services should be coming online."
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
```

## 10. GPU Configuration Notes

To utilize GPU passthrough for the AI processor:
1. Ensure NVIDIA drivers are installed on the host.
2. Install the **NVIDIA Container Toolkit**.
3. In `docker-compose.yml`, the `deploy.resources.reservations.devices` block ensures the `processor` container can access the GPU.
4. The `processor/Dockerfile` uses `nvidia/cuda:11.8.0-runtime-ubuntu22.04` as its base to have proper CUDA libraries.
If running without a GPU, remove the `deploy` block from the `processor` service in `docker-compose.yml` and replace the base image in `processor/Dockerfile` with a standard Python slim image.
