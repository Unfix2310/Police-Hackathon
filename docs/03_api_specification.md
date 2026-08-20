# 03 - API Specification

This document details the complete API surface for the Gujarat CCTV Intelligence Platform (Hackathon MVP). All endpoints follow RESTful conventions, accept/return `application/json`, and require a Bearer token in the `Authorization` header.

## Global Headers
- `Authorization`: `Bearer <token>` (Required for all endpoints)
- `X-Correlation-ID`: Trace ID for end-to-end request tracking (Optional but recommended)

## Roles Reference
- `operator`: PSI/ASI (Jurisdiction scoped)
- `investigator`: PI/DySP (Jurisdiction + Case scoped)
- `command`: SP/DIG/IGP (Statewide or District scoped)
- `sysadmin`: IT/NIC (System configuration)
- `auditor`: Compliance / Oversight (Read-only logs)

---

## 1. Camera Domain

### `GET /api/v1/cameras`
List cameras in the system.
- **Auth**: `operator`, `investigator`, `command`, `sysadmin` (Scoped by jurisdiction)
- **Query Params**:
  - `district` (string, optional): Filter by district code
  - `status` (string, optional): Filter by status (`online`, `offline`, `degraded`)
  - `capability` (string, optional): Filter by AI capability (`anpr`, `facial_recognition`, `crowd`)
  - `limit` (int, default=50): Pagination
  - `offset` (int, default=0): Pagination
- **Response** (200 OK):
  ```json
  {
    "cameras": [
      {
        "id": "cam_5f9a2b",
        "name": "SG_Highway_Junction_North",
        "district": "ahmedabad",
        "location": {"lat": 23.0225, "lon": 72.5714},
        "status": "online",
        "capabilities": ["anpr", "vehicle_type"]
      }
    ],
    "total": 1250
  }
  ```

### `GET /api/v1/cameras/{cam_id}`
Get details for a specific camera.
- **Auth**: `operator`, `investigator`, `command`, `sysadmin`
- **Response** (200 OK):
  ```json
  {
    "id": "cam_5f9a2b",
    "name": "SG_Highway_Junction_North",
    "district": "ahmedabad",
    "location": {"lat": 23.0225, "lon": 72.5714},
    "status": "online",
    "capabilities": ["anpr", "vehicle_type"],
    "stream_url": "rtsp://gateway/cam_5f9a2b/stream",
    "installed_at": "2023-01-15T00:00:00Z"
  }
  ```

### `GET /api/v1/cameras/{cam_id}/health`
Get health telemetry for a specific camera.
- **Auth**: `operator`, `command`, `sysadmin`
- **Response** (200 OK):
  ```json
  {
    "status": "degraded",
    "uptime_seconds": 864000,
    "last_ping": "2024-05-10T14:32:00Z",
    "packet_loss_pct": 2.4,
    "issues": ["high_latency"]
  }
  ```

### `GET /api/v1/cameras/health/summary`
Get aggregate health statistics.
- **Auth**: `command`, `sysadmin`
- **Response** (200 OK):
  ```json
  {
    "total": 1250,
    "online": 1180,
    "offline": 45,
    "degraded": 25,
    "by_district": {
      "ahmedabad": {"online": 400, "offline": 12}
    }
  }
  ```

---

## 2. Observation Domain

### `GET /api/v1/observations`
Search raw canonical observations.
- **Auth**: `investigator`, `command`
- **Query Params**:
  - `camera_id` (string, optional)
  - `start_time` (iso8601, required)
  - `end_time` (iso8601, required)
  - `type` (string, optional): `vehicle` or `person`
  - `lat` (float, optional)
  - `lon` (float, optional)
  - `radius_meters` (int, optional)
- **Response** (200 OK):
  ```json
  {
    "observations": [
      {
        "id": "obs_99a8b7",
        "camera_id": "cam_5f9a2b",
        "timestamp": "2024-05-10T14:30:00Z",
        "type": "vehicle",
        "attributes": {
          "type": "car",
          "color": "white",
          "plate": "GJ01AB1234"
        },
        "thumbnail_url": "https://storage/obs_99a8b7.jpg"
      }
    ]
  }
  ```

### `GET /api/v1/observations/{obs_id}`
Get details for a specific observation.
- **Auth**: `investigator`, `command`
- **Response** (200 OK): Contains full Canonical Observation object including bounding boxes, metadata, and cropped images.

### `POST /api/v1/observations`
Internal endpoint for the AI pipeline to create an observation.
- **Auth**: System internal (API Key or Service Account)
- **Request Body**: Full Canonical Observation object.
- **Response** (201 Created): `{"id": "obs_99a8b7"}`

---

## 3. Entity Domain

### `GET /api/v1/entities/vehicles`
Search for vehicle entities.
- **Auth**: `investigator`, `command`
- **Query Params**:
  - `plate` (string, optional)
  - `color` (string, optional)
  - `type` (string, optional)
  - `start_time` (iso8601, optional)
  - `end_time` (iso8601, optional)
- **Response** (200 OK): Array of canonical vehicle entities.

### `GET /api/v1/entities/vehicles/{vehicle_id}`
Get unified vehicle entity details.
- **Auth**: `investigator`, `command`
- **Response** (200 OK):
  ```json
  {
    "id": "veh_GJ01AB1234",
    "plate": "GJ01AB1234",
    "colors_observed": ["white"],
    "types_observed": ["car", "suv"],
    "first_seen": "2024-05-01T10:00:00Z",
    "last_seen": "2024-05-10T14:30:00Z",
    "recent_observations": ["obs_99a8b7", "obs_99a8b8"]
  }
  ```

### `GET /api/v1/entities/vehicles/{vehicle_id}/trajectory`
Get spatial trajectory of a vehicle.
- **Auth**: `investigator`, `command`
- **Response** (200 OK):
  ```json
  {
    "points": [
      {
        "observation_id": "obs_99a8b7",
        "lat": 23.0225,
        "lon": 72.5714,
        "timestamp": "2024-05-10T14:30:00Z",
        "camera_id": "cam_5f9a2b"
      }
    ]
  }
  ```

### `GET /api/v1/entities/persons`
Search for person entities.
- **Auth**: `investigator`, `command`
- **Query Params**: `gender`, `clothing_color`, `start_time`, `end_time`
- **Response** (200 OK): Array of canonical person entities.

### `GET /api/v1/entities/persons/{person_id}`
Get person details + recent observations.
- **Auth**: `investigator`, `command`
- **Response** (200 OK): Canonical person entity with bounding boxes and vector references.

---

## 4. Search Domain

### `POST /api/v1/search`
Unified semantic/attribute search.
- **Auth**: `investigator`, `command`
- **Request Body**:
  ```json
  {
    "query": "white SUV near SG Highway",
    "entity_type": "vehicle",
    "filters": {
      "time_range": {"start": "2024-05-10T10:00:00Z", "end": "2024-05-10T18:00:00Z"}
    }
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "results": [
      {"score": 0.95, "type": "vehicle", "entity_id": "veh_GJ01AB1234", "observation_id": "obs_99a8b7"}
    ]
  }
  ```

### `POST /api/v1/search/scene`
Reconstruct a scene (all entities in radius at time).
- **Auth**: `investigator`
- **Request Body**:
  ```json
  {
    "lat": 23.0225,
    "lon": 72.5714,
    "radius_meters": 500,
    "timestamp": "2024-05-10T14:30:00Z",
    "time_window_seconds": 600
  }
  ```
- **Response** (200 OK): Map of vehicles and persons present in the spacetime volume.

---

## 5. Correlation Domain

### `GET /api/v1/trajectory/{entity_type}/{entity_id}`
Get full trajectory with spatial-temporal feasibility scores (speed violations, impossible jumps).
- **Auth**: `investigator`
- **Response** (200 OK):
  ```json
  {
    "trajectory": [],
    "feasibility_score": 0.98,
    "anomalies": []
  }
  ```

### `POST /api/v1/correlate`
Find entities correlated in time and space with a target (e.g. "which car always travels with this bike?").
- **Auth**: `investigator`
- **Request Body**:
  ```json
  {
    "target_type": "vehicle",
    "target_id": "veh_GJ01AB1234",
    "correlation_threshold_pct": 80
  }
  ```
- **Response** (200 OK): List of correlated entities and shared observation instances.

---

## 6. Investigation Domain

### `GET /api/v1/graph/{entity_type}/{entity_id}`
Get investigation graph neighbors (NetworkX mapping).
- **Auth**: `investigator`
- **Query Params**: `depth` (int, default=1)
- **Response** (200 OK): Nodes and edges format for D3/ReactFlow.

### `GET /api/v1/graph/{entity_type}/{entity_id}/path`
Find connection path between two entities.
- **Auth**: `investigator`
- **Query Params**: `target_type` (string), `target_id` (string)
- **Response** (200 OK): Array of edges forming the shortest path.

### `GET /api/v1/timeline/{entity_type}/{entity_id}`
Chronological timeline events.
- **Auth**: `investigator`
- **Response** (200 OK): Sorted array of `Observation` and `Incident` objects.

---

## 7. Incident Domain

### `GET /api/v1/incidents`
List incidents.
- **Auth**: `operator`, `investigator`, `command`
- **Query Params**: `status`, `district`, `priority`
- **Response** (200 OK): Array of incident objects.

### `POST /api/v1/incidents`
Create new incident.
- **Auth**: `operator`, `investigator`
- **Request Body**: `{"title": "...", "description": "...", "priority": "high", "location": {...}}`
- **Response** (201 Created): Incident ID.

### `PATCH /api/v1/incidents/{inc_id}`
Update status or priority.
- **Auth**: `operator`, `investigator`
- **Request Body**: `{"status": "resolved"}`
- **Response** (200 OK): Updated incident object.

---

## 8. Case Domain

### `GET /api/v1/cases`
List cases.
- **Auth**: `investigator`, `command`
- **Response** (200 OK): Array of case summaries.

### `POST /api/v1/cases`
Create case.
- **Auth**: `investigator`
- **Request Body**: Case details, tags.
- **Response** (201 Created): Case object.

### `GET /api/v1/cases/{case_id}`
Case detail.
- **Auth**: `investigator` (assigned only), `command`
- **Response** (200 OK): Full case document including linked entities.

### `POST /api/v1/cases/{case_id}/link`
Link an observation or entity to a case.
- **Auth**: `investigator` (assigned only)
- **Request Body**: `{"link_type": "observation", "target_id": "obs_123", "notes": "..."}`
- **Response** (200 OK): Updated case manifest.

---

## 9. Evidence Domain

### `POST /api/v1/evidence/generate`
Generate verifiable Sec 65B evidence package.
- **Auth**: `investigator`
- **Request Body**: `{"case_id": "case_123", "items": [{"type": "observation", "id": "obs_123"}]}`
- **Response** (202 Accepted): `{"job_id": "ev_gen_888"}` (async generation).

### `GET /api/v1/evidence/{evidence_id}`
Get completed evidence package metadata and download link.
- **Auth**: `investigator`
- **Response** (200 OK):
  ```json
  {
    "id": "ev_888",
    "status": "ready",
    "hash_sha256": "abc123def...",
    "download_url": "https://storage/ev_888.zip"
  }
  ```

---

## 10. Alert Domain

### `GET /api/v1/alerts`
List active unacknowledged alerts.
- **Auth**: `operator`, `command`
- **Response** (200 OK): Array of alert objects (e.g. Watchlist Match, Crowd Anomaly).

### `PATCH /api/v1/alerts/{alert_id}/acknowledge`
Acknowledge an alert.
- **Auth**: `operator`, `investigator`
- **Request Body**: `{"notes": "False alarm"}`
- **Response** (200 OK)

---

## 11. Watchlist Domain

### `GET /api/v1/watchlists`
List active watchlists.
- **Auth**: `investigator`, `command`
- **Response** (200 OK): Array of watchlists (e.g., "Stolen Vehicles").

### `POST /api/v1/watchlists`
Create watchlist.
- **Auth**: `investigator`
- **Request Body**: `{"name": "...", "description": "..."}`
- **Response** (201 Created)

### `POST /api/v1/watchlists/{list_id}/entries`
Add entity (e.g. license plate or face vector) to watchlist.
- **Auth**: `investigator`
- **Request Body**: `{"type": "vehicle", "value": "GJ01AB1234"}`
- **Response** (201 Created)

---

## 12. Analytics Domain

### `GET /api/v1/analytics/overview`
State overview for Command Dashboard.
- **Auth**: `command`
- **Response** (200 OK): Active incidents, total observations today, active cameras.

### `GET /api/v1/analytics/camera-health`
Camera health by district.
- **Auth**: `command`, `sysadmin`
- **Response** (200 OK): Aggregated timeseries data.

### `GET /api/v1/analytics/trends`
7-day / 30-day incident/observation trends.
- **Auth**: `command`
- **Response** (200 OK): Timeseries datapoints for chart rendering.

---

## 13. Admin Domain

### `GET /api/v1/health`
System health check.
- **Auth**: None (Public)
- **Response** (200 OK): `{"status": "healthy", "version": "1.0.0"}`

### `GET /api/v1/audit`
Query system audit logs.
- **Auth**: `auditor`, `sysadmin`
- **Query Params**: `user_id`, `action`, `resource_id`, `start_time`, `end_time`
- **Response** (200 OK): Array of audit events.

---

## 14. WebSockets & SSE

### `WS /ws/alerts`
Real-time push of generated alerts.
- **Auth**: Token provided in connection URL or initial payload.
- **Events**: `alert.new`, `alert.updated`

### `WS /ws/cameras`
Camera status heartbeat stream.
- **Auth**: Token required.
- **Events**: `camera.online`, `camera.offline`

### `SSE /api/v1/observations/stream`
Server-Sent Events for live observation ticker.
- **Auth**: Token required.
- **Events**: `observation.created`

---

## Error Handling

Standard HTTP response codes are used:
- `400 Bad Request`: Invalid input or parameters.
- `401 Unauthorized`: Missing or invalid token.
- `403 Forbidden`: Authenticated, but lacks role/jurisdiction (RBAC/ABAC denied).
- `404 Not Found`: Resource does not exist.
- `429 Too Many Requests`: Rate limit exceeded.
- `500 Internal Server Error`: Backend failure.

Error Body Schema:
```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "User lacks jurisdiction access for this camera.",
    "trace_id": "req_xyz123"
  }
}
```

## Rate Limiting
APIs are rate-limited per user and IP:
- Operators: 100 req/sec
- Investigators: 50 req/sec (Search paths are highly resource-intensive)
- System/Command: 200 req/sec
- Real-time Streams: 1 active connection per user.
