# Project Structure & Module Design

This document defines the complete project structure and module design for the Gujarat CCTV Intelligence Platform Hackathon MVP. It is designed to strictly align with the Five-Plane architecture (Physical/Data, Integration, Intelligence, Investigation & Ops, Application) and the technology choices specified in §54.3.

## 1. Directory Structure

```text
gujarat-cctv-platform/
├── docker-compose.yml
├── .env.example
├── README.md
├── docs/
├── backend/
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/          (SQLAlchemy + Pydantic)
│   ├── api/             (FastAPI routers per domain)
│   ├── services/        (business logic)
│   ├── ai/              (detection, tracking, ANPR, features)
│   ├── engine/          (entity resolution, correlation, feasibility, graph)
│   ├── evidence/        (evidence package generation)
│   └── simulator/       (camera simulator from recordings)
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── utils/
├── data/
│   ├── recordings/      (50 test video files)
│   ├── seed/            (seed SQL, sample data)
│   └── maps/            (Gujarat GeoJSON)
└── scripts/
    ├── setup.sh
    ├── seed_db.sh
    └── process_recordings.py
```

---

## 2. Backend Module Details

### `backend/main.py`
- **Purpose**: Entry point for the FastAPI application. Sets up middleware, includes routers, and handles startup/shutdown events.
- **Key classes/functions**: `app` (FastAPI instance), `lifespan` (for DB/Redis startup).
- **Dependencies**: `config`, `database`, `api.*`
- **External dependencies**: `fastapi`, `uvicorn`, `starlette`

### `backend/config.py`
- **Purpose**: Centralized configuration management using Pydantic BaseSettings. Loads variables from `.env`.
- **Key classes/functions**: `Settings` class.
- **Dependencies**: None.
- **External dependencies**: `pydantic-settings`

### `backend/database.py`
- **Purpose**: Database connection management and session generation.
- **Key classes/functions**: `engine`, `SessionLocal`, `get_db()`.
- **Dependencies**: `config`.
- **External dependencies**: `sqlalchemy`

### `backend/models/`
- **Purpose**: Defines database schemas (SQLAlchemy) and API schemas (Pydantic). Contains canonical models (Camera, Observation, Person, Vehicle, Incident, Case).
- **Key classes/functions**: `Base` (Declarative), `CameraModel`, `ObservationModel`, `ObservationCreate` (Pydantic), `CameraResponse`.
- **Dependencies**: `database`.
- **External dependencies**: `sqlalchemy`, `pydantic`

### `backend/api/`
- **Purpose**: API controllers/routers grouped by domain (e.g., `cameras.py`, `observations.py`, `intelligence.py`, `cases.py`).
- **Key classes/functions**: `router` instances per file. Endpoint functions like `get_cameras`, `search_observations`.
- **Dependencies**: `models.*`, `services.*`, `engine.*`.
- **External dependencies**: `fastapi`

### `backend/services/`
- **Purpose**: Core business logic separating API routing from operations (CRUD operations, RBAC enforcement, dispatch logic).
- **Key classes/functions**: `CameraService`, `CaseService`, `AuthService`.
- **Dependencies**: `models.*`, `database`.
- **External dependencies**: `passlib`, `python-jose`

### `backend/ai/`
- **Purpose**: Wraps AI perception capabilities simulating the Edge processing and Intelligence plane.
- **Key classes/functions**: `Detector` (YOLO wrapper), `ANPRProcessor` (PaddleOCR wrapper), `FeatureExtractor`.
- **Dependencies**: `config`, `models.ObservationCreate`.
- **External dependencies**: `ultralytics`, `paddleocr`, `paddlepaddle`, `opencv-python`, `numpy`, `pillow`

### `backend/engine/`
- **Purpose**: Complex analytics representing the Intelligence and Investigation planes (correlation, feasibility scoring, graph construction).
- **Key classes/functions**: `CorrelationEngine`, `FeasibilityScorer` (calculates speed/time plausibility), `GraphBuilder` (NetworkX graph).
- **Dependencies**: `models.*`, `database`.
- **External dependencies**: `networkx`, `faiss-cpu`, `shapely`, `geopy`

### `backend/evidence/`
- **Purpose**: Generates evidence packages with full provenance and Section 65B metadata.
- **Key classes/functions**: `EvidenceGenerator`, `HashCalculator`.
- **Dependencies**: `models.*`, `database`.
- **External dependencies**: `hashlib` (std)

### `backend/simulator/`
- **Purpose**: Simulates RTSP streams/edge nodes by reading local test video files and pumping frames/events to the AI module.
- **Key classes/functions**: `CameraSimulator`, `StreamManager`.
- **Dependencies**: `ai.*`, `config`.
- **External dependencies**: `opencv-python`, `redis`

---

## 3. Frontend Module Details

### `frontend/src/App.jsx`
- **Purpose**: Main React component. Handles routing, authentication context provider, and global layout.
- **Key classes/functions**: `App`, `PrivateRoute`.
- **Dependencies**: `pages/*`, `components/*`.
- **External dependencies**: `react-router-dom`

### `frontend/src/components/`
- **Purpose**: Reusable UI components (buttons, modals, tables, map overlays).
- **Key classes/functions**: `CameraMap`, `VideoPlayer`, `TimelineView`, `InvestigationGraph`.
- **Dependencies**: `hooks/*`, `utils/*`.
- **External dependencies**: `react-leaflet`, `lucide-react`, `recharts`

### `frontend/src/pages/`
- **Purpose**: High-level page views (Dashboard, Investigator Workspace, Command Center).
- **Key classes/functions**: `Dashboard`, `InvestigatorView`, `CaseManagement`.
- **Dependencies**: `components/*`, `services/*`.
- **External dependencies**: `react`

### `frontend/src/hooks/`
- **Purpose**: Custom React hooks for data fetching, polling, and state management.
- **Key classes/functions**: `useCameras`, `useLiveAlerts`, `useAuth`.
- **Dependencies**: `services/*`.
- **External dependencies**: `react`

### `frontend/src/services/`
- **Purpose**: API client and WebSocket handlers to communicate with the backend.
- **Key classes/functions**: `apiClient`, `CameraAPI`, `AlertsWebSocket`.
- **Dependencies**: `utils/*`.
- **External dependencies**: `axios`

### `frontend/src/utils/`
- **Purpose**: Helper functions (date formatting, spatial calculations, token decoding).
- **Key classes/functions**: `formatDate`, `calculateDistance`, `parseToken`.
- **Dependencies**: None.
- **External dependencies**: None.

---

## 4. Dependencies

### `backend/requirements.txt`
```text
fastapi==0.109.2
uvicorn==0.27.1
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
pydantic==2.6.1
pydantic-settings==2.1.0
ultralytics==8.1.10
paddleocr==2.7.3
paddlepaddle==2.6.0
opencv-python==4.9.0.80
numpy==1.26.4
networkx==3.2.1
faiss-cpu==1.7.4
redis==5.0.1
python-multipart==0.0.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.26.0
pillow==10.2.0
shapely==2.0.2
geopy==2.4.1
```

### `frontend/package.json` Dependencies
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "react-leaflet": "^4.2.1",
    "leaflet": "^1.9.4",
    "axios": "^1.6.7",
    "recharts": "^2.11.0",
    "lucide-react": "^0.323.0",
    "tailwindcss": "^3.4.1",
    "@headlessui/react": "^1.7.18"
  }
}
```

---

## 5. Environment Configuration

### `.env.example`
```dotenv
# Environment Options: development, testing, production
ENV=development

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Database Configuration (PostgreSQL)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cctv_intel

# Redis Configuration (Pub/Sub & Cache)
REDIS_URL=redis://localhost:6379/0

# Security / Auth
SECRET_KEY=your_super_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Models & Processing
YOLO_MODEL_PATH=ai/weights/yolov8n.pt
OCR_LANG=en
CONFIDENCE_THRESHOLD=0.6

# Edge Simulator Settings
VIDEO_DIR=../data/recordings
MAX_SIMULATED_CAMERAS=50
```

---

## 6. Module Dependency Diagram (Backend)

```text
┌─────────────────┐
│     api/        │
└────────┬────────┘
         │ (calls)
         ▼
┌─────────────────┐
│   services/     │ ◄─────┐
└────────┬────────┘       │ (consumes logic/data)
         │ (uses)         │
         ▼                │
┌─────────────────┐    ┌─────────────────┐
│     models/     │    │    engine/      │
└────────┬────────┘    └────────┬────────┘
         │ (maps to)            │ (queries/computes)
         ▼                      │
┌─────────────────┐             │
│   database.py   │ ◄───────────┘
└────────┬────────┘
         │
         ▼
    PostgreSQL
```
*Note: The `simulator/` invokes the `ai/` module and pushes inferred canonical observations into `services/` or directly via pub/sub.*

---

## 7. Coding Standards

### 7.1 Naming Conventions
- **Python (Backend)**: 
  - Modules & packages: `snake_case` (e.g., `camera_service.py`)
  - Classes: `PascalCase` (e.g., `CorrelationEngine`)
  - Functions & Variables: `snake_case` (e.g., `get_observations`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_PAGE_SIZE`)
- **React (Frontend)**: 
  - Components & files exporting them: `PascalCase` (e.g., `CameraMap.jsx`)
  - Hooks: `camelCase` prefixed with `use` (e.g., `useLiveAlerts.js`)
  - Variables/Functions: `camelCase`
- **Database**:
  - Tables: `snake_case`, pluralized (e.g., `cameras`, `observations`)
  - Columns: `snake_case`

### 7.2 Error Handling
- **Backend**:
  - Avoid generic `Exception` blocks. Catch specific exceptions.
  - Raise `HTTPException` in the `api/` layer for client-facing errors (400, 404, 401).
  - Use custom exception classes in the `services/` and `engine/` layers, which are caught and converted by the API layer or middleware.
- **Frontend**:
  - Global error boundary for UI crashes.
  - Axios interceptors to handle 401 (redirect to login) and 500 (show toast notification).
  - Graceful degradation for AI failures (e.g., if feasibility score fails, just show the timeline without the score).

### 7.3 Logging
- **Format**: Structured JSON logging is preferred. At minimum, standard log format should include timestamp, level, module, and message.
- `[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s`
- **Levels**: 
  - `ERROR`: System failures, unexpected exceptions, integration drops.
  - `WARNING`: Recoverable errors, degraded performance (e.g., GPU memory high).
  - `INFO`: Key lifecycle events (camera connected, case created).
  - `DEBUG`: Detailed tracing for the Spatio-Temporal engine, API request traces.
- Do not log sensitive PII or Section 65B evidence contents directly.
