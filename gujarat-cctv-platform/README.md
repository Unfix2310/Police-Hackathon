# Gujarat CCTV Intelligence Platform — Hackathon MVP

> A statewide CCTV intelligence ecosystem for Gujarat Police.  
> Turns raw camera feeds into actionable investigation intelligence.

## Quick Start

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## Architecture

```
Camera Feeds → AI Detection → Observations → Entity Resolution → Correlation → Investigation Graph → Evidence
```

**Tech Stack**: Python/FastAPI · PostgreSQL/PostGIS · Redis · YOLOv8 · PaddleOCR · React · Leaflet · Docker

## Services

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | React dashboards (Operator / Investigator / Command) |
| Backend API | http://localhost:8000 | FastAPI REST + WebSocket |
| API Docs | http://localhost:8000/docs | Swagger UI |
| PostgreSQL | localhost:5432 | Data store with PostGIS |
| Redis | localhost:6379 | Pub/sub + cache |

## Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Operator | operator1 | operator123 |
| Investigator | investigator1 | investigator123 |
| Command | command1 | command123 |
| Admin | admin1 | admin123 |

## Documentation

See `/docs/` for complete technical specifications.
