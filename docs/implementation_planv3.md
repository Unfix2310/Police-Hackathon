# Gujarat Statewide CCTV Intelligence Platform

## Master Implementation, Architecture & Deployment Plan

# Gujarat Police Hackathon: CCTV Intelligence Platform — Implementation Plan v3

> [!NOTE]
> **Superseded for MVP scope.** Graph technology decision for the hackathon
> MVP has been updated — see `docs/v4.1_decisions.md` §5. This document's
> Neo4j specification (§28, §38) remains the target for statewide
> production scale and is not currently implemented.

### Government of Gujarat

---

> **Classification**: Government Critical Infrastructure  
> **Document Version**: 3.0  
> **Date**: August 2026  
> **Scale**: 50,000+ cameras (initial), 80,000 design capacity, 100,000+ expansion  
> **Scope**: 33 districts, 250+ talukas, all jurisdictions

---

## Table of Contents

| §  | Section | §  | Section |
|----|---------|----|---------|
| 0  | [Document Purpose](#0-document-purpose) | 28 | [Data Architecture & System of Record](#28-data-architecture--system-of-record) |
| 1  | [Architecture Objectives](#1-architecture-objectives) | 29 | [Data Lake / Historical Analytics](#29-data-lake--historical-analytics) |
| 2  | [What This Platform Is — and Is Not](#2-what-this-platform-is--and-is-not) | 30 | [Security Architecture](#30-security-architecture) |
| 3  | [Current-State Architecture](#3-current-state-architecture) | 31 | [IAM: RBAC + ABAC](#31-iam-rbac--abac) |
| 4  | [Target-State Architecture](#4-target-state-architecture) | 32 | [AI Governance](#32-ai-governance) |
| 5  | [Five Core Architectural Planes](#5-five-core-architectural-planes) | 33 | [Human-in-the-Loop](#33-human-in-the-loop) |
| 6  | [Cross-Cutting Architecture](#6-cross-cutting-architecture) | 34 | [Privacy & Data Governance](#34-privacy--data-governance) |
| 7  | [CCTV Integration Fabric](#7-cctv-integration-fabric) | 35 | [Data Lifecycle](#35-data-lifecycle) |
| 8  | [Canonical Camera Model](#8-canonical-camera-model) | 36 | [Observability / NOC](#36-observability--noc) |
| 9  | [Camera Capability Registry](#9-camera-capability-registry) | 37 | [Failure Architecture](#37-failure-architecture) |
| 10 | [Edge Architecture](#10-edge-architecture) | 38 | [HA / DR](#38-ha--dr) |
| 11 | [Regional Architecture](#11-regional-architecture) | 39 | [Deployment Architecture](#39-deployment-architecture) |
| 12 | [Event Backbone](#12-event-backbone) | 40 | [Scalability Architecture](#40-scalability-architecture) |
| 13 | [AI Architecture](#13-ai-architecture) | 41 | [Existing-System Migration Strategy](#41-existing-system-migration-strategy) |
| 14 | [Canonical Observation](#14-canonical-observation) | 42 | [Camera Onboarding](#42-camera-onboarding) |
| 15 | [Entity Intelligence](#15-entity-intelligence) | 43 | [Vendor-Neutral Architecture](#43-vendor-neutral-architecture) |
| 16 | [Person Intelligence](#16-person-intelligence) | 44 | [API Architecture](#44-api-architecture) |
| 17 | [Vehicle Intelligence](#17-vehicle-intelligence) | 45 | [Application Architecture](#45-application-architecture) |
| 18 | [Correlation Engine](#18-correlation-engine) | 46 | [Investigator Workspace](#46-investigator-workspace) |
| 19 | [Spatio-Temporal Feasibility Engine](#19-spatio-temporal-feasibility-engine) | 47 | [Command Architecture](#47-command-architecture) |
| 20 | [Investigation Graph](#20-investigation-graph) | 48 | [Operations & NOC](#48-operations--noc) |
| 21 | [Investigation Timeline](#21-investigation-timeline) | 49 | [Procurement Architecture](#49-procurement-architecture) |
| 22 | [Search Architecture](#22-search-architecture) | 50 | [Cost Architecture](#50-cost-architecture) |
| 23 | [Police Integration Fabric](#23-police-integration-fabric) | 51 | [Deployment Phases](#51-deployment-phases) |
| 24 | [GIS Architecture](#24-gis-architecture) | 52 | [Success Metrics](#52-success-metrics) |
| 25 | [PSIM / Incident Management](#25-psim--incident-management) | 53 | [Final Architecture — One Sentence](#53-final-architecture--one-sentence) |
| 26 | [Case Architecture](#26-case-architecture) | 54 | [Hackathon MVP Strategy](#54-hackathon-mvp-strategy) |
| 27 | [Evidence Architecture](#27-evidence-architecture) | | |

---

# 0. Document Purpose

This document defines the **production-grade target architecture** for a statewide CCTV intelligence ecosystem for Gujarat.

The platform is designed to operate as an **intelligence and investigation layer over existing CCTV infrastructure**, rather than replacing existing city, police, traffic, Smart City, VMS, NVR, and command-center investments.

The architecture must support:

```
Existing CCTV Ecosystem
        ↓
Unified Integration
        ↓
Video + Metadata Normalization
        ↓
Edge / Regional Processing
        ↓
AI Perception
        ↓
Entity Intelligence
        ↓
Spatio-Temporal Correlation
        ↓
Incident Intelligence
        ↓
Investigation Graph
        ↓
Case / Evidence
        ↓
Police Operations
```

### Capacity Objective

| Stage | Camera Count | Trigger |
|-------|-------------|---------|
| Initial baseline | **50,000+** | Day-one statewide |
| Design capacity | **~80,000** | Urban expansion + highways |
| Horizontal expansion | **100,000+** | Future growth, private/partner integration |

The system **must not require an architectural redesign** when moving between these capacity levels. Scaling is achieved by adding infrastructure (edge nodes, GPU workers, database replicas, event partitions, storage capacity), not by changing the architecture.

---

# 1. Architecture Objectives

The platform shall:

| # | Objective |
|---|-----------|
| 1 | Integrate heterogeneous CCTV infrastructure without requiring universal camera replacement |
| 2 | Reuse existing VMS / NVR / camera / command-center investments |
| 3 | Normalize video and metadata from multiple vendors, protocols, codecs, and resolutions |
| 4 | Process high-volume streams through edge and regional infrastructure |
| 5 | Generate persistent, searchable, explainable CCTV observations |
| 6 | Build vehicle / person / object entities from observations |
| 7 | Correlate observations across cameras, time, and geography |
| 8 | Validate trajectories using spatio-temporal feasibility |
| 9 | Correlate entities with incidents and cases |
| 10 | Provide an investigation graph connecting all entities |
| 11 | Generate traceable evidence packages with full provenance |
| 12 | Integrate with authorized government and police systems (CCTNS, ICJS, eGujCop, ERSS, Vahan, etc.) |
| 13 | Support incident response and operational workflows (PSIM) |
| 14 | Provide statewide command visibility |
| 15 | Preserve security, privacy, auditability, and governance at every layer |
| 16 | Provide HA / DR with graceful degradation |
| 17 | Avoid vendor lock-in through open interfaces and canonical data models |
| 18 | Scale horizontally from 50K to 100K+ cameras |

---

# 2. What This Platform Is — and Is Not

## 2.1 It IS

> A **Statewide CCTV Intelligence and Investigation Platform** that converts fragmented CCTV into structured, searchable, correlated intelligence for authorized police and government use.

## 2.2 It is NOT

| It is NOT | Because |
|-----------|---------|
| Generalized mass surveillance | Purpose-bound to authorized investigation and incident response |
| Unrestricted person searching | Every search is case-bound, audited, and jurisdiction-scoped |
| Predictive / pre-crime scoring | System reconstructs past events; it does not predict future crime |
| Automated determination of guilt | AI produces probabilistic associations, not verdicts |
| Automated identification without human review | Every identity association requires human verification before operational action |
| Replacement for CCTNS / ICJS | Integrates with CCTNS/ICJS as systems of record; does not duplicate them |
| Replacement for existing VMS / NVR systems | Operates as an intelligence layer *over* existing VMS/NVR |
| Replacement for existing city command centers | Enhances existing command centers with cross-camera intelligence |

The platform acts as an **intelligence layer and interoperability layer** over existing systems.

---

# 3. Current-State Architecture

> [!IMPORTANT]
> Gujarat must be treated as a **federated CCTV ecosystem**, not a single CCTV network. The platform must embrace this heterogeneity, not fight it.

### 3.1 Existing Infrastructure Categories

```
Police CCTV
Traffic CCTV
Municipal CCTV
Smart City CCTV
Safe City infrastructure
Highway CCTV (NHAI)
Toll plaza cameras
Private / partner cameras (where lawfully integrated)
Existing NVR / VMS deployments
District command centers
City command centers (Ahmedabad ICCC, Surat COC, etc.)
```

### 3.2 Heterogeneity Profile

| Dimension | Variation |
|-----------|-----------|
| **Vendors** | Hikvision, Dahua, CP Plus, Bosch, Axis, Honeywell, Pelco, others |
| **VMS** | Milestone, Genetec, Digifort, iVMS, vendor-bundled, none |
| **Codecs** | H.264, H.265, MJPEG |
| **Resolutions** | VGA to 4K |
| **FPS** | 5–30 |
| **Retention** | 7 days to 90 days (varies by deployment) |
| **Protocols** | RTSP, ONVIF, vendor API, VMS SDK |
| **Networks** | GSWAN, BSNL, private fiber, wireless, mixed |
| **Metadata** | Vendor-specific, non-standard, or absent |
| **Management** | Police, municipal, traffic, Smart City SPV, highway authority |

### 3.3 Current-State Flow

```
CURRENT STATE
─────────────

Cameras (multiple owners, vendors, networks)
        ↓
Multiple VMS / NVR (siloed per deployment)
        ↓
Multiple Command Centers (per city, per department)
        ↓
Multiple Data Silos (no cross-deployment visibility)
        ↓
Manual Investigation (officer visits each command center)
        ↓
Manual Evidence Collection (screenshots, USB drives)
```

### 3.4 Core Problems with Current State

| Problem | Impact |
|---------|--------|
| No cross-system visibility | Officer must physically visit 5+ command centers for one case |
| No unified camera registry | Nobody knows exactly how many cameras exist statewide |
| No cross-camera intelligence | Same vehicle on two VMS systems appears as two unrelated events |
| No standardized metadata | Each system stores data differently, making correlation impossible |
| No evidence provenance | Screenshots from VMS lack chain-of-custody metadata |
| No statewide command picture | DGP office cannot see camera health or incidents statewide |
| Vendor lock-in | Each deployment is locked to its VMS vendor's analytics |

---

# 4. Target-State Architecture

```
                       GUJARAT CCTV ECOSYSTEM
                     (heterogeneous, federated)
                                │
                                ▼
                    ┌───────────────────────┐
                    │ CCTV INTEGRATION      │
                    │ FABRIC                │
                    │                       │
                    │ Adapters → Normalize  │
                    │ → Camera Registry     │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
               Stream Layer            Metadata Layer
                    │                       │
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │ EDGE / REGIONAL       │
                    │                       │
                    │ Decode → Sample →     │
                    │ Infer → Buffer        │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ EVENT BACKBONE        │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ AI INTELLIGENCE       │
                    │                       │
                    │ Perception            │
                    │ Entity Intelligence   │
                    │ Event Intelligence    │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ CORRELATION ENGINE    │
                    │                       │
                    │ Cross-camera          │
                    │ Spatio-temporal       │
                    │ Incident             │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ INVESTIGATION GRAPH   │
                    └───────────┬───────────┘
                                │
             ┌──────────────────┼──────────────────┐
             ▼                  ▼                  ▼
          Search             Timeline           Evidence
                                │
                                ▼
                    ┌───────────────────────┐
                    │ CASE / INVESTIGATION  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ PSIM / INCIDENT       │
                    │ RESPONSE              │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ POLICE WORKFLOW       │
                    │                       │
                    │ Operator              │
                    │ Investigator          │
                    │ Command               │
                    │ Field Officer          │
                    └───────────────────────┘

                    ╔═══════════════════════╗
                    ║   CROSS-CUTTING       ║
                    ║                       ║
                    ║ Police Integration    ║
                    ║ GIS                   ║
                    ║ Security / IAM        ║
                    ║ Privacy / Governance  ║
                    ║ AI Governance         ║
                    ║ Audit                 ║
                    ║ HA / DR              ║
                    ║ Observability         ║
                    ╚═══════════════════════╝
```

---

# 5. Five Core Architectural Planes

> [!IMPORTANT]
> Five planes, not three. Each plane has **separate concerns, separate scaling, separate teams, and separate failure domains**.

```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║  PLANE 5 — APPLICATION                                             ║
║  Operator │ Investigator │ Command │ Field │ Admin │ Auditor       ║
║                                                                    ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  PLANE 4 — INVESTIGATION & OPERATIONS                              ║
║  Incident │ PSIM │ Case │ Investigation │ Graph │ Search │         ║
║  Timeline │ Evidence │ Dispatch │ Alert Management                 ║
║                                                                    ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  PLANE 3 — INTELLIGENCE                                            ║
║  Perception │ Entity Intelligence │ Correlation │ Trajectory │     ║
║  Event Intelligence │ Analytics │ Watchlist │ Anomaly              ║
║                                                                    ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  PLANE 2 — INTEGRATION                                             ║
║  CCTV Integration Fabric │ Police Integration Fabric │             ║
║  Government APIs │ GIS │ External Authorized Systems               ║
║                                                                    ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  PLANE 1 — PHYSICAL / DATA                                         ║
║  Cameras │ VMS │ NVR │ Network │ Edge │ District Hub │             ║
║  State DC │ DR │ Object Storage │ Databases                        ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

| Plane | Scaling Strategy | Failure Impact | Team |
|-------|-----------------|----------------|------|
| **1 — Physical/Data** | Add cameras, edge nodes, storage | Camera/edge offline → observation gap, system continues | Infrastructure + Network |
| **2 — Integration** | Add adapters, API connectors | Adapter failure → specific VMS offline, others continue | Integration + DevOps |
| **3 — Intelligence** | Add GPU workers, scale event partitions | AI slow → delayed processing, no data loss (backpressure) | AI / ML |
| **4 — Investigation & Ops** | Scale search, graph, case services independently | Graph down → raw observations remain authoritative | Backend + Product |
| **5 — Application** | Stateless web tier, scale horizontally | Dashboard down → no user access, processing continues | Frontend + UX |

---

# 6. Cross-Cutting Architecture

These concerns sit **across all five planes**. They are not afterthoughts bolted onto Plane 5.

```
┌────────────────────────────────────────────────────────────────────┐
│                    CROSS-CUTTING CONCERNS                          │
│                                                                    │
│  SECURITY                    │  DATA GOVERNANCE                    │
│  ├── Network security        │  ├── Purpose limitation             │
│  ├── Camera security         │  ├── Collection rules               │
│  ├── Edge security           │  ├── Access rules                   │
│  ├── API security            │  ├── Retention policies             │
│  ├── Application security    │  ├── Deletion / archival            │
│  ├── Database security       │  ├── Case hold                      │
│  ├── Storage security        │  └── System-of-record ownership     │
│  ├── Evidence security       │                                     │
│  └── Audit security          │  AI GOVERNANCE                      │
│                              │  ├── Model registry                 │
│  IDENTITY & ACCESS           │  ├── Model approval workflow        │
│  ├── Authentication (LDAP)   │  ├── Deployment governance          │
│  ├── MFA                     │  ├── Performance monitoring          │
│  ├── RBAC + ABAC             │  ├── Drift detection                │
│  ├── Jurisdiction scoping    │  ├── Human feedback loop             │
│  ├── Case-bound access       │  └── Bias assessment                │
│  └── Purpose logging         │                                     │
│                              │  PRIVACY                            │
│  AUDIT                       │  ├── DPDP Act compliance             │
│  ├── Immutable audit log     │  ├── Purpose-bound processing        │
│  ├── 7-year retention        │  ├── Data minimization               │
│  ├── Tamper-evident          │  ├── Access auditing                 │
│  └── Anomaly detection       │  └── Right to erasure (where legal) │
│                              │                                     │
│  OBSERVABILITY               │  HA / DR                            │
│  ├── Infrastructure metrics  │  ├── Tiered RPO/RTO                  │
│  ├── Application metrics     │  ├── Graceful degradation            │
│  ├── AI model metrics        │  ├── DR failover                     │
│  ├── Camera health           │  └── Quarterly drill                 │
│  └── Alerting / escalation   │                                     │
│                              │  INTEROPERABILITY                   │
│  CONFIGURATION MANAGEMENT    │  ├── Open interfaces                 │
│  ├── Infra as code           │  ├── Canonical data models           │
│  ├── Model versioning        │  ├── Standard protocols              │
│  └── Feature flags           │  └── Export mechanisms               │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

# 7. CCTV Integration Fabric

## 7.1 Purpose

The platform must integrate **existing** heterogeneous CCTV infrastructure. The Integration Fabric is the boundary between the existing camera ecosystem and the platform's intelligence pipeline.

> [!IMPORTANT]
> The platform does NOT require every camera to speak one protocol. The Integration Fabric normalizes diversity into canonical streams and metadata.

## 7.2 Supported Integration Classes

| Class | Protocol / Interface | Typical Source |
|-------|---------------------|---------------|
| RTSP pull | Standard RTSP stream | Most IP cameras |
| ONVIF | ONVIF Profile S / T / G | Standards-compliant cameras |
| VMS API | Milestone MIP SDK, Genetec SDK, etc. | Existing VMS deployments |
| NVR interface | Vendor-specific API or RTSP re-stream | NVR-managed cameras |
| Vendor SDK / API | Hikvision ISAPI, Dahua API, etc. | Vendor-managed deployments |
| Command-center feed | API or stream from existing ICCC / COC | Smart City / Safe City |
| File / video ingestion | Upload or scheduled pull | Legacy systems, offline footage |

## 7.3 Adapter Architecture

```
                 EXISTING SYSTEMS
                       │
   ┌───────────────────┼───────────────────┐
   │                   │                   │
   ▼                   ▼                   ▼
┌──────────┐    ┌────────────┐    ┌────────────┐
│  RTSP    │    │  ONVIF     │    │  VMS API   │    ... more adapters
│  Adapter │    │  Adapter   │    │  Adapter   │
│          │    │            │    │            │
│ Connect  │    │ Discover   │    │ Authenticate│
│ Pull     │    │ Subscribe  │    │ Map cameras │
│ Reconnect│    │ Events     │    │ Pull stream │
│ Health   │    │ PTZ proxy  │    │ Re-stream   │
└────┬─────┘    └─────┬──────┘    └──────┬─────┘
     │                │                  │
     └────────────────┼──────────────────┘
                      ▼
            ┌──────────────────┐
            │ INTEGRATION      │
            │ FABRIC CORE      │
            │                  │
            │ ┌──────────────┐ │
            │ │ Stream       │ │
            │ │ Normalizer   │ │     → Normalized RTSP / internal
            │ └──────────────┘ │
            │ ┌──────────────┐ │
            │ │ Metadata     │ │     → Canonical camera record
            │ │ Normalizer   │ │
            │ └──────────────┘ │
            │ ┌──────────────┐ │
            │ │ Health       │ │     → Heartbeat, status
            │ │ Aggregator   │ │
            │ └──────────────┘ │
            │ ┌──────────────┐ │
            │ │ Camera       │ │     → Authoritative camera list
            │ │ Registry     │ │
            │ └──────────────┘ │
            │                  │
            └────────┬─────────┘
                     │
                     ▼
                   EDGE
```

## 7.4 Adapter Strategy by Source

| Source | Adapter Approach | Notes |
|--------|------------------|-------|
| Hikvision cameras | RTSP pull + ISAPI for PTZ/config | Most common in Gujarat |
| Dahua / CP Plus cameras | RTSP pull + Dahua API | CP Plus typically Dahua OEM |
| Bosch cameras | ONVIF Profile S/T | Government installations |
| Axis cameras | RTSP + VAPIX | Some city installations |
| Milestone VMS | MIP SDK → re-stream + metadata map | Existing Safe City VMS |
| Genetec VMS | SDK → re-stream + metadata map | Existing city deployments |
| Existing ICCC | API / stream feed from ICCC platform | Smart City command centers |
| NVR-only sites | RTSP re-stream from NVR | Older deployments with no VMS |
| Legacy / offline | File ingestion (upload / SFTP) | Historical footage, evidence |

---

# 8. Canonical Camera Model

Every camera receives a **platform-independent identity**. Downstream services never depend on vendor-specific camera formats.

```
CANONICAL CAMERA RECORD
─────────────────────────────────────────────
IDENTITY
  cam_id              : CAM-GJ-AHM-SG-0142     (platform-assigned, immutable)
  external_cam_id     : VMS-specific or NVR-specific reference
  display_name        : SG Highway / Drive-In Jn

OWNERSHIP
  owner_department    : Gujarat Police / AMC / NHAI / Smart City SPV / ...
  managing_authority  : Ahmedabad City Police
  integration_source  : Milestone VMS / Direct RTSP / ICCC feed / ...

VENDOR
  vendor              : Hikvision / Dahua / Bosch / ...
  model               : DS-2CD2T47G2-L
  firmware_version    : V5.7.15

PROTOCOL
  protocol            : RTSP │ ONVIF │ VMS-API │ ...
  stream_url          : rtsp://... (internal, via integration fabric)
  vms_system          : Milestone XProtect / None
  vms_camera_ref      : VMS-internal camera ID

LOCATION (authoritative)
  latitude            : 23.0395
  longitude           : 72.5268
  altitude_m          : 52
  direction_deg       : 315 (compass bearing of FOV center)
  fov_h_deg           : 90
  mount_height_m      : 6.5
  location_type       : intersection │ highway │ building_entry │ market │ ...
  road                : SG Highway
  intersection        : Drive-In Junction

JURISDICTION
  state               : Gujarat
  district            : Ahmedabad
  taluka              : City
  police_station      : Satellite PS
  beat                : Beat 7
  jurisdiction_code   : GJ-AHM-SAT

TECHNICAL
  resolution          : 2560x1440
  fps                 : 25
  codec               : H.265
  camera_type         : fixed │ PTZ │ dome │ bullet │ ...

STATUS
  status              : ONLINE │ OFFLINE │ DEGRADED │ MAINTENANCE
  last_heartbeat      : 2026-08-19T12:30:00+05:30
  uptime_30d_pct      : 97.2
  avg_bitrate_kbps    : 4200

EDGE
  gateway_id          : GW-AHM-WEST-02
  edge_node_id        : EDGE-AHM-SAT-01

RETENTION
  retention_local_hrs : 720  (30 days at camera/NVR)
  retention_platform  : per platform retention policy

LIFECYCLE
  onboarded_date      : 2025-03-14
  last_maintenance    : 2026-07-22
  decommissioned      : null

NETWORK
  network_segment     : GSWAN-AHM-ZONE3
  ip_address          : 10.x.x.x (internal, not exposed)

TAGS
  tags                : [highway, night_capable, anpr_suitable, high_traffic]
```

---

# 9. Camera Capability Registry

Every camera declares what it can actually support. This is critical when the system selects cameras for a query or determines which AI models to run.

```
CAMERA CAPABILITIES — CAM-GJ-AHM-SG-0142
──────────────────────────────────────────

Capability            Supported    Quality      Notes
──────────           ─────────    ───────      ─────
ANPR                  YES          HIGH         Direct line-of-sight, good angle
PTZ                   YES          —            Pan 360°, Tilt -20° to +90°
Audio                 NO           —            
Person Detection      YES          HIGH         4MP, well-lit
Vehicle Detection     YES          HIGH         Highway camera
Night Vision          YES          MEDIUM       IR, 30m range
Crowd Estimation      YES          MEDIUM       Wide FOV
Speed Estimation      NO           —            No calibration
Direction Detection   YES          HIGH         Clear lanes
```

Capabilities are determined during [camera onboarding](#42-camera-onboarding) and updated during maintenance cycles.

**Usage**: When an investigator searches "Show vehicles near SG Highway, 19:00–20:00", the system knows which cameras in that area are ANPR-capable versus detection-only, and weights results accordingly.

---

# 10. Edge Architecture

### 10.1 Edge Processing Pipeline

```
Camera
  │
  │ RTSP (via Integration Fabric)
  ▼
Camera Gateway
  │
  │ Normalized stream
  ▼
Stream Decode (H.264/H.265 → frames)
  │
  ▼
Frame Sampling
  │
  ├── Motion-triggered: process when scene changes
  ├── Interval: minimum 1 fps during quiet periods
  └── Event-triggered: process at full rate during alerts
  │
  ▼
Local AI Inference
  │
  ├── Person detection + attributes
  ├── Vehicle detection + attributes
  ├── ANPR (where camera is ANPR-capable)
  ├── Object detection
  ├── Within-camera tracking (assign track IDs)
  └── Event detection (basic: zone intrusion, stopped vehicle)
  │
  ▼
Metadata Generation (Canonical Observations)
  │
  ▼
Local Buffer (circular, 24-48 hours video + 7 days metadata)
  │
  ▼
Upstream → Regional Hub / Event Backbone
```

### 10.2 Edge Responsibilities

| Responsibility | Detail |
|---------------|--------|
| **Decoding** | H.264/H.265 to raw frames; GPU-accelerated |
| **Frame sampling** | Intelligent: motion-triggered, not fixed-interval |
| **AI inference** | Detection, tracking, ANPR, attributes (lightweight models) |
| **Metadata generation** | Canonical observations with provenance |
| **Local buffering** | Circular video buffer + metadata buffer |
| **Camera health** | Monitor heartbeat, stream quality, resolution, FPS |
| **Bandwidth optimization** | Send metadata + key frames upstream, NOT raw video |
| **Temporary storage** | Local SSD for buffer and recent observations |
| **Disconnected operation** | Continue detection + buffering during GSWAN outage; sync when reconnected |
| **Model update** | Receive and apply updated AI models from central model registry |

### 10.3 Edge Hardware

| Tier | Hardware | Cameras | Deployment |
|------|----------|---------|------------|
| Small PS edge | NVIDIA Jetson AGX Orin (64GB) | 10–30 cameras | Small police stations |
| Standard PS edge | Single NVIDIA A30 GPU server | 30–60 cameras | Standard police stations |
| Large PS / cluster | Dual GPU server | 60–120 cameras | Major police stations, junctions |

### 10.4 What Flows Upstream

```
EDGE → DISTRICT HUB / STATE DC
────────────────────────────────

CONTINUOUS (small, sustainable bandwidth):
  ✓ Observation metadata         JSON, ~1-5 KB per observation
  ✓ Key frames / thumbnails      JPEG, ~50-200 KB per observation
  ✓ Appearance feature vectors   Binary, ~2 KB per person crop
  ✓ ANPR results                 JSON, <1 KB
  ✓ Event alerts                 JSON, <1 KB
  ✓ Camera health telemetry      JSON, <0.5 KB per heartbeat

NEVER CONTINUOUS:
  ✗ Full raw video streams       (stays at edge/NVR)

ON-DEMAND PULL (investigator requests clip):
  ↔ Specific video clips         (30-60 sec around observation)
  ↔ Higher-resolution frames     (for verification)
```

### 10.5 Bandwidth Impact

| Path | Per Camera | Per Station (30 cam) | Per District (1,500 cam) | Statewide (50K cam) |
|------|-----------|---------------------|------------------------|---------------------|
| Raw video (if sent) | ~4 Mbps | ~120 Mbps | ~6 Gbps | **~200 Gbps** ❌ |
| Metadata only | ~2 Kbps avg | ~60 Kbps | ~3 Mbps | ~100 Mbps ✓ |
| Metadata + key frames | ~20 Kbps avg | ~600 Kbps | ~30 Mbps | **~1 Gbps** ✓ |
| On-demand clip pull | Burst | ~5 Mbps burst | ~50 Mbps burst | ~500 Mbps burst ✓ |

> [!TIP]
> Edge processing reduces sustained bandwidth from **~200 Gbps to ~1 Gbps** — a **200× reduction**. This is what makes 50,000+ cameras technically feasible over GSWAN without requiring a network rebuild.

---

# 11. Regional Architecture

Instead of every camera communicating directly with the State DC:

```
Cameras
  ↓
Police Station / Local Edge (x 250+)
  ↓
District / Regional Hub (x 33)
  ↓
State Data Center (1 primary)
  ↓
DR Site (1)
```

### District / Regional Hub Responsibilities

| Responsibility | Detail |
|---------------|--------|
| **Aggregation** | Collect observations from all PS edges in district |
| **Higher-accuracy AI** | Run larger models (second-pass ANPR verification, person ReID features) |
| **Caching** | Hot cache of district observations for local queries |
| **Event routing** | Forward relevant observations to state event backbone |
| **Local investigation** | Support district-level investigator queries without round-trip to state DC |
| **Watchlist matching** | District-level watchlist matching (subset of state watchlist) |
| **Failover** | Continue district-level operations if state DC link is degraded |
| **Model distribution** | Receive updated models from state, distribute to PS edges |
| **Configuration distribution** | Distribute camera config, sampling rules, alert rules to edges |
| **Health aggregation** | Aggregate camera/edge health for district-level view |

### District Hub Hardware

| Component | Specification | Per Hub |
|-----------|--------------|---------|
| GPU server | 2× NVIDIA A30 or equivalent, 256 GB RAM | 1–2 |
| Storage | 20 TB NVMe (hot) + 100 TB HDD (warm) | 1 |
| Network | 10 GbE internal, GSWAN uplink | 1 |

---

# 12. Event Backbone

All observations, alerts, and system events flow through a central event backbone.

### 12.1 Logical Event Domains

```
camera.events            Camera status changes, health
observation.person       Person observations
observation.vehicle      Vehicle observations
observation.object       Object observations
anpr.events              ANPR reads
event.events             Detected events (zone intrusion, crowd, etc.)
alert.events             Generated alerts (watchlist match, anomaly)
incident.events          Incident lifecycle events
case.events              Case lifecycle events
evidence.events          Evidence package events
audit.events             Audit trail events
model.events             Model deployment, drift, performance
```

### 12.2 Design Principles

| Principle | Implementation |
|-----------|---------------|
| Technology-agnostic naming | Logical domains, not Kafka topic names |
| Partitioning | By camera_id (locality of reference) |
| Ordering | Per-partition ordering guaranteed |
| Retention | 7 days hot; archive to object storage |
| Replication | 3× minimum |
| Throughput target | 500K events/sec at 50K cameras |
| Backpressure | Consumer lag monitored; producers never blocked |

**Technology**: Kafka or Kafka-compatible platform. The architecture must remain replaceable; no Kafka-specific features in business logic.

---

# 13. AI Architecture

> [!IMPORTANT]
> AI is split into **four stages**. Each stage has a distinct purpose. Do not conflate them.

### Stage 1 — Perception (Edge + Hub)

What is in this frame?

| Module | Runs At | Model Class | Latency Target |
|--------|---------|-------------|----------------|
| Person detection | Edge | YOLOv8 / RT-DETR | <50 ms/frame |
| Vehicle detection | Edge | YOLOv8 / RT-DETR | <50 ms/frame |
| ANPR (plate detection + OCR) | Edge | Custom CNN + CRNN | <100 ms/plate |
| Gujarati plate OCR | Edge + Hub | Custom CRNN (GJ-format trained) | <50 ms/plate |
| Object detection | Edge | YOLOv8 | <50 ms/frame |
| Within-camera tracking | Edge | ByteTrack / BoTSORT | <10 ms/frame |
| Basic event detection | Edge | Rule-based + lightweight CNN | <100 ms |

### Stage 2 — Scene Understanding (Hub)

What is happening in this scene?

| Module | Runs At | Model Class | Latency Target |
|--------|---------|-------------|----------------|
| Person-vehicle interaction | Hub | Spatial reasoning | <200 ms |
| Crowd estimation | Hub | CSRNet / custom | <100 ms/frame |
| Anomalous movement | Hub | Autoencoder / rule-based | <500 ms/clip |
| Restricted-area entry | Hub | Zone + detection | <50 ms |
| Road event detection (accident, wrong-way) | Hub | SlowFast + rules | <200 ms/clip |

### Stage 3 — Entity Intelligence (Hub + State)

Who or what is this entity?

| Module | Runs At | Model Class | Latency Target |
|--------|---------|-------------|----------------|
| Person appearance features | Edge + Hub | OSNet / BoT | <20 ms/crop |
| Person attributes (clothing, bag, helmet) | Edge | Multi-task CNN | <30 ms/crop |
| Vehicle attributes (color, type, make) | Edge | Multi-task CNN | <30 ms/crop |
| Person ReID candidate generation | Hub + State | ANN search on feature vectors | <50 ms/query |
| Vehicle entity resolution | Hub + State | Plate match + attribute match | <20 ms |
| Watchlist matching | Hub + State | Feature / plate comparison | <100 ms |

### Stage 4 — Correlation Intelligence (State)

How are entities connected across cameras, time, and space?

| Module | Runs At | Approach |
|--------|---------|----------|
| Cross-camera person association | State | ReID features + spatio-temporal feasibility |
| Cross-camera vehicle association | State | Plate match + attributes + feasibility |
| Trajectory inference | State | Ordered observations + route validation |
| Event correlation | State | Temporal + spatial + entity clustering |
| Incident inference | State | Multi-event pattern matching |

### Gujarat-Specific AI Considerations

| Challenge | Approach |
|-----------|----------|
| **Gujarati license plates** | Custom OCR trained on GJ-format (GJ XX YY ZZZZ); support temporary/dealer plates |
| **Two-wheeler dominance** | Detection models trained on Indian 2W; smaller plates handled separately |
| **Dust / haze** | Image pre-processing: dehazing, contrast enhancement |
| **Night / IR** | Night-optimized models; IR-compatible feature extraction |
| **Festival crowds** (Navratri, Uttarayan) | Crowd models calibrated for Indian densities |
| **Indian clothing** | Person attribute models trained on Indian clothing patterns |
| **Mixed traffic** | Vehicle classification includes auto-rickshaw, tractor, bullock cart |

---

# 14. Canonical Observation

The observation is the **single most important data object** in the system. Everything downstream — entities, correlation, graph, evidence — works from observations.

```
CANONICAL OBSERVATION
──────────────────────────────────

IDENTITY
  observation_id     : UUID (globally unique, immutable)
  observation_type   : PERSON │ VEHICLE │ OBJECT │ EVENT

SOURCE
  source_camera_id   : CAM-GJ-AHM-SG-0142
  source_gateway_id  : GW-AHM-WEST-02
  source_edge_id     : EDGE-AHM-SAT-01

TIME
  timestamp_capture  : 2026-08-19T18:32:14.237+05:30  (camera-synced NTP)
  timestamp_process  : 2026-08-19T18:32:14.891+05:30

LOCATION (inherited from camera, may be overridden for PTZ)
  location_lat       : 23.0395
  location_lng       : 72.5268

DETECTION
  bounding_box       : [x1, y1, x2, y2]  (pixel coordinates)
  track_id           : T-142  (within-camera track)
  confidence         : 0.94

ATTRIBUTES (type-specific)
  payload            : { ... see entity-specific sections ... }

FEATURES
  feature_vector_ref : vectordb://person-features/obs-<uuid>

REFERENCES
  frame_ref          : s3://frames/2026/08/19/CAM-GJ-AHM-SG-0142/18-32-14-237.jpg
  video_ref          : s3://video/2026/08/19/CAM-GJ-AHM-SG-0142/18-30-00.mp4
  frame_offset_ms    : 134237
  crop_ref           : s3://crops/2026/08/19/obs-<uuid>.jpg

PROVENANCE
  model_id           : person-detect-v3.2
  model_version      : 3.2.1
  model_hash         : sha256:a1b2c3...
  processing_node    : edge-ahm-sat-01
  processing_latency : 47 ms

INTEGRITY
  observation_hash   : sha256:d4e5f6...
```

---

# 15. Entity Intelligence

> [!WARNING]
> Entities are **not automatically equal to real-world identity**. The system works with probabilistic candidate entities, not declared identities.

### 15.1 Entity Lifecycle

```
Observation (raw detection)
        ↓
Candidate Entity (system-generated ID)
        ↓
Association (linked to existing entity with confidence score)
        ↓
Confidence level (probabilistic, not boolean)
        ↓
Human Review (required before operational action)
```

### 15.2 Association Status Levels

| Level | Meaning | Example | Action Allowed |
|-------|---------|---------|----------------|
| **Detected** | Object exists in frame | "A vehicle is at (x,y)" | Automated processing |
| **Observed** | Detection elevated to observation with attributes | "White sedan heading north" | Automated processing |
| **Associated** | Linked to existing entity by AI | "Probably Vehicle V-4521 (conf: 0.87)" | Automated alerting, investigator review |
| **Probable match** | High-confidence association | "Very likely same person (conf: 0.93)" | Investigator use in case |
| **Confirmed by human** | Investigator verified association | "Confirmed: this is the suspect vehicle" | Evidentiary use |

This distinction matters for responsible AI and legal defensibility.

---

# 16. Person Intelligence

```
Person Detection (Perception)
        ↓
Within-camera Tracking (assign track ID)
        ↓
Appearance Feature Extraction (2048-dim vector)
        ↓
Attribute Extraction (clothing color, bag, helmet, etc.)
        ↓
ReID Candidate Generation (ANN search in vector store)
        ↓
Cross-camera Association (feature similarity + feasibility)
        ↓
Confidence Scoring (weighted: similarity + spatial + temporal + attributes)
        ↓
Person Entity Created/Updated (P-XXXX)
        ↓
Watchlist Check (if match → alert)
        ↓
Human Review Required (before any operational action)
```

### Person Entity Record

```
Person P-7834
─────────────
  person_id           : P-7834
  first_seen          : 2026-08-19T12:10:14+05:30
  last_seen           : 2026-08-19T12:45:22+05:30
  observation_count   : 4
  observation_ids     : [obs-1, obs-2, obs-3, obs-4]
  running_confidence  : 0.87
  attributes          : { clothing: "blue shirt, dark pants",
                          bag: "backpack",
                          helmet: false,
                          gender_estimate: "male" }
  watchlist_matches   : []
  status              : CANDIDATE  (not human-confirmed)
```

> [!CAUTION]
> Facial recognition, if ever deployed, must be a **separately governed capability** with its own approval workflow, bias assessment, legal review, and access controls. It is not the default identity mechanism.

---

# 17. Vehicle Intelligence

```
Vehicle Detection (Perception)
        ↓
Within-camera Tracking
        ↓
Plate Detection (locate plate region)
        ↓
ANPR / OCR (read plate text)
        ↓
Plate Normalization (GJ01AB1234 → canonical format)
        ↓
Vehicle Attribute Extraction (color, type, make/model)
        ↓
Vehicle Entity Match (exact plate → direct match;
                       partial plate + attributes → candidate match)
        ↓
Cross-camera Association
        ↓
Vehicle Entity Created/Updated (V-XXXX)
        ↓
Watchlist Check (stolen vehicle, suspect plate → alert)
```

### Vehicle Entity Record

```
Vehicle V-4521
──────────────
  vehicle_id          : V-4521
  plate               : GJ01AB1234
  plate_confidence    : 0.96  (highest read)
  color               : White
  vehicle_class       : Sedan
  make_model          : (estimated where feasible)
  first_seen          : 2026-08-19T18:14:02+05:30
  last_seen           : 2026-08-19T18:48:31+05:30
  observation_count   : 5
  observation_ids     : [obs-11, obs-12, obs-13, obs-14, obs-15]
  associated_persons  : [P-17, P-22]
  watchlist_matches   : []
  status              : ACTIVE
```

### Vehicle Entity — Association Logic

| Match Type | Input | Confidence | Example |
|-----------|-------|------------|---------|
| Exact plate | Full plate matches | HIGH (0.90+) | GJ01AB1234 = GJ01AB1234 |
| Partial plate + attributes | Partial plate + color + type | MEDIUM (0.60–0.85) | GJ01AB12_4 + White Sedan |
| Attributes only | No readable plate; color + type + trajectory | LOW (0.40–0.65) | White Sedan, feasible trajectory |

---

# 18. Correlation Engine

> [!IMPORTANT]
> This is a **core differentiator**. The system does not merely detect — it correlates across cameras, time, space, and entities.

### 18.1 Correlation Inputs

The engine evaluates every candidate association using:

```
Identity similarity       (feature vector cosine distance or plate match)
  +
Temporal consistency      (time ordering makes sense)
  +
Spatial consistency       (locations are geographically reasonable)
  +
Route feasibility         (road distance vs. time difference)
  +
Appearance consistency    (clothing/color/type matches across observations)
  +
Camera topology           (known camera sequences on a route)
  +
Direction consistency     (heading at camera A consistent with arrival at camera B)
```

### 18.2 Output

The correlation engine produces an **Association Score** (0.0 – 1.0), never a binary TRUE / FALSE.

```
Association Score = w1 × identity_similarity
                  + w2 × temporal_feasibility
                  + w3 × spatial_feasibility
                  + w4 × appearance_consistency
                  + w5 × direction_consistency
                  + w6 × camera_topology_bonus

Where weights are tuned per entity type and validated against ground truth.
```

Every association carries its score and the breakdown of contributing factors — this is the basis for **explainable correlation**.

---

# 19. Spatio-Temporal Feasibility Engine

### 19.1 Core Concept

```
Given:
  Observation A — Camera C1, Time T1, Location L1
  Observation B — Camera C2, Time T2, Location L2

Step 1: Road distance
  distance = road_network_distance(L1, L2)
  NOTE: Road distance, NOT Euclidean distance.
  Source: OpenStreetMap + Gujarat road authority data

Step 2: Time difference
  time_diff = T2 - T1

Step 3: Required speed
  required_speed = distance / time_diff

Step 4: Feasibility assessment
  ┌─────────────────────────────────────────────────────────────┐
  │  Context              │ Required Speed    │ Assessment       │
  │───────────────────────│───────────────────│──────────────────│
  │  City road            │ < 40 km/h         │ PLAUSIBLE        │
  │  City road            │ 40-60 km/h        │ POSSIBLE         │
  │  City road            │ 60-80 km/h        │ LOW PLAUSIBILITY │
  │  City road            │ > 80 km/h         │ IMPLAUSIBLE      │
  │  Highway              │ < 80 km/h         │ PLAUSIBLE        │
  │  Highway              │ 80-120 km/h       │ POSSIBLE         │
  │  Highway              │ > 120 km/h        │ LOW PLAUSIBILITY │
  │  Any                  │ > 200 km/h        │ PHYSICALLY       │
  │                       │                   │ IMPOSSIBLE       │
  │  Any                  │ Negative (T2<T1)  │ IMPOSSIBLE       │
  └─────────────────────────────────────────────────────────────┘

Step 5: Contextual adjustments
  - Time of day (night → lower likely speeds)
  - Road class (NH / SH / city / rural)
  - Known traffic patterns (peak hours)
  - Direction consistency
  - Weather (if data available)

Step 6: Output
  feasibility_score  : 0.0 – 1.0
  feasibility_label  : PLAUSIBLE │ POSSIBLE │ LOW_PLAUSIBILITY │ IMPLAUSIBLE
  required_speed_kmh : X
  road_distance_km   : Y
  road_class         : highway │ city │ rural
  explanation        : "Requires 96 km/h on city roads — unlikely"
```

### 19.2 Pre-computed Road Network

```
Camera-to-camera road distances:
  Pairs within 10 km  : ~5M pairs   → pre-compute, store in PostgreSQL + cache in Redis
  Pairs within 50 km  : ~50M pairs  → compute on demand, cache result
  Pairs > 50 km       : compute on demand

Data source: OpenStreetMap (primary) + Gujarat road authority GIS
Update: Re-compute when cameras are added/moved
```

---

# 20. Investigation Graph

### 20.1 Purpose

The investigation graph connects all entities through typed relationships, enabling investigators to traverse connections that would be invisible in tabular data.

### 20.2 Graph Schema

**Core Nodes:**

```
(:Camera)       (:Location)     (:Observation)
(:Person)       (:Vehicle)      (:Object)
(:Event)        (:Incident)     (:Case)
(:Evidence)     (:Watchlist)    (:WatchlistEntry)
```

**Core Relationships:**

```
(:Observation)-[:CAPTURED_BY]->(:Camera)
(:Camera)-[:LOCATED_AT]->(:Location)
(:Person)-[:OBSERVED_AS {confidence, timestamp}]->(:Observation)
(:Vehicle)-[:OBSERVED_AS {confidence, timestamp}]->(:Observation)
(:Person)-[:ASSOCIATED_WITH {confidence, co_observations}]->(:Vehicle)
(:Person)-[:SEEN_WITH {distance_m, time_diff_s}]->(:Person)
(:Vehicle)-[:TRAVELED_TO {time_diff_s, distance_km, speed_kmh}]->(:Location)
(:Observation)-[:PART_OF]->(:Incident)
(:Incident)-[:RELATED_TO]->(:Case)
(:Observation)-[:SUPPORTED_BY]->(:Evidence)
(:Evidence)-[:GENERATED {timestamp, officer_id}]->(:Case)
(:Person)-[:MATCHED_ON]->(:WatchlistEntry)
(:Vehicle)-[:MATCHED_ON]->(:WatchlistEntry)
(:Observation)-[:DERIVED_FROM {model_id, confidence}]->(:Observation)
```

### 20.3 Example Graph Queries

```
// Vehicle trajectory
MATCH (v:Vehicle {plate: 'GJ01AB1234'})-[:OBSERVED_AS]->(o:Observation)
      -[:CAPTURED_BY]->(c:Camera)-[:LOCATED_AT]->(l:Location)
RETURN o.timestamp, c.cam_id, l.address, o.confidence
ORDER BY o.timestamp

// Vehicles that share cameras with suspect vehicle
MATCH (v1:Vehicle {plate: 'GJ01AB1234'})-[:OBSERVED_AS]->()
      -[:CAPTURED_BY]->(c:Camera)<-[:CAPTURED_BY]-()
      <-[:OBSERVED_AS]-(v2:Vehicle)
WHERE v2 <> v1
RETURN v2.plate, collect(DISTINCT c.cam_id) as shared_cameras
ORDER BY size(shared_cameras) DESC

// People associated with a vehicle
MATCH (p:Person)-[:ASSOCIATED_WITH]->(v:Vehicle {plate: 'GJ01AB1234'})
RETURN p.person_id, p.first_seen, p.last_seen, p.observation_count

// Scene reconstruction: everything at a location in a time window
MATCH (c:Camera)-[:LOCATED_AT]->(l:Location)
WHERE distance(point({latitude: l.lat, longitude: l.lng}),
               point({latitude: 23.0395, longitude: 72.5268})) < 500
WITH c
MATCH (o:Observation)-[:CAPTURED_BY]->(c)
WHERE o.timestamp >= datetime('2026-08-19T19:00:00+05:30')
  AND o.timestamp <= datetime('2026-08-19T19:30:00+05:30')
OPTIONAL MATCH (e)-[:OBSERVED_AS]->(o)
RETURN o.timestamp, c.cam_id, labels(e), e, o.confidence
ORDER BY o.timestamp
```

---

# 21. Investigation Timeline

The graph engine generates timelines for any entity.

```
TIMELINE: Vehicle V-4521 (GJ01AB1234)
──────────────────────────────────────

  18:14:02 ● CAM-GJ-AHM-SG-0101   SG Highway / ISRO
           │   Conf: 0.96 | ANPR | [Frame] [Clip]
           │
           │   ↓ 7 min, 3.2 km (27 km/h ✓ PLAUSIBLE)
           │
  18:21:17 ● CAM-GJ-AHM-SG-0113   SG Highway / Drive-In
           │   Conf: 0.98 | ANPR | [Frame] [Clip]
           │
           │   ↓ 8 min, 2.8 km (21 km/h ✓ PLAUSIBLE)
           │
  18:29:44 ● CAM-GJ-AHM-SG-0127   SG Highway / Thaltej
           │   Conf: 0.94 | ANPR | [Frame] [Clip]
           │   ⚠ Person P-17 observed near vehicle (conf: 0.82)
           │
           │   ↓ 8 min, 4.1 km (31 km/h ✓ PLAUSIBLE)
           │
  18:37:08 ● CAM-GJ-AHM-SG-0144   SG Highway / Sola
           │   Conf: 0.97 | ANPR | [Frame] [Clip]
           │
           │   ↓ 11 min, 8.7 km (47 km/h ✓ PLAUSIBLE)
           │
  18:48:31 ● CAM-GJ-AHM-SP-0171   SP Ring Road / Motera
               Conf: 0.93 | ANPR | [Frame] [Clip]
               ⚠ Person P-22 observed exiting vehicle (conf: 0.71)
```

**Every timeline entry links back to its underlying observation.** The investigator can click any entry to view the original frame, original video clip, and full observation provenance.

---

# 22. Search Architecture

The investigator can start from **any dimension**.

### Search Starting Points

| Start From | Query Parameters | Returns |
|-----------|-----------------|---------|
| **Vehicle** | Plate, vehicle attributes, camera, time | Trajectory, associated persons, incidents |
| **Person** | Appearance features, clothing attributes, camera, time | Movement history, associated vehicles, co-located persons |
| **Location** | GPS/address, radius, time window | All observations, entities present, events |
| **Incident** | Incident ID, location, time | Related entities, timeline, evidence |
| **Camera** | Camera ID, time range | All observations from that camera |
| **Graph** | Entity → traverse connections | Connected entities, shared cameras, co-occurrence |
| **Time** | Time window, optional area | Reconstruct scene at a moment |

### Query Translation Example

```
INVESTIGATOR ENTERS:
  "Show vehicles near SG Highway / Thaltej between 19:00 and 20:00"

SYSTEM TRANSLATES TO:
  1. Find cameras within 500m of SG Highway / Thaltej (PostGIS spatial query)
     → 8 cameras, 5 are ANPR-capable (from capability registry)
  2. Get vehicle observations from those cameras in time window (PostgreSQL)
  3. Group by vehicle entity (entity engine)
  4. For ANPR cameras: high-confidence plate matches
  5. For non-ANPR cameras: attribute-only associations (lower confidence)
  6. Rank by relevance (proximity to center, time, confidence)
  7. Check for incident correlation
  8. Return ranked results with confidence indicators

RESULT:
  23 unique vehicles, 5 with high-confidence plates, 18 attribute-only
  4 trajectories that pass through the area
  1 incident correlation (I-4521, spatial-temporal overlap)
```

---

# 23. Police Integration Fabric

> [!IMPORTANT]
> The platform must integrate with — not duplicate — existing police and government systems. Each external system remains its own system of record.

### 23.1 Integration Architecture

```
                    PLATFORM
                       │
                       ▼
              POLICE API GATEWAY
              (Auth, Audit, Rate Limit)
                       │
       ┌───────────────┼──────────────────────┐
       ▼               ▼                      ▼
     CCTNS          eGujCop                 ICJS
       │               │                      │
       ├── FIR data    ├── Gujarat-specific   ├── Case status
       ├── Criminal    │   police records     ├── Court requirements
       │   records     └── State crime data   └── Prosecution data
       ├── Case
       │   metadata
       └── Investigation
           status

       ┌───────────────┼──────────────────────┐
       ▼               ▼                      ▼
     VAHAN          SARATHI               ERSS / Dial 112
       │               │                      │
       ├── Vehicle     ├── License data       ├── Emergency call
       │   registration│                      │   location + time
       └── Owner       └── Driver data        └── Nearest observations
           details                                  returned

       ┌───────────────┐
       ▼               ▼
     AFIS / NAFIS   Other authorized
       │            systems
       ├── Fingerprint
       │   (if applicable)
       └── Criminal
           identification
```

### 23.2 Integration Principles

| Principle | Detail |
|-----------|--------|
| **Reference, don't duplicate** | Platform stores reference IDs (FIR number, Vahan registration), not full copies of external data |
| **API-first** | All integrations via documented REST APIs with versioning |
| **Read-mostly** | Most integrations are lookups; platform writes case links back to CCTNS |
| **Fail-open** | If CCTNS API is down, platform continues; external data simply unavailable until reconnected |
| **Audit every call** | Every API call to/from external system is logged with user, purpose, data accessed |
| **Data minimization** | Only request and cache the minimum data needed for the query |

### 23.3 External System Integration Matrix

| System | Owner | Direction | Data | Caching |
|--------|-------|-----------|------|---------|
| **CCTNS** | NCRB/NIC | Bidirectional | FIR data → Platform; Case links ← Platform | 24h cache for lookups |
| **eGujCop** | Gujarat Police | Read | Gujarat crime data, officer data | As needed |
| **ICJS** | DoJ | Read | Case status, court requirements | No cache |
| **Vahan** | MoRTH | Read | Vehicle registration on plate match | 7-day cache |
| **Sarathi** | MoRTH | Read | Driving license data on request | No cache |
| **AFIS/NAFIS** | NCRB | Read | Fingerprint match (if applicable) | No cache |
| **ERSS / Dial 112** | Gujarat Police | Bidirectional | Emergency location → Platform; Nearby obs ← Platform | Real-time, no cache |
| **GIS / Bhuvan** | ISRO/NIC | Read | Map tiles, geocoding, reverse geocoding | Map tile cache |

---

# 24. GIS Architecture

GIS is an **architectural component**, not merely a dashboard map layer.

### 24.1 GIS Provides

| Function | Used By |
|----------|---------|
| **Camera topology** | Spatial queries: "cameras within 500m of this point" |
| **Road network** | Spatio-temporal feasibility: road distance between cameras |
| **Jurisdiction boundaries** | RBAC: which cameras/observations a user can access |
| **Police station boundaries** | Camera assignment, operator scope |
| **District boundaries** | Regional hub routing, command dashboard |
| **Camera visibility** | Which areas a camera can actually observe (FOV + obstructions) |
| **Route graph** | Trajectory rendering, driving direction validation |
| **Incident location** | Spatial correlation with observations |
| **Spatial query** | "What vehicles passed within 1 km of the crime scene?" |
| **Heat maps** | Command dashboard: incident density, camera coverage gaps |

### 24.2 GIS Data Sources

| Source | Data | Update Frequency |
|--------|------|-----------------|
| OpenStreetMap | Road network, POIs | Monthly sync |
| Gujarat revenue / GIS dept | District, taluka, PS boundaries | Annual |
| Bhuvan (ISRO) | Satellite imagery, base maps | As available |
| Platform camera registry | Camera locations, FOVs | Real-time |
| Platform observations | Incident locations, trajectories | Real-time |

### 24.3 Spatial Database

PostGIS (PostgreSQL extension) for all spatial queries. Indexed:
- Camera locations (point geometry)
- Jurisdiction polygons
- Road network (line geometry)
- Camera FOV (polygon geometry, where defined)

---

# 25. PSIM / Incident Management

This section connects the platform to **actual police operations**, not just data analysis.

### 25.1 Incident Lifecycle

```
DETECTION (automated or manual)
        ↓
CORRELATION (link related observations/events)
        ↓
ALERT GENERATION (push to operators)
        ↓
VERIFICATION (operator confirms: real incident or false positive)
        ↓
INCIDENT CREATION (assigned incident ID, type, severity)
        ↓
PRIORITY ASSIGNMENT (P1 Critical / P2 High / P3 Medium / P4 Low)
        ↓
ASSIGNMENT (to responding unit / investigating officer)
        ↓
RESPONSE TRACKING (unit dispatched, arrived, status updates)
        ↓
STATUS UPDATES (in-progress, escalated, resolved)
        ↓
RESOLUTION (closed with outcome, linked evidence)
        ↓
CASE LINKAGE (if FIR filed → link to case)
        ↓
POST-INCIDENT REVIEW (response time, outcome, system accuracy)
```

### 25.2 Alert Types

| Alert Category | Examples | Priority | Response |
|---------------|----------|----------|----------|
| **Watchlist match** | Stolen vehicle plate, wanted person appearance match | P1/P2 | Immediate notification, dispatcher action |
| **Zone intrusion** | Restricted area entry, perimeter breach | P2 | Operator verification → dispatch |
| **Anomaly** | Wrong-way vehicle, crowd formation, abandoned object | P2/P3 | Operator verification |
| **Camera health** | Camera offline, cluster offline, degraded quality | P3/P4 | NOC → field maintenance |
| **System** | AI performance drift, storage threshold, network degradation | P3/P4 | NOC → engineering escalation |

### 25.3 Dispatch Integration

When an incident is confirmed and requires response:

```
Incident confirmed
        ↓
Nearest patrol unit identified (from Dial 112 / eGujCop)
        ↓
Dispatch notification (via platform or Dial 112 integration)
        ↓
Location + context shared (map, camera feed, entity info)
        ↓
Field officer receives on mobile interface
        ↓
Status updates flow back to platform
```

---

# 26. Case Architecture

Case is a **first-class entity** in the system, not an afterthought.

```
CASE RECORD
───────────

IDENTITY
  case_id              : CASE-2026-AHM-SAT-0421
  fir_reference        : FIR/AHM/SAT/2026/4521  (link to CCTNS, not duplicated)
  cctns_case_ref       : CCTNS reference ID

JURISDICTION
  district             : Ahmedabad
  police_station       : Satellite PS
  jurisdiction_code    : GJ-AHM-SAT

ASSIGNMENT
  investigating_officer : PI R.K. Sharma (Badge: GJ-PI-4421)
  supervising_officer   : DySP M.N. Patel
  assigned_date         : 2026-08-19

LINKED ENTITIES
  incidents            : [I-4521]
  persons              : [P-17, P-22]
  vehicles             : [V-4521]
  observations         : [obs-11, obs-12, ..., obs-15, obs-201, obs-202]
  cameras              : [C101, C113, C127, C144, C171]

INVESTIGATION ARTIFACTS
  timeline             : auto-generated, editable
  evidence_packages    : [EP-2026-4521-001]
  investigator_notes   : [structured notes]
  actions              : [action log]

ACCESS CONTROL
  access_list          : [PI Sharma, DySP Patel, SP Ahmedabad]
  access_justification : FIR/AHM/SAT/2026/4521
  classification       : RESTRICTED

LIFECYCLE
  status               : OPEN │ UNDER_INVESTIGATION │ CHARGE_SHEET │ CLOSED
  created              : 2026-08-19T20:00:00+05:30
  last_updated         : 2026-08-19T22:15:00+05:30

AUDIT
  audit_trail          : [complete history of every access, modification, export]
```

---

# 27. Evidence Architecture

### 27.1 Legal Positioning

> [!WARNING]
> The platform produces **evidence packages designed to preserve integrity, provenance, and required evidentiary metadata**. Legal admissibility remains subject to applicable law and competent authority. The platform is not a legal authority.

### 27.2 Provenance Chain

Every observation carries full provenance. Every evidence package links back through the complete chain:

```
Evidence Package
        ↓
Observation(s)
        ↓
Original Frame (with hash)
        ↓
Original Video Segment (with hash)
        ↓
Source Camera (with registry record)
        ↓
Timestamp (NTP-synced, verified)
        ↓
Processing Record (model ID, version, node, latency)
        ↓
Model Version (with training metadata hash)
        ↓
Integrity Hash (SHA-256, chained)
        ↓
Audit Record (who generated, when, for what case)
```

### 27.3 Evidence Package Contents

```
EVIDENCE PACKAGE EP-2026-4521-001
─────────────────────────────────

METADATA
  package_id          : EP-2026-4521-001
  case_reference      : CASE-2026-AHM-SAT-0421
  fir_reference       : FIR/AHM/SAT/2026/4521
  generated_by        : PI R.K. Sharma (Badge: GJ-PI-4421)
  generated_at        : 2026-08-19T20:15:00+05:30
  package_hash        : sha256:x7y8z9...
  purpose             : Vehicle trajectory evidence

SUBJECT
  Vehicle V-4521 │ Plate GJ01AB1234 │ White Sedan

TIMELINE (5 observations)
  ┌─────────────────────────────────────────────────────────┐
  │ # │ Time     │ Camera │ Location          │ Conf │ Type │
  ├───┼──────────┼────────┼───────────────────┼──────┼──────┤
  │ 1 │ 18:14:02 │ C101   │ SG Hwy / ISRO     │ 0.96 │ ANPR │
  │ 2 │ 18:21:17 │ C113   │ SG Hwy / Drive-In │ 0.98 │ ANPR │
  │ 3 │ 18:29:44 │ C127   │ SG Hwy / Thaltej  │ 0.94 │ ANPR │
  │ 4 │ 18:37:08 │ C144   │ SG Hwy / Sola     │ 0.97 │ ANPR │
  │ 5 │ 18:48:31 │ C171   │ SP Ring / Motera   │ 0.93 │ ANPR │
  └─────────────────────────────────────────────────────────┘

TRAJECTORY VALIDATION
  All transitions: PLAUSIBLE (speeds 21–47 km/h on city/highway roads)

ASSOCIATED PERSONS
  P-17: Observed near vehicle at C127 (conf: 0.82)
  P-22: Observed exiting vehicle at C171 (conf: 0.71)

VIDEO CLIPS
  clip_001.mp4 — C101, 18:13:32 to 18:14:32 │ hash: sha256:...
  clip_002.mp4 — C113, 18:20:47 to 18:21:47 │ hash: sha256:...
  clip_003.mp4 — C127, 18:29:14 to 18:30:14 │ hash: sha256:...
  clip_004.mp4 — C144, 18:36:38 to 18:37:38 │ hash: sha256:...
  clip_005.mp4 — C171, 18:48:01 to 18:49:01 │ hash: sha256:...

PROVENANCE (per observation)
  [Full provenance chain as defined in §14]

INTEGRITY
  Package hash verified: ✓
  All component hashes verified: ✓
  Chain-of-custody: Unbroken
  Generated by authorized personnel: ✓

SECTION 65B CERTIFICATE (auto-generated, officer-countersigned)
  [See §27.4]

DISCLAIMER
  All identifications are probabilistic assessments by automated systems.
  Confidence scores indicate detection reliability, not evidentiary certainty.
  Human verification is required for all identity determinations.
  Legal admissibility is subject to applicable law and competent authority.
```

### 27.4 Section 65B Compliance

```
CERTIFICATE UNDER SECTION 65B
OF THE INDIAN EVIDENCE ACT, 1872
─────────────────────────────────

This certificate is generated in respect of electronic record(s)
produced by the Gujarat CCTV Intelligence Platform.

1. The electronic record was produced by a computer system regularly
   used for storing and processing CCTV observations in the ordinary
   course of law enforcement activities.

2. During the relevant period, the computer system was operating
   properly, or if not, any deviation did not affect the accuracy
   of the electronic record.

3. The information contained in the electronic record reproduces
   information fed into the computer in the ordinary course of
   the said activities.

4. The electronic record is accompanied by:
   a. Integrity hash verification
   b. Chain-of-custody metadata
   c. Source camera identification
   d. Processing pipeline version and model version
   e. Timestamp verification (NTP-synchronized)

Auto-generated by: Gujarat CCTV Intelligence Platform v[X.Y.Z]
Countersigned by: [Authorized officer]
Date: [Auto-generated]
Reference: [Evidence package ID]
```

---

# 28. Data Architecture & System of Record

> [!IMPORTANT]
> Each data type has one and only one **system of record**. This prevents "which database is authoritative?" ambiguity.

### 28.1 System-of-Record Ownership

| Data | System of Record | Technology | Notes |
|------|-----------------|------------|-------|
| Camera configuration & registry | **PostgreSQL** | PostgreSQL 16 | Authoritative camera list |
| Camera location & spatial data | **PostgreSQL + PostGIS** | PostGIS | Authoritative geospatial |
| Raw video & frames | **Object storage** | MinIO (on-prem S3-compatible) | Immutable once written |
| Evidence clips & packages | **Object storage** | MinIO (evidence bucket, immutable) | Legal retention |
| Observation metadata | **PostgreSQL** | PostgreSQL (time-partitioned) | Authoritative observation records |
| Search index | **OpenSearch** | OpenSearch 2.x | Derived from PostgreSQL via CDC; not authoritative |
<!-- Superseded for MVP — see docs/v4.1_decisions.md §5 -->
| Investigation relationships | **Graph DB** | Neo4j Enterprise (clustered) | Authoritative relationship data |
| Embedding / feature vectors | **Vector DB** | Milvus or Qdrant | Authoritative feature store |
| Real-time state & cache | **Redis** | Redis 7.x cluster | Ephemeral; reconstructable from authoritative stores |
| Event stream | **Kafka** | Apache Kafka 3.x | 7-day hot retention; archived to object storage |
| Audit trail | **Immutable audit store** | PostgreSQL (append-only) + object storage archive | 7-year retention, tamper-evident |
| Case data | **PostgreSQL** | PostgreSQL | Cross-references CCTNS (does not duplicate) |
| External data (FIR, vehicle reg) | **External system** | CCTNS, Vahan, etc. | Platform stores references only |

### 28.2 Data Flow Between Stores

```
PostgreSQL (authoritative observations)
        │
        ├──► OpenSearch (CDC via Debezium/Kafka Connect) → search index
        <!-- Superseded for MVP — see docs/v4.1_decisions.md §5 -->
        ├──► Neo4j (event-driven via Kafka) → graph relationships
        ├──► Redis (event-driven) → real-time cache
        └──► Data lake (batch ETL) → historical analytics

Object Storage (authoritative video/frames)
        │
        └──► Evidence packages (selected subsets, immutable copy)

Vector DB (authoritative features)
        │
        └──► ANN search for ReID queries
```

### 28.3 Storage Capacity Estimates (Full Scale: 50K cameras)

| Store | Initial | Year 1 | Year 3 | Notes |
|-------|---------|--------|--------|-------|
| Object storage (video) | 200 TB | 2 PB | 5 PB | 90-day retention + evidence hold |
| Object storage (frames/crops) | 50 TB | 500 TB | 1.5 PB | Key frames + entity crops |
| PostgreSQL | 500 GB | 2 TB | 6 TB | Time-partitioned, archived monthly |
| OpenSearch | 200 GB | 1 TB | 3 TB | Derived, can be rebuilt |
<!-- Superseded for MVP — see docs/v4.1_decisions.md §5 -->
| Neo4j | 100 GB | 500 GB | 1.5 TB | Graph grows with entities/relationships |
| Vector DB | 50 GB | 200 GB | 600 GB | ~100M vectors at scale |
| Redis | 32 GB | 64 GB | 128 GB | Ephemeral, bounded |
| Audit store | 50 GB | 200 GB | 1 TB | Immutable, 7-year retention |

---

# 29. Data Lake / Historical Analytics

```
Raw events (Kafka)
        ↓
Archive to Object Storage / Data Lake (Parquet format)
        ↓
Historical Analytics
        ├── Crime pattern analysis (monthly)
        ├── Camera utilization analysis
        ├── AI model evaluation (precision/recall over time)
        ├── Traffic pattern analysis
        └── Operational intelligence (response times, coverage gaps)
        ↓
Reporting / Command Dashboard Analytics
```

> [!WARNING]
> The data lake must NOT become an uncontrolled duplicate of all personal data. Same **purpose limitation, retention policies, and access controls** apply. Analytics should use aggregated / anonymized data wherever possible. Individual-level analytics only for authorized investigation purposes.

---

# 30. Security Architecture

### 30.1 Ten Security Layers

```
┌────────────────────────────────────────────────────────────────────┐
│                    SECURITY ARCHITECTURE                            │
│                                                                    │
│  LAYER 1: CAMERA SECURITY                                          │
│  • Camera credentials managed centrally (not default passwords)    │
│  • Firmware update management                                      │
│  • Camera network isolated from data network                       │
│  • No direct camera-to-internet connectivity                       │
│                                                                    │
│  LAYER 2: NETWORK SECURITY                                         │
│  • GSWAN = isolated government network (not public internet)       │
│  • Camera networks on separate VLANs                               │
│  • Edge ↔ Hub: encrypted tunnels (IPSec / WireGuard)               │
│  • Hub ↔ State DC: encrypted GSWAN links                           │
│  • Firewall: whitelist-only between network segments               │
│                                                                    │
│  LAYER 3: EDGE SECURITY                                            │
│  • Hardened OS (CIS benchmarks)                                    │
│  • Encrypted local storage                                         │
│  • Secure boot where supported                                     │
│  • Remote attestation                                              │
│                                                                    │
│  LAYER 4: API SECURITY                                             │
│  • API gateway with auth, rate limiting, input validation          │
│  • OWASP Top 10 compliance                                        │
│  • TLS 1.3 for all API traffic                                     │
│  • No API key sharing; per-user credentials                        │
│                                                                    │
│  LAYER 5: APPLICATION SECURITY                                     │
│  • Authentication: LDAP/AD (Gujarat Police directory)              │
│  • MFA: mandatory for Investigator and Command roles               │
│  • Session: JWT with short TTL (15 min), refresh token rotation    │
│  • CSRF, XSS, injection protection                                │
│                                                                    │
│  LAYER 6: DATABASE SECURITY                                        │
│  • Encryption at rest: AES-256 for all stores                      │
│  • Row-level security in PostgreSQL (jurisdiction-scoped)          │
│  • Database credentials in secrets manager (Vault)                 │
│  • No direct DB access; all through API layer                      │
│                                                                    │
│  LAYER 7: STORAGE SECURITY                                         │
│  • Object storage: server-side encryption, bucket policies         │
│  • Evidence bucket: WORM (Write Once Read Many) mode               │
│  • Access logging on all storage operations                        │
│                                                                    │
│  LAYER 8: IDENTITY SECURITY                                        │
│  • Person feature vectors are mathematical representations,        │
│    not photographs stored as identity records                      │
│  • PII handling: minimized, encrypted, access-controlled           │
│                                                                    │
│  LAYER 9: EVIDENCE SECURITY                                        │
│  • Immutable storage with integrity hash verification              │
│  • Chain-of-custody metadata                                       │
│  • Export requires authorization + audit log entry                  │
│                                                                    │
│  LAYER 10: AUDIT SECURITY                                          │
│  • Audit logs: append-only, tamper-evident                         │
│  • Audit store: separate from operational databases                │
│  • Anomaly detection on access patterns                            │
│  • Regular audit reports for oversight bodies                      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

# 31. IAM: RBAC + ABAC

Role-based access control (RBAC) alone is insufficient. The system uses **RBAC + Attribute-Based Access Control (ABAC)** combining:

```
Role
  +
Jurisdiction
  +
Case assignment
  +
Purpose
  +
Data classification
  +
Time-of-access
```

### 31.1 Role Definitions

| Role | Description | Count (est.) |
|------|-------------|-------------|
| **Operator** (PSI/ASI) | Monitor live feeds, respond to alerts, log incidents | ~1,500+ |
| **Investigator** (PI/DySP) | Search, trace, timeline, graph, evidence, case management | ~500+ |
| **Command Officer** (SP/DIG/IGP) | Statewide/district overview, trends, response tracking | ~50–100 |
| **Field Officer** | Mobile access to incident details, location, basic search | ~2,000+ |
| **System Administrator** (IT/NIC) | Camera onboarding, system config, user management | ~20–50 |
| **Security Administrator** | Security config, access reviews, incident response | ~5–10 |
| **Auditor** | Read-only audit log access, compliance review | ~5–10 |

### 31.2 Access Matrix

```
                          Operator  Investigator  Command  Field  SysAdmin  SecAdmin  Auditor
                          ────────  ────────────  ───────  ─────  ────────  ────────  ───────
Live camera view           ✓(own)    ✓(own dist)   ✓(all)  ✗       ✗         ✗         ✗
Camera health              ✓(own)    ✗             ✓(all)  ✗       ✓         ✗         ✗
Alert view                 ✓(own)    ✓(own dist)   ✓(all)  ✓(own)  ✗         ✗         ✗
Alert acknowledge          ✓(own)    ✓(own)        ✓(all)  ✗       ✗         ✗         ✗
Search observations        ✗         ✓(case+jur)   ✓(all)  ✗       ✗         ✗         ✗
Cross-district search      ✗         ✓(approved)   ✓       ✗       ✗         ✗         ✗
View trajectory            ✗         ✓(case)       ✓       ✗       ✗         ✗         ✗
View investigation graph   ✗         ✓(case)       ✓       ✗       ✗         ✗         ✗
Generate evidence pkg      ✗         ✓(case)       ✗       ✗       ✗         ✗         ✗
Manage watchlist           ✗         ✓(own)        ✓       ✗       ✗         ✗         ✗
Case management            ✗         ✓(assigned)   ✓(view) ✗       ✗         ✗         ✗
State overview             ✗         ✗             ✓       ✗       ✗         ✗         ✗
Analytics/trends           ✗         ✓(own dist)   ✓       ✗       ✗         ✗         ✗
Incident management        ✓(own)    ✓(own dist)   ✓       ✓(view) ✗         ✗         ✗
Field incident view        ✗         ✗             ✗       ✓(own)  ✗         ✗         ✗
Camera onboarding          ✗         ✗             ✗       ✗       ✓         ✗         ✗
User management            ✗         ✗             ✗       ✗       ✓         ✗         ✗
System configuration       ✗         ✗             ✗       ✗       ✓         ✗         ✗
Security configuration     ✗         ✗             ✗       ✗       ✗         ✓         ✗
Access reviews             ✗         ✗             ✗       ✗       ✗         ✓         ✓
Audit log access           ✗         ✗             ✓(own)  ✗       ✗         ✓         ✓
Video clip export          ✗         ✓(logged)     ✗       ✗       ✗         ✗         ✗

Jurisdiction:
  "own"      = user's police station
  "own dist" = user's district
  "case"     = cameras/observations linked to user's assigned case
  "case+jur" = case-bound + jurisdiction-scoped
  "approved" = requires supervisor approval for cross-jurisdiction
  "all"      = statewide (Command and above)
```

---

# 32. AI Governance

### 32.1 Model Lifecycle Governance

```
MODEL REGISTRY
  │  Every model has: ID, version, training data hash,
  │  architecture, validation metrics, bias assessment,
  │  performance benchmarks, owner
  ▼
MODEL APPROVAL
  │  Review: accuracy, bias, edge cases, legal implications
  │  Approver: AI Governance Board (technical + legal + operational)
  ▼
DEPLOYMENT
  │  Canary → percentage rollout → full deployment
  │  Shadow mode for new models: run alongside production, compare results
  ▼
PRODUCTION INFERENCE
  │  Every inference tagged with model_id + model_version
  ▼
PERFORMANCE MONITORING
  │  Continuous: precision, recall, confidence distribution
  │  Sample-based: human validation of random observations
  ▼
DRIFT DETECTION
  │  Alert if: confidence distribution shifts, detection rate anomaly,
  │  false positive rate increase, accuracy degradation
  ▼
ACCURACY REVIEW (quarterly)
  │  Ground-truth validation against manually labeled samples
  ▼
HUMAN FEEDBACK LOOP
  │  Investigator feedback: "this association was wrong/correct"
  │  Flows back to model improvement pipeline
  ▼
MODEL UPDATE
  │  Retrain with new data + feedback → re-enter approval workflow
  └──► Back to MODEL REGISTRY
```

### 32.2 Model Card (required for every production model)

```
MODEL CARD
──────────
  model_id            : vehicle-detect-v3.2
  model_version       : 3.2.1
  model_hash          : sha256:...
  architecture        : YOLOv8-L
  training_data       : GJ-vehicle-dataset-v5 (hash: sha256:...)
  training_data_size  : 45,000 images
  validation_accuracy : mAP@0.5 = 0.94
  bias_assessment     : Tested across day/night, rain, haze, all vehicle classes
  known_limitations   : Two-wheeler detection drops to 0.81 in heavy rain
  deployment_date     : 2026-07-15
  owner               : AI Team Lead
  approved_by         : AI Governance Board
  next_review_date    : 2026-10-15
```

---

# 33. Human-in-the-Loop

The system distinguishes three levels:

```
Level 1: AI SUGGESTION
        │
        │  AI produces observation, association, alert
        │  Carries confidence score and explanation
        │  Allowed actions: automated indexing, correlation, alerting
        │
        ▼
Level 2: HUMAN VERIFICATION
        │
        │  Operator/investigator reviews AI output
        │  Confirms, corrects, or dismisses
        │  Required before: identity assertion, case linkage,
        │  evidence generation, operational dispatch
        │
        ▼
Level 3: OPERATIONAL ACTION
        │
        │  Authorized officer takes action based on verified intelligence
        │  Fully audited
        │  Platform records: who verified, who acted, when, on what basis
```

### What AI Must NOT Do Independently

| Prohibited Autonomous Action | Reason |
|------------------------------|--------|
| Declare guilt or innocence | Judicial determination, not AI function |
| Create a criminal identity record as fact | Identity is probabilistic until human-confirmed |
| Trigger irreversible operational action | Arrest, detention require human judgment |
| Replace investigator judgment | AI supports, does not replace |
| Share investigation data without authorization | Access control is human-governed |

---

# 34. Privacy & Data Governance

### 34.1 Governance Policies

| Policy Area | Rule |
|------------|------|
| **Purpose** | Data collected and processed only for authorized law enforcement purposes |
| **Collection** | Minimum data necessary; no bulk collection beyond operational need |
| **Access** | Case-bound, jurisdiction-scoped, role-limited, audited |
| **Use** | Investigation and incident response only; no unauthorized secondary use |
| **Sharing** | Between authorized officers on same case; cross-jurisdiction requires approval |
| **Retention** | Defined per data type (see §35); enforced automatically |
| **Deletion** | Automatic at retention expiry unless case-held |
| **Case hold** | Data linked to active case exempt from deletion until case closed + hold released |
| **Audit** | Every sensitive query logged: user, case ID, purpose, timestamp, query, result scope |

### 34.2 Sensitive Query Logging

Every investigation-class query produces:

```
QUERY AUDIT RECORD
──────────────────
  user_id          : PI-SHARMA-4421
  role             : INVESTIGATOR
  case_id          : CASE-2026-AHM-SAT-0421
  purpose          : Vehicle trajectory for FIR investigation
  timestamp        : 2026-08-19T20:10:14+05:30
  query_type       : VEHICLE_SEARCH
  query_params     : { plate: "GJ01AB1234", time_from: ..., time_to: ... }
  result_count     : 5 observations
  data_accessed    : [obs-11, obs-12, obs-13, obs-14, obs-15]
  export           : false
  client_ip        : 10.x.x.x
```

### 34.3 Regulatory Compliance

| Regulation | Applicability | Compliance Approach |
|-----------|---------------|-------------------|
| **DPDP Act 2023** | Processing of personal data | Purpose limitation, data minimization, DPO appointment, breach notification |
| **IT Act 2000/2008** | Cyber security, electronic records | Encryption, access control, audit trails, Sec 43A compliance |
| **Indian Evidence Act (Sec 65B)** | Electronic evidence | Certificate generation, hash chain, provenance (see §27.4) |
| **MeitY Cloud Guidelines** | Government cloud deployment | Deploy on GI Cloud / approved infrastructure |
| **NIC Security Guidelines** | Government IT systems | NIC security framework compliance |
| **IS/ISO 27001** | Information security | ISMS implementation |
| **CERT-In Directives** | Incident reporting | 6-hour incident reporting, 180-day log retention |
| **Gujarat State IT Policy** | State government IT | Alignment with state IT department requirements |

### 34.4 Data Sovereignty

```
ALL data MUST reside within India.

  ✓ State Data Center in Gujarat (Gandhinagar SDC)
  ✓ DR site within Gujarat or adjacent state
  ✓ No cloud services with data leaving Indian borders
  ✓ No external API calls that transmit observation data abroad
  ✓ No AI model APIs hosted outside India
  ✓ AI model training: on Indian infrastructure only

Approved infrastructure:
  ✓ Gujarat State Data Center (primary)
  ✓ NIC Data Center (backup)
  ✓ MeghRaj / GI Cloud (burst compute, if approved)
  ✓ On-premise at district hubs
```

---

# 35. Data Lifecycle

```
CAPTURE → PROCESS → STORE → INDEX → CORRELATE → INVESTIGATE → CASE-LINK → RETAIN → DELETE/ARCHIVE
```

### Retention by Data Type

| Data Type | Hot (SSD) | Warm (HDD) | Cold (Archive) | Evidence Hold | Deletion |
|-----------|-----------|------------|----------------|---------------|----------|
| Raw video | 7 days | 30 days | 90 days | Indefinite | Auto at 90d unless held |
| Key frames | 30 days | 90 days | 1 year | Indefinite | Auto at 1yr unless held |
| Observations | 90 days | 1 year | 3 years | Indefinite | Auto at 3yr unless held |
| Entity records | Always hot | — | Archive >2yr | Indefinite | Archive only |
| Graph relationships | Always hot | — | Archive >2yr | Indefinite | Archive only |
| Feature vectors | 90 days | 1 year | — | Indefinite | Auto at 1yr unless held |
| Alerts | 30 days | 90 days | 1 year | Indefinite | Auto at 1yr unless held |
| Cases | Always hot | — | — | Indefinite | Never auto-deleted |
| Evidence packages | Always hot | — | — | Indefinite | Never auto-deleted |
| Audit logs | 1 year | 3 years | 7 years | Indefinite | Auto at 7yr |
| Camera health logs | 30 days | 90 days | 1 year | — | Auto at 1yr |

> [!NOTE]
> **Evidence Hold**: When any data is linked to an active case or evidence package, it is exempt from retention lifecycle and preserved indefinitely until the case is closed and hold is explicitly released by authorized officer.

---

# 36. Observability / NOC

### 36.1 Monitoring Domains

| Domain | Key Metrics | Tool |
|--------|------------|------|
| **Camera health** | Online/offline per camera, uptime %, last heartbeat age, stream quality | Custom + Prometheus |
| **Stream health** | Decode success rate, frame drop rate, bitrate anomaly | Custom |
| **Edge health** | CPU, GPU utilization, memory, disk, inference throughput, buffer depth | Prometheus + node_exporter |
| **Network** | Latency (edge→hub, hub→DC), bandwidth utilization, packet loss | Prometheus + SNMP |
| **Kafka** | Consumer lag, partition count, throughput, replication status | Prometheus (JMX) |
| **Databases** | Query latency (p50/p95/p99), connection pool, replication lag, disk | pg_stat + Prometheus |
| **AI inference** | Latency per model, throughput, confidence distribution, detection rate | Custom metrics |
| **Search** | Query latency, index health, shard balance | OpenSearch metrics |
| **Graph** | Query latency, node/relationship counts, cache hit rate | Neo4j metrics |
| **Storage** | Capacity used/remaining, IOPS, lifecycle policy execution | MinIO metrics |
| **API** | Response time (p50/p95/p99), error rate, rate limit hits | API gateway metrics |
| **Security** | Failed auth attempts, anomalous access patterns, bulk export attempts | SIEM / OpenSearch |

### 36.2 Alerting & Escalation

```
L1 — NOC Operator (24×7)
  │  Camera offline, edge warning, minor performance degradation
  │  Response: Acknowledge, basic troubleshooting, escalate if unresolved
  ▼
L2 — Platform Engineer (on-call)
  │  Service degradation, Kafka lag, DB issues, AI performance
  │  Response: Diagnose, remediate, escalate if systemic
  ▼
L3 — Team Lead / Architect
  │  Systemic failures, data integrity, security incidents
  │  Response: Incident management, root cause, design fix
  ▼
Management
  │  Major outage, data breach, compliance incident
  │  Response: Executive communication, CERT-In notification if required
```

---

# 37. Failure Architecture

> [!IMPORTANT]
> Design for failure. Every component will fail. The question is: what continues to work?

```
FAILURE                         BEHAVIOR
──────────────────────────────  ─────────────────────────────────────
Camera fails                    → Other cameras continue;
                                  observation gap for that camera only

Camera network fails            → Edge buffers locally;
                                  sync when reconnected

Edge server fails               → Camera NVR continues recording;
                                  observations delayed until edge recovers;
                                  neighboring edge servers not affected

District hub fails              → Edges operate independently (detection continues);
                                  observations queue at edge;
                                  district correlation paused;
                                  state DC continues for other districts

GSWAN segment fails             → Edge + hub operate locally;
                                  observations queue and sync when restored;
                                  state platform continues for connected districts

Kafka broker fails              → Remaining brokers serve (3× replication);
                                  automatic rebalance

AI service degraded             → Observations delayed, not lost (backpressure);
                                  video remains available for manual review

Graph DB unavailable            → Raw observations remain authoritative in PostgreSQL;
                                  search works via OpenSearch;
                                  graph queries degraded until restored

Search unavailable              → PostgreSQL direct queries (slower but functional);
                                  underlying records remain authoritative

State DC power failure          → DR site activates (see §38);
                                  edges and hubs continue local operation

Evidence store unavailable      → Evidence references preserved in PostgreSQL;
                                  video clips accessible from edge/hub cache;
                                  generation queued until storage restored
```

**Principle**: No single component failure causes total system failure. Graceful degradation, not cascade failure.

---

# 38. HA / DR

### 38.1 Tiered RPO / RTO

Different data tiers have different recovery requirements:

| Tier | Data | RPO | RTO | DR Strategy |
|------|------|-----|-----|-------------|
| **Tier 1 (Critical)** | IAM, Case, Investigation graph, Evidence metadata, Audit | **5 min** | **1 hour** | Synchronous replication to DR |
| **Tier 2 (Operational)** | Search index, Alerts, Observation metadata, Camera registry | **15 min** | **4 hours** | Async replication + rebuild from Tier 1 |
| **Tier 3 (Bulk)** | Historical video, Frames, Feature vectors, Analytics | **1 hour** | **24 hours** | Async replication, delayed sync |

### 38.2 HA Architecture

```
EDGE LEVEL
  Edge server: automatic restart on failure
  Camera NVR: independent recording continues
  Target: 99% uptime per edge

DISTRICT HUB LEVEL
  Hub services: containerized, auto-restart
  Hub storage: RAID + local backup
  Target: 99.5% uptime per hub

STATE DATA CENTER
  PostgreSQL: Primary + 2 synchronous replicas (auto-failover via Patroni)
  Kafka: 5-broker cluster, survive 2 failures
  Redis: 6-node cluster, survive 2 failures
  <!-- Superseded for MVP — see docs/v4.1_decisions.md §5 -->
  Neo4j: 3-core causal cluster
  API servers: N+2 redundancy behind load balancer
  GPU cluster: N+1 redundancy
  Target: 99.9% uptime (≤8.7 hours downtime/year)
```

### 38.3 DR Architecture

```
PRIMARY: Gujarat State Data Center (Gandhinagar)
DR SITE: Secondary data center (>100 km from primary)

Replication:
  Tier 1: Synchronous (PostgreSQL streaming, real-time)
  Tier 2: Asynchronous (Kafka MirrorMaker2, 15-min lag)
  Tier 3: Batch (object storage replication, hourly)

Failover procedure:
  DNS failover:        5 minutes
  Database promotion:  15 minutes
  Service startup:     1–2 hours (Tier 1), 4 hours (Tier 2)
  Validation:          1–2 hours
  Full restoration:    24 hours (Tier 3 data available)

DR DRILL: Quarterly (mandatory)
  Full failover to DR → run 24 hours → validate all services → failback
  Documented findings → remediation plan
```

### 38.4 Backup Strategy

| Data | Frequency | Retention | Method | Location |
|------|-----------|-----------|--------|----------|
| PostgreSQL | Continuous WAL + daily full | 30 daily, 12 monthly | pg_basebackup + WAL archive | DR + offline |
| Neo4j | Daily full | 30 daily | Neo4j backup | DR |
| OpenSearch | Daily snapshot | 14 daily | Snapshot to S3 | DR |
| Object storage | Continuous replication | Per retention policy | MinIO replication | DR |
| Configuration | On every change | 90 days | Git (infrastructure as code) | Multiple |
| Kafka | Topic mirroring | 7 days | MirrorMaker2 | DR |

---

# 39. Deployment Architecture

### Physical Hierarchy

```
50,000+ CAMERAS (heterogeneous, multi-vendor, multi-VMS)
        │
        │ Integration Fabric (adapters, normalization)
        ▼
LOCAL EDGE (x 250+)
  │  Police station / junction / local site
  │  GPU edge device (Jetson / small GPU server)
  │  10–60 cameras each
  │  Local buffer, AI inference, health monitoring
  │
  │  GSWAN / local network
  ▼
DISTRICT / REGIONAL HUB (x 33)
  │  One per district + major city centers
  │  Multi-GPU server rack
  │  Aggregation, higher-accuracy AI, district investigation
  │  100 TB+ district storage
  │
  │  GSWAN backbone
  ▼
STATE DATA CENTER (Gandhinagar)
  │  GPU cluster + compute + storage cluster
  │  All databases, event backbone, API layer
  │  Cross-district correlation, state-wide intelligence
  │  500 TB+ storage (growing to PB)
  │
  │  Dedicated DR link
  ▼
DR SITE (>100 km from primary)
  │  Replicated databases + storage
  │  Cold standby compute (activatable)
```

### Network: GSWAN

```
GSWAN connects:
  - State HQ (Gandhinagar)
  - 33 District HQs
  - 250+ Taluka offices
  - Major police stations

Our bandwidth requirement:
  Sustained: ~1 Gbps statewide (metadata + key frames)
  Burst: ~500 Mbps (on-demand clip pull)
  Well within GSWAN capacity due to edge processing architecture.
```

This architecture supports **both urban and rural** environments. Rural sites with limited connectivity get more aggressive edge processing and larger local buffers.

---

# 40. Scalability Architecture

### 40.1 Three Capacity Stages

| Stage | Cameras | Trigger | Scaling Actions |
|-------|---------|---------|----------------|
| **Stage 1** | 50,000+ | Initial statewide deployment | Baseline infrastructure as designed |
| **Stage 2** | ~80,000 | Urban expansion, new highways, municipal additions | Add edge nodes, add GPU workers, add event partitions, add DB replicas |
| **Stage 3** | 100,000+ | Private/partner cameras, new districts, future growth | Add regional gateways, add search shards, add object storage capacity |

### 40.2 Scaling Mechanisms

| Component | Scaling Method | No Architectural Change |
|-----------|---------------|------------------------|
| Edge processing | Add edge nodes (1 per new PS or cluster) | ✓ |
| Regional gateways | Add district hub capacity (more GPU, more storage) | ✓ |
| AI workers | Add GPU servers to state DC pool | ✓ |
| Event backbone | Add Kafka partitions, add brokers | ✓ |
| Database (PostgreSQL) | Add read replicas, increase partitioning | ✓ |
| Graph (Neo4j) | Add read replicas, increase core cluster | ✓ |
| Search (OpenSearch) | Add shards, add data nodes | ✓ |
| Vector DB | Add shards, increase capacity | ✓ |
| Object storage | Add capacity (MinIO nodes) | ✓ |
| API layer | Add stateless API server instances | ✓ |
| Network | Increase GSWAN link capacity where needed | ✓ |

**No architectural rewrite at any stage.** The architecture scales by adding infrastructure.

---

# 41. Existing-System Migration Strategy

> [!IMPORTANT]
> Do NOT migrate everything at once. Integrate, normalize, enable — in that order. Existing VMS/NVR/command centers continue operating throughout.

### Eight-Step Migration

```
STEP 1: INVENTORY
  │  Catalogue every existing CCTV deployment in Gujarat
  │  Output: Master inventory (count, vendor, VMS, location, network, owner)
  ▼
STEP 2: CAPABILITY DISCOVERY
  │  For each deployment: determine protocol, API, stream access method
  │  Output: Integration feasibility matrix
  ▼
STEP 3: INTEGRATE EXISTING VMS/NVR
  │  Deploy appropriate adapter (RTSP, ONVIF, VMS API)
  │  Camera appears in platform Camera Registry
  │  Existing VMS continues to operate unchanged
  │  Output: Cameras visible in platform, dual-operated
  ▼
STEP 4: NORMALIZE METADATA
  │  Map vendor-specific camera data to canonical camera model
  │  Validate location, jurisdiction, capabilities
  │  Output: Canonical camera records in platform registry
  ▼
STEP 5: ENABLE EDGE PROCESSING
  │  Deploy edge server at or near the PS/site
  │  Connect to camera streams via integration fabric
  │  Begin AI processing → observations flowing
  │  Output: Observations being generated from existing cameras
  ▼
STEP 6: ENABLE INVESTIGATION
  │  Observations indexed in search, graphed in Neo4j
  │  Investigators can search existing camera data
  │  Output: Investigation capabilities live for this camera set
  ▼
STEP 7: ENABLE EVIDENCE
  │  Evidence provenance chain active
  │  Evidence packages generatable from this camera set
  │  Output: Full evidence capability
  ▼
STEP 8: OPTIMIZE & RETIRE DUPLICATES
  │  Only after operational validation (minimum 3 months)
  │  Retire duplicate analytics running on vendor VMS
  │  (Only if platform analytics proven superior)
  │  Existing VMS remains for recording and live view
  │  Output: Optimized, non-redundant deployment
```

> [!WARNING]
> **Never decommission the existing VMS for recording.** The platform is an intelligence layer, not a recording replacement. VMS/NVR continue to provide local recording and live view. The platform provides intelligence on top.

---

# 42. Camera Onboarding

Formal lifecycle, not ad-hoc connection.

```
PHASE 1: DISCOVERY
  │  Identify camera (site visit or VMS inventory scan)
  │  Record: vendor, model, protocol, network, location
  ▼
PHASE 2: REGISTRATION
  │  Create canonical camera record (§8)
  │  Assign platform cam_id
  │  Assign to jurisdiction, PS, edge node
  ▼
PHASE 3: CAPABILITY TEST
  │  Determine capabilities (§9): ANPR, PTZ, night, resolution
  │  Record in capability registry
  ▼
PHASE 4: NETWORK TEST
  │  Verify network path: camera → edge → hub → state DC
  │  Measure latency, bandwidth, reliability
  ▼
PHASE 5: TIME SYNCHRONIZATION
  │  Verify camera NTP sync
  │  Record time offset if camera clock is not NTP-synced
  ▼
PHASE 6: LOCATION VALIDATION
  │  Verify GPS coordinates (field survey vs. registered)
  │  Verify direction, FOV, mount height
  ▼
PHASE 7: STREAM VALIDATION
  │  Confirm stream decode: resolution, FPS, codec
  │  Verify quality: night, day, weather conditions
  ▼
PHASE 8: AI CALIBRATION
  │  Run detection models: baseline accuracy
  │  Configure ANPR zones (where plates are readable)
  │  Configure detection zones, exclusion zones
  │  Measure false positive baseline
  ▼
PHASE 9: SECURITY VALIDATION
  │  Verify credentials changed from default
  │  Verify network isolation
  │  Verify firmware version
  ▼
PHASE 10: PRODUCTION ACTIVATION
  │  Enable in production processing pipeline
  │  Add to operator console
  │  Notify jurisdiction
  ▼
CONTINUOUS: HEALTH MONITORING
  │  Heartbeat every 30 sec
  │  Quality monitoring
  │  Predictive maintenance triggers
```

**Target throughput**: 100–200 cameras onboarded per week during rollout phases.  
**Bulk onboarding**: Automated for VMS-integrated cameras (Steps 1–4 can be scripted from VMS API).

---

# 43. Vendor-Neutral Architecture

### 43.1 AI Abstraction

```
                 AI INFERENCE API (canonical)
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Vendor A     Vendor B      Open Source
       (e.g.,       (e.g.,       (e.g.,
       proprietary   partner     YOLOv8,
       ANPR)        analytics)   PaddleOCR)
```

The rest of the system only consumes **Canonical Observations** (§14). It never knows or cares which AI vendor produced the detection.

### 43.2 Anti-Lock-In Principles

| Principle | Implementation |
|-----------|---------------|
| **Open data formats** | Canonical observation schema, standard JSON, Parquet for analytics |
| **Open interfaces** | All inter-component communication via documented REST/gRPC APIs |
| **Exportable data** | Full data export capability for all platform-generated data |
| **Replaceable components** | Each major component (AI, DB, search, graph, event bus) can be replaced independently |
| **No vendor-specific AI dependency** | AI models wrap behind canonical inference API |
| **Standard protocols** | RTSP, ONVIF for camera integration; no vendor-locked protocols |

### 43.3 Procurement Requirement

> Every major component procured must expose **documented APIs and data export mechanisms**. Avoid architectures where:

```
❌ Vendor VMS → Vendor AI → Vendor Database → Vendor Dashboard
```

Instead:

```
✓ Vendor Camera → Standard Interface (RTSP/ONVIF) → GoG Platform
✓ Vendor VMS → VMS Adapter → GoG Platform
✓ Vendor AI (optional) → Canonical Observation API → GoG Platform
```

---

# 44. API Architecture

### 44.1 API Domains

```
CAMERA DOMAIN            INVESTIGATION DOMAIN
  /api/v1/cameras          /api/v1/cases
  /api/v1/camera-health    /api/v1/investigate
                           /api/v1/graph

OBSERVATION DOMAIN       EVIDENCE DOMAIN
  /api/v1/observations     /api/v1/evidence
  /api/v1/entities
  /api/v1/search         OPERATIONAL DOMAIN
                           /api/v1/incidents
CORRELATION DOMAIN         /api/v1/alerts
  /api/v1/trajectory       /api/v1/dispatch
  /api/v1/correlate
                         INTEGRATION DOMAIN
GIS DOMAIN                 /api/v1/integration/cctns
  /api/v1/gis              /api/v1/integration/vahan
  /api/v1/locations        /api/v1/integration/erss

WATCHLIST DOMAIN         ADMINISTRATION DOMAIN
  /api/v1/watchlists       /api/v1/admin
                           /api/v1/audit
ANALYTICS DOMAIN           /api/v1/health
  /api/v1/analytics        /api/v1/models
```

### 44.2 API Gateway

All APIs pass through a single gateway:

```
Client request
        ↓
API GATEWAY
  ├── Authentication (LDAP/JWT verification)
  ├── Authorization (RBAC + ABAC evaluation)
  ├── Rate limiting (per-user, per-role)
  ├── Input validation
  ├── Audit logging (every request)
  └── Routing to backend service
        ↓
Service
        ↓
Response (filtered by authorization scope)
```

### 44.3 Real-Time APIs

```
WebSocket: /ws/alerts       Real-time alert push to operators
WebSocket: /ws/cameras      Camera status live updates
WebSocket: /ws/incidents    Incident status updates
SSE:       /sse/observations  Observation stream (for dashboards)
```

---

# 45. Application Architecture

Seven user roles, not three.

### 45.1 Application Matrix

| Application | Primary User | Platform | Key Functions |
|-------------|-------------|----------|---------------|
| **Operator Console** | PSI / ASI | Web (desktop) | Live cameras, alerts, camera health, incident logging |
| **Investigator Workspace** | PI / DySP | Web (desktop) | Search, trace, timeline, graph, evidence, case management |
| **Command Dashboard** | SP / DIG / IGP | Web (large screen / desktop) | State map, incidents, trends, district health, coverage |
| **Field Officer App** | Constable / SI (field) | Mobile (responsive web / PWA) | Incident details, location, basic alerts, status updates |
| **System Admin Console** | IT / NIC | Web (desktop) | Camera onboarding, user management, system config, health |
| **Security Admin Console** | CISO / Security team | Web (desktop) | Access reviews, security config, incident response, threat monitoring |
| **Audit Interface** | Auditor / oversight | Web (desktop, read-only) | Audit log search, compliance reports, access review |

---

# 46. Investigator Workspace

> This is the **most important application**. It must feel like an investigation tool, not a dashboard.

```
┌────────────────────────────────────────────────────────────────────┐
│  INVESTIGATOR WORKSPACE — PI Sharma, Satellite PS                  │
│  Case: CASE-2026-AHM-SAT-0421 │ FIR/AHM/SAT/2026/4521            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─── CASE CONTEXT ──────────────────────────────────────────┐     │
│  │  Case: Robbery at SG Highway │ FIR: 4521 │ Status: Active │     │
│  │  Linked: 1 incident, 1 vehicle, 2 persons, 5 observations │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                    │
│  ┌─── SEARCH ────────────────────────────────────────────────┐     │
│  │  Type: [Vehicle ▼]    Plate: [GJ01AB1234        ]         │     │
│  │  From: [2026-08-19 18:00]  To: [2026-08-19 20:00]        │     │
│  │  Area: [Ahmedabad City ▼]  [🔍 Search] [Advanced]         │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                    │
│  ┌─── RESULTS ───────────────────────────────────────────────┐     │
│  │  Vehicle V-4521 │ GJ01AB1234 │ White Sedan                │     │
│  │  5 observations, all PLAUSIBLE │ 2 associated persons      │     │
│  │                                                           │     │
│  │  ┌─ TIMELINE ─────────────────────────────────────────┐   │     │
│  │  │  18:14 ● C101  SG Highway / ISRO                   │   │     │
│  │  │         │      [Frame] [Clip] Conf: 0.96            │   │     │
│  │  │         │  ↓ 7 min, 3.2 km (27 km/h ✓)            │   │     │
│  │  │  18:21 ● C113  SG Highway / Drive-In               │   │     │
│  │  │         │      [Frame] [Clip] Conf: 0.98            │   │     │
│  │  │         │  ↓ 8 min, 2.8 km (21 km/h ✓)            │   │     │
│  │  │  18:29 ● C127  SG Highway / Thaltej                │   │     │
│  │  │         │      [Frame] [Clip] Conf: 0.94            │   │     │
│  │  │         │  ⚠ Person P-17 near vehicle (0.82)       │   │     │
│  │  │         │  ↓ 8 min, 4.1 km (31 km/h ✓)            │   │     │
│  │  │  18:37 ● C144  SG Highway / Sola                   │   │     │
│  │  │         │      [Frame] [Clip] Conf: 0.97            │   │     │
│  │  │         │  ↓ 11 min, 8.7 km (47 km/h ✓)           │   │     │
│  │  │  18:48 ● C171  SP Ring / Motera                    │   │     │
│  │  │                [Frame] [Clip] Conf: 0.93            │   │     │
│  │  │                ⚠ Person P-22 exiting (0.71)        │   │     │
│  │  └────────────────────────────────────────────────────┘   │     │
│  │                                                           │     │
│  │  ┌─ MAP ──────────────────┐  ┌─ GRAPH ──────────────┐    │     │
│  │  │  Trajectory on Gujarat │  │   V-4521              │    │     │
│  │  │  road map, camera      │  │    ├── P-17 (0.82)    │    │     │
│  │  │  markers, direction    │  │    ├── P-22 (0.71)    │    │     │
│  │  │  arrows                │  │    ├── C101→C171      │    │     │
│  │  └────────────────────────┘  │    └── I-4521         │    │     │
│  │                              └───────────────────────┘    │     │
│  │  ┌─ VIDEO ────────────────────────────────────────────┐   │     │
│  │  │  [Clip player: selected observation's video]       │   │     │
│  │  │  [◄ Prev] [► Play/Pause] [Next ►] [Full screen]   │   │     │
│  │  └────────────────────────────────────────────────────┘   │     │
│  │                                                           │     │
│  │  [📋 Generate Evidence Package]  [📌 Add to Case]         │     │
│  │  [🔗 Link to Incident]          [📤 Export Timeline]      │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

# 47. Command Architecture

Command officers see **operational intelligence**, not unrestricted investigative content.

```
┌────────────────────────────────────────────────────────────────────┐
│  COMMAND DASHBOARD — DGP Office, Gandhinagar                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─── STATE OVERVIEW ────────────────────────────────────────┐     │
│  │  Cameras: 52,341 │ Online: 49,872 (95.3%) │ Offline: 2,469│     │
│  │  Active Incidents: 47 │ Open Alerts: 312                   │     │
│  │  Today's Observations: 14.2M │ WL Matches (24h): 23       │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                    │
│  ┌─── STATE MAP ─────────────────────────────────────────────┐     │
│  │  Gujarat map with:                                         │     │
│  │  • District camera health (color coded: green/yellow/red)  │     │
│  │  • Active incident markers                                 │     │
│  │  • Hotspot heat overlay (crime density)                    │     │
│  │  • Camera coverage gaps (where coverage < threshold)       │     │
│  │  • Click district → drill down                             │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                    │
│  ┌── DISTRICT HEALTH ──────┐  ┌── TRENDS (7 day) ──────────┐     │
│  │  Ahmedabad   97.2% 🟢   │  │  Incidents:  ↑ 12%          │     │
│  │  Surat       96.8% 🟢   │  │  Alerts:     ↓ 3%           │     │
│  │  Vadodara    94.1% 🟡   │  │  WL Matches: ↑ 8%           │     │
│  │  Rajkot      93.7% 🟡   │  │  Cam Uptime: → 95.3%        │     │
│  │  Kutch       87.3% 🔴   │  │  Avg Response: 4.2 min      │     │
│  │  [All 33 districts...]   │  │  [Detailed Analytics]       │     │
│  └──────────────────────────┘  └─────────────────────────────┘     │
│                                                                    │
│  ┌─── CRITICAL ALERTS (operational, not investigative) ──────┐     │
│  │  🔴 Wanted vehicle GJ05XX9999 — Surat — 5 min ago         │     │
│  │  🔴 Mass gathering detected — Vadodara — 12 min ago       │     │
│  │  🟡 Camera cluster offline — Kutch — 45 min ago           │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                    │
│  ⚠ Command officers see incident summaries and operational         │
│    status. Detailed investigation data (person searches, case      │
│    evidence, trajectories) is restricted to assigned investigators. │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

# 48. Operations & NOC

### 48.1 NOC Structure

```
NOC (24×7, State Data Center)
  │
  ├── Camera Health Monitoring
  │     Status of all 50K+ cameras
  │     Offline alerts, cluster offline escalation
  │     Field maintenance dispatch
  │
  ├── Edge & Hub Health
  │     Edge server status per PS
  │     Hub status per district
  │     GPU utilization, buffer depth
  │
  ├── Network Monitoring
  │     GSWAN link status
  │     Edge-to-hub latency
  │     Hub-to-DC latency
  │
  ├── AI Pipeline Monitoring
  │     Kafka consumer lag
  │     Inference throughput and latency
  │     Detection rate anomalies
  │     Model performance dashboards
  │
  ├── Storage Monitoring
  │     Capacity trending
  │     Lifecycle policy execution
  │     Evidence store integrity checks
  │
  ├── API & Application Monitoring
  │     API response times, error rates
  │     User session counts
  │     Dashboard performance
  │
  ├── Security Monitoring
  │     Failed auth, anomalous access
  │     Threat indicators
  │     Compliance status
  │
  └── DR Monitoring
        Replication lag
        DR site health
        Backup verification
```

### 48.2 SLA Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Platform uptime | 99.9% | Monthly |
| Camera uptime (state avg) | 95% | Daily |
| Observation latency (detection → searchable) | <5 sec | p95 |
| API response time | <500 ms | p95 |
| Search response time | <3 sec | p95 |
| Alert delivery (detection → operator screen) | <30 sec | p95 |
| Evidence package generation | <5 min | p95 |
| DR failover | <4 hours (Tier 1+2) | Drill |

---

# 49. Procurement Architecture

### 49.1 Procurement Route

| Component | Procurement | Notes |
|-----------|-------------|-------|
| Hardware (servers, GPU, storage, network) | GeM / government rate contract / RFP | Standard government procurement |
| Open-source software (PostgreSQL, Kafka, MinIO, etc.) | No license cost | Support AMC via SI or OEM |
| Commercial software (Neo4j, OS licenses) | GeM / direct | Evaluate open-source alternatives |
| AI models | In-house development + open-source | Avoid proprietary model lock-in |
| System Integration | RFP → SI partner | Implementation, deployment, training |
| AMC | Separate contract or bundled with SI | Post-deployment support |

### 49.2 Open Interface Requirement

> Every major component procured or deployed must expose **documented APIs and data export mechanisms**.

### 49.3 Government Data Ownership

```
Government of Gujarat retains:
  ✓ Ownership of all data generated by the platform
  ✓ Ownership of all trained models (if trained on government data)
  ✓ Right to export all data in standard formats
  ✓ Right to switch vendors for any component
  ✓ Source code escrow for custom-developed components

Vendor retains:
  ✓ IP of their pre-existing products
  ✗ No claim on government data
  ✗ No lock-in through proprietary data formats
```

---

# 50. Cost Architecture

### 50.1 CAPEX (Indicative)

| Component | Unit Cost (₹) | Quantity | Total (₹ Cr) |
|-----------|--------------|----------|-------------|
| State DC — GPU servers | 50–80 L | 4 | 2–3.2 |
| State DC — App/DB servers | 15–25 L | 20 | 3–5 |
| State DC — Storage (500 TB) | — | 1 | 2–4 |
| State DC — Networking | — | 1 | 1–2 |
| District hubs (x33) | 30–50 L | 33 | 10–16.5 |
| Edge servers (x250+) | 3–8 L | 250 | 7.5–20 |
| DR site | — | 1 | 3–5 |
| Software licenses | — | — | 3–5 |
| Network upgrades (GSWAN) | — | — | 5–10 |
| Implementation (SI) | — | — | 5–10 |
| Training | — | — | 1–2 |
| Contingency (15%) | — | — | 6–12 |
| **Total CAPEX** | | | **~46–95 Cr** |

### 50.2 OPEX (Annual, Indicative)

| Component | Annual (₹ Cr) |
|-----------|--------------|
| Team (state + district) | 5–8 |
| Infrastructure maintenance + AMC | 3–5 |
| Software licenses & support | 2–4 |
| Network (GSWAN share) | 1–2 |
| Power & cooling | 1–2 |
| Training (ongoing) | 0.5–1 |
| Security audit | 0.5–1 |
| **Total Annual OPEX** | **~13–23 Cr** |

### 50.3 Reuse Savings

> [!TIP]
> A major part of the government business case:

| Existing Asset | Reuse | Savings |
|---------------|-------|---------|
| Existing 50K+ cameras | Not replaced | ₹ hundreds of crores in camera procurement avoided |
| Existing VMS/NVR | Continue operating, integrated via fabric | No VMS replacement cost |
| Existing networks (GSWAN) | Leveraged for all connectivity | No new WAN buildout |
| Existing command centers | Enhanced, not replaced | No new command center construction |
| Existing storage (NVR-local) | Used for local recording | Reduced central storage requirement |

---

# 51. Deployment Phases

### 51.1 Five Phases with Go/No-Go Gates

```
PHASE 0 — ARCHITECTURE + PoC
─────────────────────────────
Duration: 2-4 weeks
Scale: 10-20 simulated cameras, synthetic data
Goal: Demonstrate architecture, core intelligence
Gate: Technical review approval

        │  GO / NO-GO: Technical + Architecture
        ▼

PHASE 1 — PILOT (Single District)
──────────────────────────────────
Duration: 3-4 months
Location: Ahmedabad City
Scale: 500-1,000 cameras (existing)
Deploy: Integration fabric, edge, detection, ANPR,
        basic search, operator console, camera health
Gate criteria:
  ✓ Technical: camera integration >95%, detection precision >90%
  ✓ Security: VAPT completed, RBAC validated
  ✓ Operational: NOC procedures validated, training completed
  ✓ AI accuracy: ANPR >85% on clear plates, detection >90%
  ✓ Governance: audit logging verified, privacy review completed
  ✓ Integration: CCTNS read-only integration tested

        │  GO / NO-GO: All six criteria
        ▼

PHASE 2 — MULTI-CITY
─────────────────────
Duration: 4-6 months
Locations: Ahmedabad, Surat, Vadodara, Rajkot, Gandhinagar
Scale: 5,000-10,000 cameras
Deploy (additional): Cross-camera correlation, trajectory,
        investigation graph, timeline, watchlist, evidence,
        investigator workspace, command dashboard (5-city)
Gate criteria:
  ✓ Technical: cross-city trajectory validated
  ✓ Security: multi-site security review
  ✓ Operational: real case investigation workflow validated
  ✓ AI accuracy: cross-camera association precision validated
  ✓ Governance: evidence admissibility review (legal team)
  ✓ Integration: CCTNS bidirectional tested

        │  GO / NO-GO: All six criteria
        ▼

PHASE 3 — DISTRICT + HIGHWAY
─────────────────────────────
Duration: 6-9 months
Scale: 20,000-35,000 cameras, all 33 districts
Deploy (additional): Full statewide command dashboard,
        event correlation, spatio-temporal feasibility,
        analytics, CCTNS/Dial 112/Vahan integration,
        multi-language support
Gate criteria:
  ✓ Technical: statewide search <3 sec
  ✓ Security: full VAPT + penetration test
  ✓ Operational: DR failover drill passed
  ✓ AI accuracy: model performance across all districts validated
  ✓ Governance: full data governance review, DPO appointed
  ✓ Integration: all external systems operational

        │  GO / NO-GO: All six criteria
        ▼

PHASE 4 — STATEWIDE + OPTIMIZATION
───────────────────────────────────
Duration: 6-12 months (ongoing)
Scale: 50,000+ cameras
Deploy (additional): Remaining cameras, advanced analytics,
        mobile field officer app, continuous model improvement,
        performance optimization
Ongoing: Camera onboarding pipeline, model retraining,
         capacity monitoring, Phase 5 (80K+) planning
```

### 51.2 Deployment Timeline

```
Month:  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
        ─────────────────────────────────────────────────────────────────────────
Phase 0 ████
Phase 1       ████████████
Phase 2                   ██████████████████
Phase 3                                     ████████████████████████
Phase 4                                                         ████████████████ → ongoing

Parallel:
Training      ──────────────────────────────────────────────────────────────────
NOC buildup        ─────────────────────────────────────────────────────────────
Security audit          ────────────────────────────────────────────────────────
Model improvement                    ───────────────────────────────────────────
```

---

# 52. Success Metrics

### Integration Metrics

| Metric | Target |
|--------|--------|
| % cameras onboarded without physical replacement | >95% |
| % VMS systems integrated (adapter-based) | 100% of identified VMS |
| Camera onboarding throughput | 100–200 cameras/week during rollout |
| Time to onboard one camera (automated) | <1 hour |
| Time to onboard one camera (manual) | <1 day |

### Investigation Metrics

| Metric | Target |
|--------|--------|
| Time to first useful lead (from investigator query) | <30 seconds |
| Time to reconstruct vehicle trajectory | <1 minute |
| Time to generate evidence package | <5 minutes |
| Search-to-results (any query type) | <3 seconds |
| Cross-district search capability | Available from Phase 2 |

### AI Metrics

| Metric | Target |
|--------|--------|
| Person detection precision | >90% |
| Vehicle detection precision | >92% |
| ANPR accuracy (clear plates, good angle) | >85% |
| ANPR accuracy (all conditions) | >70% |
| Cross-camera person association precision | >80% |
| Cross-camera vehicle association precision | >90% (plate-based) |
| False association rate | <5% |

### Operational Metrics

| Metric | Target |
|--------|--------|
| Camera uptime (state average) | >95% |
| Edge server availability | >99% |
| Platform uptime | >99.9% |
| Mean time to detect camera failure | <5 minutes |
| Mean time to recover edge server | <1 hour |
| DR failover completion | <4 hours |

### Governance Metrics

| Metric | Target |
|--------|--------|
| Case-bound investigation searches | 100% |
| Sensitive-data access audited | 100% |
| Model version traceability | 100% (every observation tagged) |
| Evidence provenance completeness | 100% (every evidence package has full chain) |
| Audit log integrity | 100% (tamper-evident, verified) |
| Data retention policy compliance | 100% (automated enforcement) |
| Security vulnerability remediation | <7 days (critical), <30 days (high) |

---

# 53. Final Architecture — One Sentence

> **A federated statewide CCTV integration and intelligence platform that connects heterogeneous existing CCTV systems, processes them through edge and regional infrastructure, converts video into persistent observations and entities, correlates those observations across time and space, integrates authorized police and government data, reconstructs incidents through an investigation graph, and produces traceable evidence and operational intelligence through secure, auditable, governed workflows.**

---

# 54. Hackathon Execution Plan

> [!IMPORTANT]
> This section covers **two concerns**: (A) what to build for the hackathon (the CCTV platform MVP), and (B) how to run the hackathon event itself (registration, judging, logistics, operations). Both must be planned together.

---

## 54.1 Event Scope & Format

### Assumptions (to be confirmed)

| Parameter | Assumed Value | Notes |
|-----------|-------------|-------|
| Duration | 24–48 hours | Typical police/gov hackathon format |
| Format | In-person (preferred) or hybrid | In-person enables live CCTV demo; hybrid extends reach |
| Participants | 50–150 registrants | Cap at 150% of venue capacity to account for ~65% show-up rate for free events |
| Teams | 10–30 teams | 3–5 members per team |
| Venue | Government venue / university / conference hall | Must have reliable power, network, AV |
| Judges | 5–10 | Police officers, tech leaders, government officials |
| Mentors | 5–10 | Domain + technical mentors |

### Event Structure

```
PRE-EVENT (T-2 weeks)
  Registration closes
  Team formation support
  Starter kit / dataset distribution
  Technical environment setup instructions

DAY 1
  09:00  Registration & check-in
  09:30  Opening ceremony + problem statement briefing
  10:00  Hacking begins
  12:00  Mentor office hours (Round 1)
  13:00  Lunch break
  14:00  Checkpoint 1: Team progress check
  16:00  Mentor office hours (Round 2)
  19:00  Dinner
  20:00  Hacking continues (overnight optional)

DAY 2
  08:00  Breakfast
  09:00  Checkpoint 2: Submission preparation guidance
  12:00  SUBMISSION DEADLINE
  12:30  Lunch
  13:00  Presentations begin (5–7 min per team + 3 min Q&A)
  16:00  Judging deliberation
  17:00  Awards ceremony + closing
  17:30  Networking / feedback collection
```

### Capacity Planning

```
Registration cap = Venue capacity × 1.5
                 = (e.g., 100 seats) × 1.5
                 = 150 registrations

Expected show-up = 150 × 0.65
                 = ~98 participants

Teams = 98 / 4 (avg team size)
      = ~25 teams

Presentations = 25 × 10 min
              = ~250 min (~4.2 hours)
              → Plan 3.5–4 hours (some teams may not submit)
```

---

## 54.2 What to Build (Platform MVP)

| Level | Scope | Priority |
|-------|-------|----------|
| **Level 1 — Must Work** | Camera simulator (10–20 cameras) → Detection → ANPR → Observation DB → Basic search → Operator dashboard → Map | Required |
| **Level 2 — Cross-Camera** | Vehicle trajectory (plate-based) → Timeline → Map trajectory → Cross-camera search | Important |
| **Level 3 — Differentiator** | Investigation graph → Person-vehicle association → Location-time search → Scene reconstruction | Differentiating |
| **Level 4 — Wow Factor** | Spatio-temporal feasibility scoring → Evidence package → Explainable confidence → Event correlation timeline | Exceptional |
| **Simulated** | Architecture diagrams showing 50K→80K→100K scale; edge processing concept; multi-role dashboards; integration fabric concept | Required |

### What NOT to Build

```
❌ Fancy dashboard animations or 3D maps
❌ Generic YOLO detection demo without intelligence layer
❌ Generic ANPR demo without cross-camera correlation
❌ Chatbot that says "there was a suspicious vehicle"
❌ Huge number of AI models
❌ Facial recognition just because it sounds impressive
❌ Fake 50,000-camera simulation with no meaningful intelligence
❌ Custom registration / auth system (use existing tools)
```

---

## 54.3 Technology Choices

| Component | Hackathon | Production |
|-----------|-----------|------------|
| Backend | Python (FastAPI) | Python / Go |
| AI | YOLOv8 + PaddleOCR | Custom / vendor models |
| Database | PostgreSQL (single) | PostgreSQL + PostGIS (clustered) |
| Graph | NetworkX (in-memory) | Neo4j Enterprise |
| Search | PostgreSQL full-text | OpenSearch |
| Vector store | FAISS (in-memory) | Milvus / Qdrant |
| Message queue | Redis pub/sub | Kafka |
| Object store | Local filesystem | MinIO |
| Cache | In-memory dict | Redis cluster |
| Frontend | React + Leaflet | React + Mapbox/Leaflet |
| Video | Pre-recorded files | RTSP live streams |
| Deployment | Docker Compose | Kubernetes |

---

## 54.4 Registration & Participant Management

### Platform Selection

| Option | Recommendation | Notes |
|--------|---------------|-------|
| **Eventbrite** | ✓ **Primary choice** | Tiered ticketing (Participant / Mentor / Judge); built-in email reminders; free for free events; custom questions |
| Google Forms | Fallback only | No payment support, no automated reminders, manual follow-up |
| HackerEarth / Devfolio | Alternative | Purpose-built for hackathons but may be proprietary / paid |

### Registration Data to Collect

```
REQUIRED FIELDS
  Full name
  Email
  Phone
  Organization / affiliation
  Role: Participant │ Mentor │ Judge │ Volunteer │ Observer
  Experience level: Student │ Junior │ Mid │ Senior
  Technical skills (checkboxes: Python, AI/ML, frontend, backend, etc.)
  Team name (if pre-formed) or "Looking for team"
  T-shirt size (if distributing)
  Dietary restrictions / allergies
  Accessibility needs / special requirements

LEGAL
  ☑ Agreement to Terms & Conditions
  ☑ Agreement to Code of Conduct
  ☑ Photo / video consent
  ☑ Privacy policy acknowledgment
```

### Registration Workflow

```
Registration opens (T-4 weeks)
        ↓
Automated confirmation email (immediate)
        ↓
Reminder email 1 (T-1 week)
        ↓
Reminder email 2 + logistics info (T-2 days)
        ↓
Registration closes (T-2 days)
        ↓
Day-of check-in (Eventbrite check-in app or manual)
        ↓
Post-event: attendance data exported for metrics
```

> [!WARNING]
> **Data security**: Registration data includes PII. Ensure the registration platform uses HTTPS/SSL. Restrict admin access to registration data (2FA required). Export and store data securely. Comply with applicable data protection regulations.

---

## 54.5 Communication Channels

### Channel Architecture

```
                     COMMUNICATION
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
        REAL-TIME      BROADCAST     PUBLIC
            │             │             │
     Slack or Discord   Email         Social Media
            │         (Eventbrite/      │
            │          Mailchimp)    Twitter/LinkedIn
            │             │          hashtag
            │             │             │
            └─────────────┼─────────────┘
                          │
                      ALL PARTICIPANTS
```

### Platform Decision

| Platform | Pros | Cons | Recommendation |
|----------|------|------|---------------|
| **Discord** | Free unlimited chat + voice; persistent history; easy screen sharing; no message limits | Less formal; fewer enterprise integrations | ✓ **Primary choice for hackathon** |
| Slack | Robust threads; search; integrations | Free tier: 90-day history limit; paid = ₹600+/user/mo | Good alternative if already in use |
| WhatsApp groups | Familiar in India; instant reach | No threads; group size limits; unprofessional for formal event | Supplement only (logistics group for organizers) |

### Channel Structure (Discord)

```
DISCORD SERVER: Gujarat CCTV Hackathon
─────────────────────────────────────

📢 ANNOUNCEMENTS
  #announcements        (organizer-only posting)
  #schedule             (pinned schedule, updates)
  #rules-and-faq        (code of conduct, FAQ, links)

💬 GENERAL
  #general              (open discussion)
  #introductions        (team intros, looking-for-team)
  #random               (off-topic)

🛠 TECHNICAL
  #tech-help            (setup issues, environment questions)
  #dataset-questions    (data clarifications)
  #api-help             (API / integration questions)
  #mentor-office-hours  (mentor Q&A during scheduled times)

👥 TEAMS (created on Day 1)
  #team-alpha
  #team-beta
  ...

🏆 SUBMISSIONS
  #submission-help      (submission process questions)
  #demo-prep            (presentation tips)

📊 ORGANIZERS (private)
  #organizer-ops        (internal coordination)
  #judge-coordination   (judge logistics)
  #incidents            (issues, escalations)
```

### Email Communications Schedule

| Timing | Email | Content |
|--------|-------|---------|
| Registration confirmation | Automated | Welcome, Discord invite, calendar hold |
| T-2 weeks | Logistics email | Venue details, parking, what to bring |
| T-1 week | Reminder + prep | Schedule, starter kit links, team formation deadline |
| T-2 days | Final reminder | Check-in time, venue map, emergency contacts |
| Day 1 morning | Day-of email | Wi-Fi credentials, room assignments, mentor schedule |
| T+1 day | Thank you | Survey link, results, photo gallery, next steps |

### Social Media

```
Event hashtag: #GujCCTVHack2026 (or similar)
Platforms: Twitter/X, LinkedIn
Content: Registration open, countdown, live updates, winner announcement
Assign: 1 social media volunteer during event
```

---

## 54.6 Submission Platform & Workflow

### Platform Selection

| Platform | Pros | Cons | Recommendation |
|----------|------|------|---------------|
| **Devpost** | All-in-one (submissions + judging + gallery); free for public events; judge dashboard; public project showcase | Requires participants to create Devpost account; less customizable | ✓ **Primary choice** |
| HackHQ | Structured judging; no participant accounts needed; live results | Less widely known; limited free tier | Good alternative |
| GitHub + Google Form | Familiar to developers; free | No integrated judging; manual collation | Fallback only |

### Submission Requirements

```
MANDATORY SUBMISSION FIELDS
─────────────────────────────

  Project name
  Team name + members
  Category (if multiple tracks)

  Problem statement (what police problem are you solving?)
  Solution description (how does your system work?)
  Architecture overview (diagram or description)

  Demo video (3–5 min, uploaded or YouTube link)
  Live demo URL (if deployed)
  Source code repository (GitHub / GitLab link)

  Tech stack used
  AI models used (with versions)
  Datasets used

  Scalability statement (how does this scale to 50K+ cameras?)
  Evidence / provenance approach (how do you preserve evidence integrity?)

OPTIONAL
  Slide deck
  Additional documentation
  Future roadmap
```

### Submission Timeline

```
T-0 (hacking starts)
  Submission portal opens on Devpost
  Link shared via Discord #announcements + email

T+20 hours
  Reminder: "4 hours to submission deadline"
  #submission-help channel active

T+23 hours
  Final reminder: "1 hour remaining"

T+24 hours (or scheduled deadline)
  SUBMISSION DEADLINE — portal closes
  Late submissions NOT accepted (enforced by platform)

T+24.5 hours
  Organizers verify: all submissions complete and accessible
  Assign submissions to judge panels
```

---

## 54.7 Judging Workflow & Criteria

### Judging Criteria (Rubric)

| Criterion | Weight | Description | Score Range |
|-----------|--------|-------------|-------------|
| **Investigation Intelligence** | 25% | Does the system go beyond detection to correlation, trajectory, graph, evidence? Is the architecture based on observations → entities → correlation → graph? | 1–10 |
| **Technical Architecture** | 20% | Is the architecture sound? Edge processing? Scalable to 50K+? Proper data flow? Multi-store strategy? | 1–10 |
| **Police Relevance** | 20% | Does it solve real police problems (§1)? Can an investigator actually use this? Is it case-bound, not mass surveillance? | 1–10 |
| **Working Demo** | 15% | Does the prototype actually work? Live demo quality? End-to-end flow visible? | 1–10 |
| **Innovation** | 10% | What is novel? Spatio-temporal feasibility? Explainable confidence? Evidence provenance? | 1–10 |
| **Presentation Quality** | 10% | Clear communication? Good architecture diagrams? Understood by non-technical judges? | 1–10 |

### Judge Panel Composition

```
TARGET: 5–10 judges

Composition:
  2–3  Senior police officers (SP / DIG / domain experts)
  2–3  Technology leaders (AI / systems / cloud)
  1–2  Government IT officials (NIC / IT Dept)
  1    Legal / privacy expert (optional but valuable)
  1    Industry / startup advisor

Judge-to-team ratio: aim 1 judge per 3–4 teams
Each project reviewed by ≥ 2 judges (average scores to reduce bias)
```

### Judging Process

```
STEP 1: ORIENTATION (T-1 week or Day 1 morning)
  Brief judges on:
  - Judging criteria and rubric (weights, score definitions)
  - Platform usage (Devpost judge dashboard)
  - Bias awareness (don't favor flashy UI over solid architecture)
  - Time management (strict 5-7 min presentations)
  - Conflict of interest disclosure

STEP 2: PRESENTATIONS (Day 2 afternoon)
  Format per team:
    5–7 min presentation / demo
    3 min judge Q&A
    Judges score immediately after each presentation (on platform)

STEP 3: DELIBERATION (after all presentations)
  Judges review aggregated scores
  Discuss top 5 teams
  Resolve ties
  Select winners by category (if applicable)

STEP 4: ANNOUNCEMENT
  Results announced at closing ceremony
  Score breakdown shared (transparency)
  All submissions visible on Devpost gallery (public showcase)
```

### Anti-Bias Measures

```
✓ Each project reviewed by ≥ 2 judges
✓ Scores averaged across judges
✓ Inter-judge variance flagged (if scores differ by >3 points, discuss)
✓ Judges cannot score teams they mentored
✓ Rubric provided in advance with clear scoring anchors (1 = poor, 5 = adequate, 10 = exceptional)
```

---

## 54.8 Technical Infrastructure (Event)

### Hosting for Event Platforms

| Service | Hosting | Cost | Notes |
|---------|---------|------|-------|
| Event website (info, schedule, FAQ) | GitHub Pages or Netlify | Free | Static site, auto-SSL, deploy from Git |
| Registration | Eventbrite (hosted) | Free for free events | No self-hosting required |
| Submissions | Devpost (hosted) | Free for public events | No self-hosting required |
| Communication | Discord (hosted) | Free | No self-hosting required |
| Participant starter kit / datasets | GitHub repo + Google Drive | Free | Large files on Drive, code on GitHub |
| Demo deployment (participant teams) | Docker on local machines or free cloud credits | Free / low | See cloud credits below |

### Cloud Credits for Participants

| Provider | Program | Credit | How to Get |
|----------|---------|--------|------------|
| **Google Cloud** | Google Cloud for Students | $300 | Student email verification |
| **AWS** | AWS Activate / Educate | $100–$1,000 | Apply via hackathon organizer portal |
| **Azure** | Azure for Students | $100 | Student email verification |
| **GitHub** | Student Developer Pack | Free Pro + tools | Student email verification |

> [!TIP]
> Apply for cloud credits **4+ weeks before the event**. AWS Activate and GCP for startups/hackathons often grant bulk credits if applied by the organizer.

### CI/CD for Event Infrastructure

```
Event website repo (GitHub)
        │
        │ Push to main
        ▼
GitHub Actions / Netlify auto-deploy
        │
        ▼
Live site updated (< 2 min)
        │
        ▼
SSL auto-provisioned (Let's Encrypt)
```

### Backup Strategy (Event Data)

```
Registration data: Export from Eventbrite daily during registration period
Submission data: Devpost maintains; organizer exports after deadline
Communication logs: Discord history persistent (free tier, no limit)
Scores: Export from Devpost / HackHQ after judging
Photos/videos: Upload to Google Drive (shared organizer account)

ALL BACKUPS: Stored in organizer Google Drive with restricted access
```

---

## 54.9 On-Site Logistics

### Network & Connectivity

```
REQUIREMENTS
─────────────

Internet:
  Dedicated connection (NOT shared public hotspot)
  Bandwidth: ≥ 100 Mbps symmetric (for 100 participants)
  Backup: Mobile hotspot (4G/5G) as fallback

Wi-Fi:
  SSID: GujCCTVHack (WPA2, password shared at check-in)
  Capacity: ≥ 200 concurrent devices (2 per participant)
  Access points: 1 per 30 devices (4–5 APs for 100 participants)
  Frequency: 5 GHz preferred for density

Backup:
  1 spare router
  1 spare access point
  Mobile hotspot (organizer's phone + SIM)

On-site tech lead:
  Assigned volunteer to monitor network, reboot equipment if needed
```

### Power & Electrical

```
REQUIREMENTS
─────────────

Power strips: 1 per table (1 per 4–5 participants)
Extension cords: 1 per 2 tables
Total outlets needed: ≥ 120 (laptops + phones + peripherals)

Backup:
  Surge protectors on all power strips
  Know location of circuit breakers
  Generator or UPS for critical systems (AV, router) if venue supports
```

### AV Equipment

```
REQUIREMENTS
─────────────

Presentation:
  1 projector or large display (min 1080p, visible from back of room)
  1 HDMI cable + adapters (USB-C to HDMI, Mini-DP to HDMI)
  1 spare HDMI cable

Audio:
  1 wireless lapel mic (for presenters)
  1 handheld mic (for Q&A)
  1 speaker system (adequate for room size)

Recording (optional but recommended):
  1 camera or phone on tripod for recording presentations
  Screen recording software for demo captures

TEST: All AV equipment tested the day before the event
BACKUP: Spare cables, spare batteries for wireless mics
```

### Venue Layout

```
┌────────────────────────────────────────────────────────────┐
│                        VENUE LAYOUT                         │
│                                                            │
│  ┌─── HACKING AREA ─────────────────────────────────────┐  │
│  │  Table Table Table Table Table Table                  │  │
│  │  (teams of 4-5, power strips, good Wi-Fi)            │  │
│  │  Table Table Table Table Table Table                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─── PRESENTATION AREA ────┐  ┌─── MENTORING AREA ────┐  │
│  │  Projector + screen      │  │  2-3 tables            │  │
│  │  Podium / standing area  │  │  Quiet, semi-private   │  │
│  │  Seating for audience    │  │  Whiteboards           │  │
│  └──────────────────────────┘  └────────────────────────┘  │
│                                                            │
│  ┌─── REGISTRATION DESK ────┐  ┌─── REFRESHMENTS ──────┐  │
│  │  Check-in + badge dist   │  │  Water, tea, coffee    │  │
│  │  Info materials          │  │  Meals (if provided)   │  │
│  └──────────────────────────┘  └────────────────────────┘  │
│                                                            │
│  ┌─── QUIET / REST AREA ────┐  ┌─── ORGANIZER OPS ─────┐  │
│  │  (for overnight events)  │  │  Router / network gear │  │
│  │  Low light, cushions     │  │  Printer (if needed)   │  │
│  └──────────────────────────┘  │  Spare equipment       │  │
│                                └────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

---

## 54.10 Event Security & Privacy

### Physical Security

```
✓ Venue access control (badge-only entry after check-in)
✓ Overnight security guard (if 24-hour event)
✓ Secure storage for personal belongings
✓ Emergency exits clearly marked
✓ First aid kit available
✓ Emergency contact numbers posted
```

### Digital Security

```
✓ Event Wi-Fi: WPA2 encrypted, unique password (not venue default)
✓ All event web properties: HTTPS / SSL (auto via Netlify / GitHub Pages)
✓ Registration data: restricted access (organizer leads only, 2FA)
✓ Submission data: managed by Devpost (SOC 2 compliant)
✓ Discord: workspace settings restrict guest access; admin roles limited
✓ Cloud accounts: separate from personal accounts; billing alerts enabled
✓ No default credentials on any event infrastructure
```

### Privacy

```
✓ Privacy policy published and accepted during registration
✓ Photo / video consent obtained during registration
✓ Registration PII: exported and stored in encrypted Google Drive
✓ Post-event: participant data retained only as long as needed
✓ No sharing of participant data with third parties without consent
✓ Opt-out option for public photo/video usage
```

### Incident Response

```
DIGITAL INCIDENT (e.g., data breach, platform outage):
  1. Identify and contain the issue
  2. Notify event lead + technical lead
  3. Communicate to participants (Discord #announcements)
  4. Remediate
  5. Document incident and response

PHYSICAL INCIDENT (e.g., medical emergency, safety concern):
  1. Call emergency services if needed (112)
  2. Notify event lead
  3. Administer first aid if trained
  4. Document incident
  5. Follow up with affected participant
```

---

## 54.11 Operations & Staffing

### Organizational Structure

```
EVENT LEAD (1)
  │  Overall coordination, final decisions, judge liaison
  │
  ├── TECHNICAL LEAD (1)
  │     ├── Network / AV volunteer (1-2)
  │     ├── Cloud / infrastructure support (1)
  │     └── Dataset / API support (1)
  │
  ├── OPERATIONS LEAD (1)
  │     ├── Registration / check-in volunteers (2-3)
  │     ├── Logistics coordinator (food, venue, supplies) (1)
  │     └── General volunteers (3-5)
  │
  ├── MENTORING COORDINATOR (1)
  │     └── Mentors (5-10, rotating shifts)
  │
  ├── JUDGE COORDINATOR (1)
  │     └── Judges (5-10)
  │
  └── COMMUNICATIONS LEAD (1)
        ├── Discord moderator (1-2)
        ├── Social media volunteer (1)
        └── Email / announcements (1)

TOTAL STAFF: 20-30 (including mentors and judges)
VOLUNTEER-TO-PARTICIPANT RATIO: aim 1:10 (operational volunteers)
```

### Shift Schedule (for 24-hour events)

```
SHIFT 1: 08:00 – 16:00 (full team)
  Check-in, opening, hacking kickoff, mentor hours, lunch

SHIFT 2: 16:00 – 00:00 (reduced team)
  Evening hacking, dinner, mentor hours, AV standby
  Minimum: 1 organizer + 1 tech volunteer + 1 general volunteer

SHIFT 3: 00:00 – 08:00 (skeleton crew, overnight events only)
  Overnight hacking, security, emergency only
  Minimum: 1 organizer + 1 security

SHIFT 4: 08:00 – 18:00 Day 2 (full team)
  Breakfast, final hacking, submissions, presentations, judging, closing
```

### Staff Briefing Checklist

```
Every staff member briefed on:
  ☐ Event schedule and their shift
  ☐ Their specific role and tasks
  ☐ Wi-Fi credentials and Discord access
  ☐ Emergency procedures and contacts
  ☐ Venue layout (rooms, exits, power, AV)
  ☐ Code of conduct enforcement
  ☐ Who to escalate issues to
  ☐ Where supplies are stored
```

---

## 54.12 Participant Support

### Help Channels

```
DURING EVENT
─────────────

  Discord #tech-help         Technical issues (environment, setup, APIs)
  Discord #dataset-questions Dataset and data format questions
  Discord #submission-help   Submission process questions
  On-site information desk   Venue, logistics, general questions
  Mentor office hours        Domain + technical guidance (scheduled slots)
```

### FAQ (published before and during event)

```
ESSENTIAL FAQ TOPICS
─────────────────────

  How do I form / join a team?
  What is the problem statement?
  What datasets / starter kit is provided?
  What tech stack can I use? Are there restrictions?
  How do I submit my project?
  What is the submission deadline? Can I submit late?
  What are the judging criteria?
  What prizes are available?
  How does the presentation work?
  Where is the Wi-Fi? What's the password?
  What food / drinks are provided?
  Where can I sleep / rest?
  Who do I contact for help?
  What happens to my code after the hackathon?
```

### Starter Kit Distribution

```
PROVIDED TO ALL TEAMS AT T-1 WEEK:
  ✓ Sample video files (10-20 camera feeds, pre-recorded Gujarat scenes)
  ✓ Sample metadata (camera registry entries for simulated cameras)
  ✓ Sample observation data (JSON examples matching canonical schema §14)
  ✓ API documentation (if platform provides API endpoints)
  ✓ Architecture reference (link to §0-§53 of this document)
  ✓ Docker Compose template (basic setup for FastAPI + PostgreSQL)
  ✓ Map data (Gujarat GeoJSON boundaries, sample camera locations)
  ✓ Judging rubric (so teams know what to optimize for)

DISTRIBUTION: GitHub repo (public) + Google Drive (large video files)
```

---

## 54.13 Legal & Compliance

### Terms & Conditions (Key Provisions)

```
HACKATHON TERMS — KEY PROVISIONS
─────────────────────────────────

ELIGIBILITY
  Open to [defined group: students / professionals / government employees]
  Minimum age: 18 (or parental consent if minors)
  Team size: 2-5 members

INTELLECTUAL PROPERTY
  Participants RETAIN full ownership of their submissions
  Organizers receive a non-exclusive license to display, publicize,
  and reference submissions for event promotion and government evaluation
  No transfer of IP to organizers or sponsors

LIABILITY
  Organizers provide venue and infrastructure "as-is"
  Organizers not liable for equipment damage, data loss, or personal injury
  (except where caused by organizer negligence)
  Participants responsible for backing up their own work

PRIVACY
  Participant data used only for event operations
  Photo / video may be used for event promotion (with consent)
  Data retained per privacy policy; deleted after purpose fulfilled

CODE OF CONDUCT
  Anti-harassment policy (mandatory)
  Respectful behavior required
  Violations result in disqualification and removal
  Reporting mechanism: event lead or designated safe person

PRIZES
  Prize eligibility requires complete submission by deadline
  Prize decisions by judges are final
  Tax implications (if any) are participant's responsibility
```

### Code of Conduct

```
All participants, mentors, judges, sponsors, and volunteers must:

  ✓ Treat everyone with respect and dignity
  ✓ Use welcoming and inclusive language
  ✓ Be collaborative and constructive
  ✓ Accept constructive feedback gracefully

  ✗ No harassment, discrimination, or intimidation of any kind
  ✗ No offensive comments related to gender, race, religion, disability,
    or any protected characteristic
  ✗ No unwelcome physical contact or sexual attention
  ✗ No disruption of presentations or event activities
  ✗ No unauthorized photography or recording of individuals

  Report violations to: [Event Lead name] or [Safe Person name]
  Reports are confidential and taken seriously
```

### Insurance & Venue

```
✓ Verify venue's liability insurance coverage
✓ Obtain event liability insurance if venue doesn't cover
✓ Ensure venue complies with fire safety regulations
✓ Ensure venue has accessible emergency exits
✓ Keep signed waivers (if used) stored securely
```

---

## 54.14 Accessibility & Inclusivity

### Accessibility Checklist

```
VENUE
  ☐ Wheelchair accessible entrance, exits, and pathways
  ☐ Accessible restrooms
  ☐ Elevator (if multi-floor)
  ☐ Clear signage (large print, high contrast)

REGISTRATION
  ☐ Registration form asks about accessibility needs
  ☐ Dietary restrictions / allergies collected
  ☐ Assistive technology needs noted

EVENT
  ☐ Reserved seating near power outlets for participants with mobility needs
  ☐ Microphone used for all announcements (hearing accessibility)
  ☐ Screen content readable from back of room (large font on slides)
  ☐ Quiet / low-stimulation rest area available
  ☐ Water and refreshments accessible (not only at high tables)
```

### Inclusivity Measures

```
✓ Outreach to underrepresented communities
  - Women-in-tech groups, university diversity clubs
  - Rural / tier-2 city tech communities
  - Students from non-CS backgrounds (police studies, law, public policy)

✓ Beginner-friendly track or mentoring
  - Pair first-time hackers with experienced mentors
  - Provide starter templates that work out-of-the-box
  - Office hours specifically for newcomers

✓ Inclusive language in all communications
  - Gender-neutral language
  - Avoid jargon in non-technical communications
  - Provide materials in English and Gujarati where feasible

✓ Diverse judging panel
  - Mix of technical and domain (police) judges
  - Gender and background diversity in judge panel
```

---

## 54.15 Event Metrics & KPIs

### Pre-Event Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Registrations | ≥ 150% of venue capacity | Eventbrite dashboard |
| Team formation rate | ≥ 80% of participants in a team | Registration data |
| Starter kit download rate | ≥ 90% of teams | GitHub / Drive analytics |
| Mentor confirmations | ≥ 5 mentors confirmed | Manual tracking |
| Judge confirmations | ≥ 5 judges confirmed | Manual tracking |

### During-Event Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Registration-to-attendance conversion | ~65% for free events | Check-in count vs. registrations |
| Discord active users | ≥ 80% of attendees | Discord server insights |
| #tech-help response time | < 15 minutes | Manual monitoring |
| Network uptime | 100% | On-site monitoring |
| AV issues | 0 during presentations | Incident log |
| Mentor sessions conducted | ≥ 2 per team | Mentor coordinator tracking |

### Post-Event Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Project submission rate | ≥ 80% of teams submit | Devpost count vs. team count |
| Submission completeness | ≥ 90% have demo video + code + description | Devpost review |
| Judge score completion | 100% of judges submit all scores | Devpost dashboard |
| Inter-judge score variance | < 3 points (on 10-point scale) | Score analysis |
| Participant satisfaction | ≥ 4.0 / 5.0 average | Post-event survey |
| "Would recommend to others" | ≥ 80% yes | Post-event survey |
| Net Promoter Score | ≥ 50 | Post-event survey |
| Cost per participant | Within budget | Financial reconciliation |

### Post-Event Survey (send T+1 day)

```
SURVEY QUESTIONS (Google Forms, 5 min)
──────────────────────────────────────

1. Overall satisfaction (1-5 stars)
2. Problem statement clarity (1-5)
3. Technical infrastructure quality (Wi-Fi, power, AV) (1-5)
4. Mentor quality and availability (1-5)
5. Judging fairness (1-5)
6. Communication quality (1-5)
7. Venue and logistics (1-5)
8. What worked well? (open text)
9. What should be improved? (open text)
10. Would you participate again? (Yes / Maybe / No)
11. Would you recommend this to a colleague? (1-10 NPS scale)
```

---

## 54.16 The Demo Script (5–7 minutes)

```
SCENARIO: "A robbery occurred at SG Highway, Ahmedabad at 19:30."

ACT 1 — OPERATOR (30 sec)
  Show operator console
  → cameras visible on map
  → alert arrives: "Watchlist vehicle detected near SG Highway"
  → operator acknowledges → creates incident

ACT 2 — INVESTIGATOR (3–4 min)
  Open investigator workspace
  → bound to Case CASE-2026-AHM-SAT-0421

  Search: Location = SG Highway, Time = 19:00–20:00
  → system returns: 23 vehicles, 17 persons, 4 trajectories

  Select Vehicle GJ01AB1234
  → show 5-camera trajectory on timeline:
     C101 → C113 → C127 → C144 → C171

  → show feasibility scores:
     "All transitions plausible: 21–47 km/h on city/highway roads"

  → show associated persons: P-17 (conf: 0.82), P-22 (conf: 0.71)

  → show investigation graph:
     Vehicle ↔ Persons ↔ Cameras ↔ Incident

  → click "Generate Evidence Package"
  → show evidence package with:
     Timeline, clips, provenance, integrity hashes, Section 65B metadata

ACT 3 — COMMAND (30 sec)
  Show command dashboard
  → state map with incident marker
  → camera health: 95.3% online
  → district-wise stats
  → NOTE: command officer sees operational summary,
    NOT unrestricted investigation data

ACT 4 — ARCHITECTURE (1–2 min)
  Show four diagrams:
  1. System context (50K cameras → Platform → Police)
  2. Data flow (Camera → Edge → AI → Observation → Correlation → Graph → Evidence)
  3. Investigation flow (Query → Candidates → Correlation → Timeline → Evidence)
  4. Deployment (Camera → Edge → Hub → State DC → DR)

  Key messages:
  • "Runs 20 cameras today, 50,000 tomorrow — no redesign"
  • "Edge processing — 200× bandwidth reduction"
  • "Graph intelligence — not just detection"
  • "Evidence with provenance — designed for legal process"
  • "Integrates existing cameras — does not replace them"
  • "Federated architecture — embraces Gujarat's heterogeneous CCTV ecosystem"
```

---

## 54.17 Event Timeline / Roadmap

```
T-12 WEEKS: PLANNING
────────────────────
  ☐ Finalize event scope (date, venue, format, capacity)
  ☐ Recruit core organizing team (event lead, tech lead, ops lead)
  ☐ Secure venue (confirm power, network, AV, accessibility)
  ☐ Begin judge and mentor recruitment
  ☐ Apply for cloud credits (AWS Activate, GCP)
  ☐ Draft Terms & Conditions, Code of Conduct

T-8 WEEKS: SETUP
─────────────────
  ☐ Launch event website (GitHub Pages / Netlify)
  ☐ Set up Eventbrite registration page
  ☐ Create Discord server with channel structure
  ☐ Set up Devpost hackathon page
  ☐ Publish Terms, Code of Conduct, FAQ
  ☐ Begin marketing and outreach
  ☐ Confirm judges and mentors

T-4 WEEKS: REGISTRATION OPEN
──────────────────────────────
  ☐ Open registration
  ☐ Announce via email, social media, university networks, police networks
  ☐ Share Discord invite with early registrants
  ☐ Prepare starter kit (sample videos, datasets, templates)
  ☐ Prepare judging rubric and share with judges
  ☐ Procure supplies (power strips, cables, badges, signage)

T-2 WEEKS: PREPARATION
────────────────────────
  ☐ Send logistics email to all registrants
  ☐ Finalize schedule and share
  ☐ Test AV equipment at venue
  ☐ Test network at venue (bandwidth, capacity)
  ☐ Release starter kit (GitHub repo + Google Drive)
  ☐ Conduct judges' orientation (rubric walkthrough, bias training)
  ☐ Recruit and brief volunteers

T-2 DAYS: FINAL PREP
──────────────────────
  ☐ Close registration
  ☐ Send final reminder email (venue map, Wi-Fi, schedule)
  ☐ Set up venue (tables, power, signage, AV)
  ☐ Test everything end-to-end (registration check-in, network, AV, Discord)
  ☐ Print badges, judging sheets (backup), emergency contact cards

T-0: EVENT DAY(S)
───────────────────
  ☐ Execute event per schedule (§54.1)
  ☐ Monitor all channels (Discord, on-site, network)
  ☐ Track metrics in real-time (attendance, submissions, issues)
  ☐ Live social media updates

T+1 DAY: FOLLOW-UP
────────────────────
  ☐ Send thank-you email with survey link
  ☐ Announce winners publicly (Devpost, social media)
  ☐ Export all data (registration, submissions, scores, photos)
  ☐ Back up everything to organizer Google Drive

T+1 WEEK: REVIEW
──────────────────
  ☐ Compile survey results
  ☐ Analyze metrics vs. targets (§54.15)
  ☐ Conduct team retrospective (what worked, what didn't)
  ☐ Document lessons learned

T+1 MONTH: FOLLOW-THROUGH
───────────────────────────
  ☐ Publish event report (metrics, outcomes, winning projects)
  ☐ Share winning solutions with Gujarat Police stakeholders
  ☐ Evaluate winning projects for potential pilot development
  ☐ Plan next event based on lessons learned
```

---

## 54.18 Tool Comparison Matrix

| Component | Tool | Pros | Cons | Cost | Recommendation |
|-----------|------|------|------|------|---------------|
| **Registration** | **Eventbrite** | Tiered tickets, reminders, check-in app, widely used | Fees on paid tickets (2-3%) | Free for free events | ✓ **Primary** |
| | Google Forms | Free, customizable, spreadsheet export | No payment, no reminders, manual follow-up | Free | Fallback |
| | HackerEarth | Purpose-built for hackathons, integrated | Paid for some features, proprietary | Varies | Alternative |
| **Submissions** | **Devpost** | All-in-one (submit + judge + gallery), free | Participants need account | Free (public events) | ✓ **Primary** |
| | HackHQ | Structured judging, no participant accounts | Less known, limited free tier | Free tier available | Alternative |
| | GitHub + Form | Free, familiar to devs | No judging workflow, manual | Free | Fallback |
| **Communication** | **Discord** | Free unlimited chat + voice, persistent history | Less formal, fewer enterprise tools | Free | ✓ **Primary** |
| | Slack | Robust threads, search, integrations | Free tier: 90-day history, paid expensive | Free / ₹600+/user/mo | Alternative |
| | Mailchimp | Email campaigns, analytics | Limited free tier (500 contacts) | Free / ₹1,200+/mo | Supplement for email |
| **Hosting** | **GitHub Pages / Netlify** | Free, auto-SSL, deploy from Git | Static only | Free | ✓ For event website |
| | AWS / GCP / Azure | Scalable, free tiers, cloud credits | Complex, risk of unexpected charges | Free tier / credits | For participant infra |
| | DigitalOcean | Simple pricing (~$5/mo), good performance | No free tier (but GitHub Pack discount) | $5-20/mo | Alternative |

---

## 54.19 Cost & Budget

### Budget Template

| Category | Item | Est. Cost (₹) | Funding Source |
|----------|------|---------------|----------------|
| **Venue** | Venue rental (if not free government venue) | 0 – 50,000 | Government / sponsor |
| | Power + cleaning | 5,000 – 15,000 | Venue |
| **Food & Beverage** | Tea/coffee + snacks (2 days) | 15,000 – 30,000 | Sponsor |
| | Lunch × 2 + Dinner × 1 | 30,000 – 60,000 | Sponsor |
| **Technology** | Extra Wi-Fi routers / APs | 5,000 – 15,000 | Purchase / rent |
| | Power strips + cables | 3,000 – 8,000 | Purchase |
| | Cloud credits for participants | 0 (free credits) | AWS / GCP / Azure |
| **Printing** | Badges, signage, rubric sheets | 3,000 – 8,000 | — |
| **Prizes** | Cash / gadgets / certificates | 25,000 – 200,000 | Sponsor / government |
| **Marketing** | Social media ads (optional) | 0 – 10,000 | — |
| **Contingency** | 15% buffer | 10,000 – 50,000 | — |
| **TOTAL** | | **~96,000 – 4,36,000** | |

> [!NOTE]
> Government venue and government sponsorship can bring total cost to under ₹1,00,000 if venue is free and food is sponsored.

### Cost Management

```
✓ Use free-tier platforms wherever possible (Eventbrite, Devpost, Discord, GitHub Pages)
✓ Apply for cloud credits early (AWS Activate, GCP, Azure)
✓ Enable billing alerts on any cloud accounts (threshold: 50% of credit)
✓ Track all expenses in a shared spreadsheet (real-time)
✓ Assign one person as budget owner
✓ Keep receipts for all purchases (government audit trail)
```

---

## 54.20 Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Low attendance** (<50% show-up) | Medium | High | Over-register at 150% capacity; send reminders; confirm attendance T-2 days |
| **Wi-Fi failure** | Medium | Critical | Dedicated network (not shared); backup router; mobile hotspot fallback |
| **Power outage** | Low | Critical | Know circuit breakers; surge protectors; UPS for router/AV; venue backup generator |
| **Submission platform down** | Low | High | Backup: email submissions + Google Form; extend deadline if platform issue |
| **Key judge no-show** | Medium | Medium | Recruit 2 backup judges; brief all judges on schedule early |
| **Code of Conduct violation** | Low | High | Clear policy published; trained safe person on-site; swift, documented response |
| **Data breach (PII)** | Low | High | HTTPS everywhere; 2FA on admin; minimal data collection; encryption at rest |
| **Cloud credit exhaustion** | Low | Medium | Billing alerts at 50%; guide teams on cost-efficient usage; free-tier defaults |
| **AV failure during presentations** | Medium | Medium | Test day-before; spare cables/adapters; backup laptop for screen share |
| **Participant team conflict** | Low | Low | Mentor intervention; team-change process defined; Code of Conduct |
| **Venue accessibility issue** | Low | Medium | Audit venue pre-event; ask about needs in registration; have contingency plan |
| **Food allergy incident** | Low | High | Collect dietary needs at registration; label all food; first aid kit on-site |
| **Overcrowding** | Medium | Medium | Cap registration; venue capacity check; manage check-in flow |

---

> [!NOTE]
> **This document is the master architecture and execution reference.** Sections §0–§53 define the CCTV platform architecture. Section §54 defines the hackathon event execution plan. All subsequent design documents, RFPs, technical specifications, and implementation guides should reference and align with this document.

---

*End of document.*
