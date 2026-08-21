# Gujarat CCTV Intelligence Platform — Master Blueprint

> **PURPOSE**: This file is the single source of truth for project state.  
> Any new session (human or AI) reads THIS FILE FIRST to know exactly what exists, what's missing, and what to do next.  
> Updated after every significant milestone.

---

## 🔖 Last Updated
- **Date**: 2026-08-21T12:51:00+05:30
- **State**: PHASE 2 — CODE BUILD (restarting — code lost to branch cleanup)
- **Next Action**: Rebuild all code files using specs in `/docs/`

---

## 📁 Project Location
```
/Users/smit/Documents/Police Hackathon/
├── docs/                          ← 8 spec docs + architecture (SURVIVE)
├── gujarat-cctv-platform/         ← CODE (NEEDS REBUILD)
│   ├── backend/
│   ├── frontend/
│   ├── data/
│   ├── scripts/
│   ├── docker-compose.yml
│   └── .env.example
└── BLUEPRINT.md                   ← THIS FILE
```

---

## ✅ PHASE 1: Documentation (COMPLETE — all files verified present)

| # | File | Path | Status |
|---|------|------|--------|
| 1 | Database Schema | `docs/01_database_schema.md` | ✅ Done |
| 2 | Data Dictionary | `docs/02_data_dictionary.md` | ✅ Done |
| 3 | API Specification | `docs/03_api_specification.md` | ✅ Done |
| 4 | AI Pipeline Spec | `docs/04_ai_pipeline_spec.md` | ✅ Done |
| 5 | Project Structure | `docs/05_project_structure.md` | ✅ Done |
| 6 | Test Data Strategy | `docs/06_test_data_strategy.md` | ✅ Done |
| 7 | Docker Deployment | `docs/07_docker_deployment.md` | ✅ Done |
| 8 | Frontend Spec | `docs/08_frontend_spec.md` | ✅ Done |
| 9 | Master Architecture (v3.0) | `docs/implementation_planv3.md` | ✅ Done |

---

## 🔨 PHASE 2: Code Build — File-by-File Checklist

### Infrastructure Files

| # | File | Path (relative to gujarat-cctv-platform/) | Spec Source | Status |
|---|------|-----|-------------|--------|
| I1 | Docker Compose | `docker-compose.yml` | `docs/07_docker_deployment.md` | ❌ TODO |
| I2 | Environment template | `.env.example` | `docs/07_docker_deployment.md` | ❌ TODO |
| I3 | Backend Dockerfile | `backend/Dockerfile` | `docs/07_docker_deployment.md` | ❌ TODO |
| I4 | Frontend Dockerfile | `frontend/Dockerfile` | `docs/07_docker_deployment.md` | ❌ TODO |
| I5 | Requirements.txt | `backend/requirements.txt` | `docs/05_project_structure.md` | ❌ TODO |
| I6 | Setup script | `scripts/setup.sh` | `docs/07_docker_deployment.md` | ❌ TODO |
| I7 | README | `README.md` | — | ❌ TODO |

### Backend Foundation (Group A — do FIRST, everything depends on this)

| # | File | Path | Spec Source | Status |
|---|------|------|-------------|--------|
| A1 | Config | `backend/config.py` | `docs/05_project_structure.md`, `docs/07_docker_deployment.md` | ❌ TODO |
| A2 | Database | `backend/database.py` | `docs/05_project_structure.md` | ❌ TODO |
| A3 | Enums | `backend/models/enums.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| A4 | Camera model | `backend/models/camera.py` | `docs/01_database_schema.md` | ❌ TODO |
| A5 | Observation model | `backend/models/observation.py` | `docs/01_database_schema.md` | ❌ TODO |
| A6 | Entity models | `backend/models/entity.py` | `docs/01_database_schema.md` | ❌ TODO |
| A7 | Incident model | `backend/models/incident.py` | `docs/01_database_schema.md` | ❌ TODO |
| A8 | Case model | `backend/models/case.py` | `docs/01_database_schema.md` | ❌ TODO |
| A9 | Evidence model | `backend/models/evidence.py` | `docs/01_database_schema.md` | ❌ TODO |
| A10 | Watchlist model | `backend/models/watchlist.py` | `docs/01_database_schema.md` | ❌ TODO |
| A11 | Alert model | `backend/models/alert.py` | `docs/01_database_schema.md` | ❌ TODO |
| A12 | User model | `backend/models/user.py` | `docs/01_database_schema.md` | ❌ TODO |
| A13 | Audit model | `backend/models/audit.py` | `docs/01_database_schema.md` | ❌ TODO |
| A14 | Models __init__ | `backend/models/__init__.py` | — | ❌ TODO |
| A15 | Camera schemas | `backend/schemas/camera.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| A16 | Observation schemas | `backend/schemas/observation.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| A17 | Entity schemas | `backend/schemas/entity.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| A18 | Incident schemas | `backend/schemas/incident.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| A19 | Case schemas | `backend/schemas/case.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| A20 | Evidence schemas | `backend/schemas/evidence.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| A21 | Alert schemas | `backend/schemas/alert.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| A22 | Watchlist schemas | `backend/schemas/watchlist.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| A23 | Search schemas | `backend/schemas/search.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| A24 | Analytics schemas | `backend/schemas/analytics.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| A25 | Auth schemas | `backend/schemas/auth.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| A26 | Common schemas | `backend/schemas/common.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| A27 | Schemas __init__ | `backend/schemas/__init__.py` | — | ❌ TODO |
| A28 | JWT auth | `backend/auth/jwt.py` | `docs/05_project_structure.md` | ❌ TODO |
| A29 | RBAC | `backend/auth/rbac.py` | `docs/05_project_structure.md` | ❌ TODO |
| A30 | Auth __init__ | `backend/auth/__init__.py` | — | ❌ TODO |

### Simulator & Test Data (Group B — can run parallel with C, D)

| # | File | Path | Spec Source | Status |
|---|------|------|-------------|--------|
| B1 | Camera registry | `backend/simulator/camera_registry.py` | `docs/06_test_data_strategy.md` | ❌ TODO |
| B2 | Distance matrix | `backend/simulator/distance_matrix.py` | `docs/06_test_data_strategy.md` | ❌ TODO |
| B3 | Video simulator | `backend/simulator/video_simulator.py` | `docs/06_test_data_strategy.md` | ❌ TODO |
| B4 | Synthetic data gen | `backend/simulator/synthetic_data_generator.py` | `docs/06_test_data_strategy.md` | ❌ TODO |
| B5 | Simulator __init__ | `backend/simulator/__init__.py` | — | ❌ TODO |
| B6 | Cameras seed SQL | `data/seed/cameras.sql` | `docs/06_test_data_strategy.md` | ❌ TODO |
| B7 | Seed data SQL | `data/seed/seed_data.sql` | `docs/06_test_data_strategy.md` | ❌ TODO |
| B8 | Distance matrix JSON | `data/seed/distance_matrix.json` | `docs/06_test_data_strategy.md` | ❌ TODO |
| B9 | Generate script | `scripts/generate_synthetic_data.py` | `docs/06_test_data_strategy.md` | ❌ TODO |

### AI Pipeline (Group C — can run parallel with B, D)

| # | File | Path | Spec Source | Status |
|---|------|------|-------------|--------|
| C1 | Detector | `backend/ai/detector.py` | `docs/04_ai_pipeline_spec.md` | ❌ TODO |
| C2 | Tracker | `backend/ai/tracker.py` | `docs/04_ai_pipeline_spec.md` | ❌ TODO |
| C3 | ANPR | `backend/ai/anpr.py` | `docs/04_ai_pipeline_spec.md` | ❌ TODO |
| C4 | Attribute extractor | `backend/ai/attribute_extractor.py` | `docs/04_ai_pipeline_spec.md` | ❌ TODO |
| C5 | Feature extractor | `backend/ai/feature_extractor.py` | `docs/04_ai_pipeline_spec.md` | ❌ TODO |
| C6 | Observation generator | `backend/ai/observation_generator.py` | `docs/04_ai_pipeline_spec.md` | ❌ TODO |
| C7 | Pipeline orchestrator | `backend/ai/pipeline.py` | `docs/04_ai_pipeline_spec.md` | ❌ TODO |
| C8 | AI __init__ | `backend/ai/__init__.py` | — | ❌ TODO |

### Intelligence Engines (Group D — can run parallel with B, C)

| # | File | Path | Spec Source | Status |
|---|------|------|-------------|--------|
| D1 | Entity resolver | `backend/engine/entity_resolver.py` | `docs/04_ai_pipeline_spec.md` §5 | ❌ TODO |
| D2 | Correlation engine | `backend/engine/correlation.py` | `docs/04_ai_pipeline_spec.md` §6 | ❌ TODO |
| D3 | Feasibility engine | `backend/engine/feasibility.py` | `docs/04_ai_pipeline_spec.md` §6 | ❌ TODO |
| D4 | Investigation graph | `backend/engine/graph.py` | `docs/04_ai_pipeline_spec.md` | ❌ TODO |
| D5 | Search engine | `backend/engine/search.py` | `docs/03_api_specification.md` | ❌ TODO |
| D6 | Watchlist matcher | `backend/engine/watchlist.py` | `docs/04_ai_pipeline_spec.md` §7 | ❌ TODO |
| D7 | Evidence generator | `backend/evidence/generator.py` | `docs/02_data_dictionary.md` | ❌ TODO |
| D8 | Engine __init__ | `backend/engine/__init__.py` | — | ❌ TODO |
| D9 | Evidence __init__ | `backend/evidence/__init__.py` | — | ❌ TODO |

### API Layer (Group E — depends on A, references D)

| # | File | Path | Spec Source | Status |
|---|------|------|-------------|--------|
| E1 | Cameras router | `backend/api/cameras.py` | `docs/03_api_specification.md` | ❌ TODO |
| E2 | Observations router | `backend/api/observations.py` | `docs/03_api_specification.md` | ❌ TODO |
| E3 | Entities router | `backend/api/entities.py` | `docs/03_api_specification.md` | ❌ TODO |
| E4 | Search router | `backend/api/search.py` | `docs/03_api_specification.md` | ❌ TODO |
| E5 | Correlation router | `backend/api/correlation.py` | `docs/03_api_specification.md` | ❌ TODO |
| E6 | Investigation router | `backend/api/investigation.py` | `docs/03_api_specification.md` | ❌ TODO |
| E7 | Incidents router | `backend/api/incidents.py` | `docs/03_api_specification.md` | ❌ TODO |
| E8 | Cases router | `backend/api/cases.py` | `docs/03_api_specification.md` | ❌ TODO |
| E9 | Evidence router | `backend/api/evidence.py` | `docs/03_api_specification.md` | ❌ TODO |
| E10 | Alerts router | `backend/api/alerts.py` | `docs/03_api_specification.md` | ❌ TODO |
| E11 | Watchlists router | `backend/api/watchlists.py` | `docs/03_api_specification.md` | ❌ TODO |
| E12 | Analytics router | `backend/api/analytics.py` | `docs/03_api_specification.md` | ❌ TODO |
| E13 | Admin router | `backend/api/admin.py` | `docs/03_api_specification.md` | ❌ TODO |
| E14 | WebSocket | `backend/api/websocket.py` | `docs/03_api_specification.md` | ❌ TODO |
| E15 | API __init__ | `backend/api/__init__.py` | — | ❌ TODO |
| E16 | Main app | `backend/main.py` | `docs/05_project_structure.md` | ❌ TODO |

### Frontend (Group F — can run parallel with B, C, D, E)

| # | File | Path | Spec Source | Status |
|---|------|------|-------------|--------|
| F1 | package.json | `frontend/package.json` | `docs/08_frontend_spec.md` | ❌ TODO |
| F2 | Vite config | `frontend/vite.config.js` | `docs/08_frontend_spec.md` | ❌ TODO |
| F3 | Tailwind config | `frontend/tailwind.config.js` | `docs/08_frontend_spec.md` | ❌ TODO |
| F4 | PostCSS config | `frontend/postcss.config.js` | `docs/08_frontend_spec.md` | ❌ TODO |
| F5 | index.html | `frontend/index.html` | `docs/08_frontend_spec.md` | ❌ TODO |
| F6 | Main entry | `frontend/src/main.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F7 | App + routes | `frontend/src/App.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F8 | Global CSS | `frontend/src/index.css` | `docs/08_frontend_spec.md` | ❌ TODO |
| F9 | API service | `frontend/src/services/api.js` | `docs/08_frontend_spec.md` | ❌ TODO |
| F10 | Auth service | `frontend/src/services/auth.js` | `docs/08_frontend_spec.md` | ❌ TODO |
| F11 | WebSocket service | `frontend/src/services/websocket.js` | `docs/08_frontend_spec.md` | ❌ TODO |
| F12 | useAuth hook | `frontend/src/hooks/useAuth.js` | `docs/08_frontend_spec.md` | ❌ TODO |
| F13 | useAlerts hook | `frontend/src/hooks/useAlerts.js` | `docs/08_frontend_spec.md` | ❌ TODO |
| F14 | useApi hook | `frontend/src/hooks/useApi.js` | `docs/08_frontend_spec.md` | ❌ TODO |
| F15 | AppShell layout | `frontend/src/components/layout/AppShell.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F16 | Sidebar | `frontend/src/components/layout/Sidebar.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F17 | Header | `frontend/src/components/layout/Header.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F18 | Login page | `frontend/src/pages/Login.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F19 | Operator console | `frontend/src/pages/OperatorConsole.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F20 | Investigator workspace | `frontend/src/pages/InvestigatorWorkspace.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F21 | Search view | `frontend/src/pages/SearchView.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F22 | Trajectory view | `frontend/src/pages/TrajectoryView.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F23 | Command dashboard | `frontend/src/pages/CommandDashboard.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F24 | Map component | `frontend/src/components/shared/Map.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F25 | CameraMarker | `frontend/src/components/shared/CameraMarker.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F26 | ConfidenceBadge | `frontend/src/components/shared/ConfidenceBadge.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F27 | FeasibilityBadge | `frontend/src/components/shared/FeasibilityBadge.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F28 | StatusIndicator | `frontend/src/components/shared/StatusIndicator.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F29 | DataTable | `frontend/src/components/shared/DataTable.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F30 | LoadingSpinner | `frontend/src/components/shared/LoadingSpinner.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F31 | StatCard | `frontend/src/components/shared/StatCard.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F32 | CameraGrid | `frontend/src/components/operator/CameraGrid.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F33 | CameraCard | `frontend/src/components/operator/CameraCard.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F34 | AlertPanel | `frontend/src/components/operator/AlertPanel.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F35 | AlertItem | `frontend/src/components/operator/AlertItem.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F36 | SearchPanel | `frontend/src/components/investigator/SearchPanel.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F37 | EntityCard | `frontend/src/components/investigator/EntityCard.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F38 | TrajectoryTimeline | `frontend/src/components/investigator/TrajectoryTimeline.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F39 | TrajectoryMap | `frontend/src/components/investigator/TrajectoryMap.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F40 | InvestigationGraph | `frontend/src/components/investigator/InvestigationGraph.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F41 | EvidenceViewer | `frontend/src/components/investigator/EvidenceViewer.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F42 | ObservationDetail | `frontend/src/components/investigator/ObservationDetail.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F43 | StateMap | `frontend/src/components/command/StateMap.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F44 | TrendCharts | `frontend/src/components/command/TrendCharts.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |
| F45 | DistrictHealthTable | `frontend/src/components/command/DistrictHealthTable.jsx` | `docs/08_frontend_spec.md` | ❌ TODO |

---

## 🔄 DEPENDENCY GRAPH (Build Order)

```
Group A (Foundation) ─────────┐
                              ├──→ Group E (API Layer) ──→ Group F (Frontend)
Group B (Simulator)      ─────┤
Group C (AI Pipeline)    ─────┤
Group D (Intelligence)   ─────┘
Group I (Infrastructure) ─────→ independent, do anytime
```

**Minimum viable build order:**
1. Group I (infra files) — no dependencies
2. Group A (models, schemas, auth) — no code dependencies, just specs
3. Groups B + C + D in parallel — depend on A for imports
4. Group E (API) — imports from A + D
5. Group F (frontend) — depends on API being defined (reads spec, not code)

---

## 📋 HOW TO RESUME

Any new AI session or human developer should:

1. **Read this file** (`BLUEPRINT.md`)
2. **Check which files exist** by scanning the ❌/✅ status column above
3. **Update status** as files are created: change `❌ TODO` → `✅ Done`
4. **Follow the dependency order**: I → A → B/C/D → E → F
5. **Read the relevant spec doc** before writing each file (listed in "Spec Source" column)
6. **Commit to git after each group** so work survives interruptions
7. **Update this file** after completing each group

---

## 📊 PROGRESS SUMMARY

| Group | Files | Done | Remaining |
|-------|-------|------|-----------|
| I — Infrastructure | 7 | 0 | 7 |
| A — Backend Foundation | 30 | 0 | 30 |
| B — Simulator & Test Data | 9 | 0 | 9 |
| C — AI Pipeline | 8 | 0 | 8 |
| D — Intelligence Engines | 9 | 0 | 9 |
| E — API Layer | 16 | 0 | 16 |
| F — Frontend | 45 | 0 | 45 |
| **TOTAL** | **124** | **0** | **124** |

---

## 🎯 PHASE 3: Test & Polish (after all code)

- `[ ]` End-to-end test with 50 recordings
- `[ ]` Demo script validation (5-7 min scenario)
- `[ ]` Performance tuning
- `[ ]` Git tag v1.0-hackathon
