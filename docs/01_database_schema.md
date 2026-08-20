# PostgreSQL Database Schema
**Document Version:** 1.0
**Target Database:** PostgreSQL 16
**Extensions:** PostGIS, uuid-ossp

This document outlines the core PostgreSQL schema for the Gujarat CCTV Intelligence Platform based on the Master Implementation Plan. It includes table definitions, indexes, constraints, row-level security (RLS) policies, and initial seed data.

## 1. Setup & Extensions

```sql
-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Create necessary ENUM types
CREATE TYPE observation_type AS ENUM ('PERSON', 'VEHICLE', 'OBJECT', 'EVENT');
CREATE TYPE entity_status AS ENUM ('CANDIDATE', 'ACTIVE', 'INACTIVE');
CREATE TYPE case_status AS ENUM ('OPEN', 'UNDER_INVESTIGATION', 'CHARGE_SHEET', 'CLOSED');
CREATE TYPE incident_severity AS ENUM ('P1', 'P2', 'P3', 'P4');
CREATE TYPE alert_priority AS ENUM ('P1', 'P2', 'P3', 'P4');
CREATE TYPE camera_status AS ENUM ('ONLINE', 'OFFLINE', 'DEGRADED', 'MAINTENANCE');
```

## 2. Access Control (RBAC)

```sql
CREATE TABLE roles (
    role_id VARCHAR(50) PRIMARY KEY,
    description TEXT
);
COMMENT ON TABLE roles IS 'Stores system roles for RBAC (e.g., Operator, Investigator).';

CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    badge_number VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    police_station VARCHAR(100) NOT NULL,
    jurisdiction_code VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
COMMENT ON TABLE users IS 'Authorized police and government users (per §31).';
COMMENT ON COLUMN users.jurisdiction_code IS 'Used for Row-Level Security and ABAC filtering.';

CREATE TABLE user_roles (
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    role_id VARCHAR(50) REFERENCES roles(role_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);
```

## 3. Physical / Edge Topology (Cameras)

```sql
CREATE TABLE cameras (
    cam_id VARCHAR(50) PRIMARY KEY,
    external_cam_id VARCHAR(100),
    display_name VARCHAR(200) NOT NULL,
    owner_department VARCHAR(100),
    managing_authority VARCHAR(100),
    integration_source VARCHAR(100),
    vendor VARCHAR(100),
    model VARCHAR(100),
    firmware_version VARCHAR(50),
    protocol VARCHAR(50),
    stream_url TEXT,
    vms_system VARCHAR(100),
    vms_camera_ref VARCHAR(100),
    
    -- Geospatial Data
    location geometry(Point, 4326),
    altitude_m NUMERIC,
    direction_deg INTEGER,
    fov_h_deg INTEGER,
    mount_height_m NUMERIC,
    location_type VARCHAR(100),
    road VARCHAR(150),
    intersection VARCHAR(150),
    
    -- Jurisdiction
    state VARCHAR(100) DEFAULT 'Gujarat',
    district VARCHAR(100),
    taluka VARCHAR(100),
    police_station VARCHAR(100),
    beat VARCHAR(100),
    jurisdiction_code VARCHAR(50) NOT NULL,
    
    -- Technical Details
    resolution VARCHAR(50),
    fps INTEGER,
    codec VARCHAR(50),
    camera_type VARCHAR(50),
    
    -- Operational Status
    status camera_status DEFAULT 'OFFLINE',
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    uptime_30d_pct NUMERIC,
    avg_bitrate_kbps NUMERIC,
    
    -- Edge processing
    gateway_id VARCHAR(100),
    edge_node_id VARCHAR(100),
    retention_local_hrs INTEGER,
    retention_platform VARCHAR(100),
    
    -- Lifecycle & Network
    onboarded_date DATE,
    last_maintenance DATE,
    decommissioned DATE,
    network_segment VARCHAR(100),
    ip_address VARCHAR(45),
    tags TEXT[]
);
COMMENT ON TABLE cameras IS 'Canonical camera registry (per §8). Authoritative list of all connected CCTV infrastructure.';
COMMENT ON COLUMN cameras.cam_id IS 'Platform-assigned immutable ID (e.g., CAM-GJ-AHM-SG-0142).';
COMMENT ON COLUMN cameras.location IS 'PostGIS geospatial point representing the camera physical location.';

CREATE INDEX idx_cameras_location ON cameras USING GIST (location);
CREATE INDEX idx_cameras_jurisdiction ON cameras(jurisdiction_code);

CREATE TABLE camera_capabilities (
    cam_id VARCHAR(50) REFERENCES cameras(cam_id) ON DELETE CASCADE,
    capability VARCHAR(100) NOT NULL,
    is_supported BOOLEAN DEFAULT FALSE,
    quality VARCHAR(50),
    notes TEXT,
    PRIMARY KEY (cam_id, capability)
);
COMMENT ON TABLE camera_capabilities IS 'Camera Capability Registry (per §9) (e.g., ANPR, Person Detection).';
```

## 4. Observations

```sql
CREATE TABLE observations (
    observation_id UUID NOT NULL,
    timestamp_capture TIMESTAMP WITH TIME ZONE NOT NULL,
    observation_type observation_type NOT NULL,
    source_camera_id VARCHAR(50) NOT NULL REFERENCES cameras(cam_id),
    source_gateway_id VARCHAR(100),
    source_edge_id VARCHAR(100),
    timestamp_process TIMESTAMP WITH TIME ZONE,
    location geometry(Point, 4326),
    bounding_box INTEGER[],
    track_id VARCHAR(100),
    confidence NUMERIC,
    payload JSONB,
    feature_vector_ref TEXT,
    frame_ref TEXT,
    video_ref TEXT,
    frame_offset_ms BIGINT,
    crop_ref TEXT,
    model_id VARCHAR(100),
    model_version VARCHAR(50),
    model_hash VARCHAR(100),
    processing_node VARCHAR(100),
    processing_latency_ms INTEGER,
    observation_hash VARCHAR(100),
    
    PRIMARY KEY (observation_id, timestamp_capture)
) PARTITION BY RANGE (timestamp_capture);

COMMENT ON TABLE observations IS 'Canonical Observation (per §14). The most important data object. Time-partitioned.';
COMMENT ON COLUMN observations.payload IS 'Type-specific JSON attributes (e.g., color, make).';
COMMENT ON COLUMN observations.observation_hash IS 'SHA-256 hash for integrity and Section 65B provenance.';

-- Default initial partition
CREATE TABLE observations_y2026m08 PARTITION OF observations 
    FOR VALUES FROM ('2026-08-01 00:00:00+05:30') TO ('2026-09-01 00:00:00+05:30');

CREATE INDEX idx_observations_camera_time ON observations(source_camera_id, timestamp_capture);
CREATE INDEX idx_observations_location ON observations USING GIST (location);
CREATE INDEX idx_observations_payload_gin ON observations USING GIN (payload jsonb_path_ops);
```

## 5. Entities (Person, Vehicle)

```sql
CREATE TABLE persons (
    person_id VARCHAR(50) PRIMARY KEY,
    first_seen TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE,
    observation_count INTEGER DEFAULT 0,
    running_confidence NUMERIC,
    attributes JSONB,
    status entity_status DEFAULT 'CANDIDATE'
);
COMMENT ON TABLE persons IS 'Person Intelligence Entity (per §16).';

CREATE TABLE vehicles (
    vehicle_id VARCHAR(50) PRIMARY KEY,
    plate VARCHAR(50),
    plate_confidence NUMERIC,
    color VARCHAR(50),
    vehicle_class VARCHAR(50),
    make_model VARCHAR(100),
    first_seen TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE,
    observation_count INTEGER DEFAULT 0,
    status entity_status DEFAULT 'ACTIVE'
);
COMMENT ON TABLE vehicles IS 'Vehicle Intelligence Entity (per §17).';
CREATE INDEX idx_vehicles_plate ON vehicles(plate);

CREATE TABLE person_observations (
    person_id VARCHAR(50) REFERENCES persons(person_id) ON DELETE CASCADE,
    observation_id UUID NOT NULL,
    timestamp_capture TIMESTAMP WITH TIME ZONE NOT NULL,
    confidence NUMERIC,
    FOREIGN KEY (observation_id, timestamp_capture) REFERENCES observations(observation_id, timestamp_capture) ON DELETE CASCADE,
    PRIMARY KEY (person_id, observation_id, timestamp_capture)
);

CREATE TABLE vehicle_observations (
    vehicle_id VARCHAR(50) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    observation_id UUID NOT NULL,
    timestamp_capture TIMESTAMP WITH TIME ZONE NOT NULL,
    confidence NUMERIC,
    FOREIGN KEY (observation_id, timestamp_capture) REFERENCES observations(observation_id, timestamp_capture) ON DELETE CASCADE,
    PRIMARY KEY (vehicle_id, observation_id, timestamp_capture)
);
```

## 6. Cases, Incidents & Evidence

```sql
CREATE TABLE incidents (
    incident_id VARCHAR(50) PRIMARY KEY,
    type VARCHAR(100) NOT NULL,
    severity incident_severity NOT NULL,
    status VARCHAR(50) DEFAULT 'OPEN',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE,
    jurisdiction_code VARCHAR(50) NOT NULL,
    location geometry(Point, 4326)
);
COMMENT ON TABLE incidents IS 'PSIM Incident Management (per §25).';
CREATE INDEX idx_incidents_location ON incidents USING GIST (location);
CREATE INDEX idx_incidents_jurisdiction ON incidents(jurisdiction_code);

CREATE TABLE cases (
    case_id VARCHAR(50) PRIMARY KEY,
    fir_reference VARCHAR(100),
    cctns_case_ref VARCHAR(100),
    district VARCHAR(100),
    police_station VARCHAR(100),
    jurisdiction_code VARCHAR(50) NOT NULL,
    investigating_officer VARCHAR(50) REFERENCES users(user_id),
    supervising_officer VARCHAR(50) REFERENCES users(user_id),
    assigned_date DATE,
    status case_status DEFAULT 'OPEN',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    access_list TEXT[],
    access_justification TEXT,
    classification VARCHAR(50)
);
COMMENT ON TABLE cases IS 'Case Architecture (per §26). Case is a first-class entity.';

CREATE TABLE evidence_packages (
    package_id VARCHAR(50) PRIMARY KEY,
    case_reference VARCHAR(50) REFERENCES cases(case_id),
    fir_reference VARCHAR(100),
    generated_by VARCHAR(50) REFERENCES users(user_id),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    package_hash VARCHAR(100),
    purpose TEXT
);
COMMENT ON TABLE evidence_packages IS 'Evidence Architecture (per §27). Designed for Sec 65B compliance.';

CREATE TABLE evidence_observations (
    package_id VARCHAR(50) REFERENCES evidence_packages(package_id) ON DELETE CASCADE,
    observation_id UUID NOT NULL,
    timestamp_capture TIMESTAMP WITH TIME ZONE NOT NULL,
    FOREIGN KEY (observation_id, timestamp_capture) REFERENCES observations(observation_id, timestamp_capture) ON DELETE CASCADE,
    PRIMARY KEY (package_id, observation_id, timestamp_capture)
);
```

## 7. Watchlists & Alerts

```sql
CREATE TABLE watchlists (
    watchlist_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id VARCHAR(50) REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE watchlist_entries (
    entry_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    watchlist_id VARCHAR(50) REFERENCES watchlists(watchlist_id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL, 
    identifier_value VARCHAR(100), 
    attributes JSONB, 
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    added_by VARCHAR(50) REFERENCES users(user_id),
    status VARCHAR(50) DEFAULT 'ACTIVE'
);

CREATE TABLE alerts (
    alert_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(100) NOT NULL,
    priority alert_priority NOT NULL,
    source_observation_id UUID,
    source_timestamp TIMESTAMP WITH TIME ZONE,
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'UNREAD',
    jurisdiction_code VARCHAR(50),
    FOREIGN KEY (source_observation_id, source_timestamp) REFERENCES observations(observation_id, timestamp_capture) ON DELETE SET NULL
);
```

## 8. Audit Log

```sql
CREATE TABLE audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) NOT NULL,
    role VARCHAR(50),
    case_id VARCHAR(50),
    purpose TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    query_type VARCHAR(100) NOT NULL,
    query_params JSONB,
    result_count INTEGER,
    data_accessed JSONB,
    export BOOLEAN DEFAULT FALSE,
    client_ip VARCHAR(45)
);
COMMENT ON TABLE audit_log IS 'Append-only immutable audit trail (per §34). Retention 7 years.';

CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_case ON audit_log(case_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
```

## 9. Row Level Security (RLS) Policies

```sql
-- Enforce Jurisdiction Scoping (per §31 RBAC+ABAC)

ALTER TABLE cameras ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view cameras in their jurisdiction or if they are command"
ON cameras
FOR SELECT
USING (
    jurisdiction_code LIKE current_setting('app.user_jurisdiction') || '%'
    OR current_setting('app.user_role') = 'command'
);

ALTER TABLE observations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view observations mapped to their jurisdiction"
ON observations
FOR SELECT
USING (
    source_camera_id IN (
        SELECT cam_id FROM cameras 
        WHERE jurisdiction_code LIKE current_setting('app.user_jurisdiction') || '%'
    )
    OR current_setting('app.user_role') = 'command'
);
```

## 10. Seed Data

```sql
-- Default Roles
INSERT INTO roles (role_id, description) VALUES
('operator', 'Monitor live feeds, respond to alerts, log incidents'),
('investigator', 'Search, trace, timeline, graph, evidence, case management'),
('command', 'Statewide/district overview, trends, response tracking'),
('field_officer', 'Mobile access to incident details, location, basic search'),
('admin', 'Camera onboarding, system config, user management'),
('security_admin', 'Security config, access reviews, incident response'),
('auditor', 'Read-only audit log access, compliance review');

-- Sample Users
INSERT INTO users (user_id, badge_number, full_name, department, district, police_station, jurisdiction_code) VALUES
('U1001', 'GJ-PI-4421', 'PI R.K. Sharma', 'Gujarat Police', 'Ahmedabad', 'Satellite PS', 'GJ-AHM-SAT'),
('U1002', 'GJ-DYSP-8822', 'DySP M.N. Patel', 'Gujarat Police', 'Ahmedabad', 'District HQ', 'GJ-AHM'),
('U1003', 'GJ-OP-1100', 'ASI K.L. Desai', 'Gujarat Police', 'Ahmedabad', 'Satellite PS', 'GJ-AHM-SAT');

INSERT INTO user_roles (user_id, role_id) VALUES
('U1001', 'investigator'),
('U1002', 'command'),
('U1003', 'operator');

-- Empty Watchlists
INSERT INTO watchlists (watchlist_id, name, description, owner_id) VALUES
('WL-001', 'Stolen Vehicles - Statewide', 'Vehicles reported stolen across Gujarat in the last 30 days', 'U1002'),
('WL-002', 'Wanted Persons - Ahmedabad', 'Active warrants and suspects in Ahmedabad district', 'U1002');
```
