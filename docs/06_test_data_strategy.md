# Test Data Strategy

This document defines the strategy for generating, managing, and injecting test data for the Gujarat CCTV Intelligence Platform Hackathon MVP. It ensures that developers and participants have realistic, consistent data that correctly exercises the platform's correlation and intelligence features.

## 1. Simulated Camera Definitions

The platform requires a realistic topology of cameras to demonstrate spatio-temporal correlation. The following 50 simulated cameras are distributed across Ahmedabad.

| ID | Name | Lat | Lng | Dir (°) | Type | Police Station | District | Capabilities |
|----|------|-----|-----|---------|------|----------------|----------|--------------|
| CAM-GJ-AHM-SG-0101 | SG Highway / ISRO | 23.0258 | 72.5074 | 350 | highway | Satellite | Ahmedabad | ANPR, PTZ, Night Vision |
| CAM-GJ-AHM-SG-0102 | SG Highway / ISRO South | 23.0245 | 72.5072 | 170 | highway | Satellite | Ahmedabad | ANPR, Night Vision |
| CAM-GJ-AHM-SG-0113 | SG Highway / Drive-In Jn | 23.0495 | 72.5175 | 345 | intersection | Vastrapur | Ahmedabad | ANPR, PTZ |
| CAM-GJ-AHM-SG-0114 | SG Highway / Drive-In South | 23.0482 | 72.5170 | 165 | intersection | Vastrapur | Ahmedabad | Detection Only |
| CAM-GJ-AHM-SG-0127 | SG Highway / Thaltej | 23.0531 | 72.5186 | 350 | intersection | Sola | Ahmedabad | ANPR, Night Vision |
| CAM-GJ-AHM-SG-0128 | SG Highway / Thaltej Cross | 23.0531 | 72.5186 | 90 | intersection | Sola | Ahmedabad | Detection Only |
| CAM-GJ-AHM-SG-0130 | SG Highway / Pakwan | 23.0381 | 72.5123 | 355 | highway | Vastrapur | Ahmedabad | ANPR |
| CAM-GJ-AHM-SG-0131 | SG Highway / Pakwan Flyover | 23.0380 | 72.5123 | 175 | highway | Vastrapur | Ahmedabad | ANPR |
| CAM-GJ-AHM-SG-0144 | SG Highway / Sola Bhagwat | 23.0805 | 72.5284 | 340 | highway | Sola | Ahmedabad | ANPR, Night Vision |
| CAM-GJ-AHM-SG-0145 | SG Highway / Sola Bridge | 23.0800 | 72.5282 | 160 | highway | Sola | Ahmedabad | ANPR |
| CAM-GJ-AHM-SP-0171 | SP Ring Road / Motera | 23.1118 | 72.5975 | 90 | highway | Chandkheda | Ahmedabad | ANPR, Night Vision |
| CAM-GJ-AHM-SP-0172 | SP Ring Road / Tapovan | 23.1189 | 72.5802 | 270 | highway | Chandkheda | Ahmedabad | ANPR |
| CAM-GJ-AHM-SP-0173 | SP Ring Road / Bopal | 23.0234 | 72.4645 | 180 | highway | Bopal | Ahmedabad | ANPR, PTZ |
| CAM-GJ-AHM-SP-0174 | SP Ring Road / Sanand Cir | 22.9912 | 72.4721 | 180 | intersection | Sarkhej | Ahmedabad | ANPR, Night Vision |
| CAM-GJ-AHM-SP-0175 | SP Ring Road / Kamod | 22.9543 | 72.5312 | 90 | highway | Aslali | Ahmedabad | ANPR |
| CAM-GJ-AHM-CG-0201 | CG Road / Swastik | 23.0345 | 72.5567 | 10 | market | Navrangpura | Ahmedabad | PTZ, Detection |
| CAM-GJ-AHM-CG-0202 | CG Road / Girish Cold | 23.0312 | 72.5552 | 190 | market | Navrangpura | Ahmedabad | ANPR |
| CAM-GJ-AHM-CG-0203 | CG Road / Panchvati | 23.0254 | 72.5523 | 20 | intersection | Ellis Bridge | Ahmedabad | ANPR, PTZ |
| CAM-GJ-AHM-CG-0204 | CG Road / Parimal | 23.0211 | 72.5501 | 200 | intersection | Ellis Bridge | Ahmedabad | Detection Only |
| CAM-GJ-AHM-AR-0301 | Ashram Road / Income Tax | 23.0456 | 72.5689 | 180 | intersection | Navrangpura | Ahmedabad | ANPR, Night Vision |
| CAM-GJ-AHM-AR-0302 | Ashram Road / Bata | 23.0412 | 72.5678 | 0 | highway | Navrangpura | Ahmedabad | ANPR |
| CAM-GJ-AHM-AR-0303 | Ashram Road / Vallabh Sadan | 23.0345 | 72.5667 | 180 | intersection | Ellis Bridge | Ahmedabad | PTZ, Detection |
| CAM-GJ-AHM-AR-0304 | Ashram Road / VS Hospital | 23.0214 | 72.5712 | 0 | building_entry | Ellis Bridge | Ahmedabad | ANPR |
| CAM-GJ-AHM-LG-0401 | Law Garden / NCC | 23.0278 | 72.5589 | 90 | market | Ellis Bridge | Ahmedabad | Detection Only |
| CAM-GJ-AHM-LG-0402 | Law Garden / Happy Street | 23.0289 | 72.5595 | 270 | market | Ellis Bridge | Ahmedabad | PTZ |
| CAM-GJ-AHM-IM-0501 | IIM Road / Panjrapole | 23.0305 | 72.5412 | 270 | intersection | Vastrapur | Ahmedabad | ANPR, Night Vision |
| CAM-GJ-AHM-IM-0502 | IIM Road / IIM Gate | 23.0321 | 72.5356 | 90 | building_entry | Vastrapur | Ahmedabad | ANPR |
| CAM-GJ-AHM-IM-0503 | IIM Road / AMA | 23.0315 | 72.5388 | 270 | building_entry | Vastrapur | Ahmedabad | Detection Only |
| CAM-GJ-AHM-RR-0601 | Relief Road / Laldarwaja | 23.0256 | 72.5812 | 90 | intersection | Karanj | Ahmedabad | ANPR, PTZ |
| CAM-GJ-AHM-RR-0602 | Relief Road / Electricity House | 23.0267 | 72.5834 | 270 | building_entry | Karanj | Ahmedabad | Detection Only |
| CAM-GJ-AHM-RR-0603 | Relief Road / Zaveriwad | 23.0278 | 72.5865 | 90 | market | Kalupur | Ahmedabad | PTZ |
| CAM-GJ-AHM-MC-0701 | Manek Chowk / Entry | 23.0234 | 72.5891 | 180 | market | Khadia | Ahmedabad | Detection Only |
| CAM-GJ-AHM-MC-0702 | Manek Chowk / Food Market | 23.0230 | 72.5895 | 0 | market | Khadia | Ahmedabad | PTZ |
| CAM-GJ-AHM-MC-0703 | Manek Chowk / Bullion | 23.0225 | 72.5890 | 90 | market | Khadia | Ahmedabad | Detection Only |
| CAM-GJ-AHM-KS-0801 | Kalupur / Station Entry | 23.0298 | 72.5987 | 270 | building_entry | Kalupur | Ahmedabad | ANPR, PTZ |
| CAM-GJ-AHM-KS-0802 | Kalupur / Station Exit | 23.0301 | 72.5985 | 90 | building_entry | Kalupur | Ahmedabad | ANPR |
| CAM-GJ-AHM-KS-0803 | Kalupur / Sindhi Market | 23.0285 | 72.5956 | 180 | market | Kalupur | Ahmedabad | PTZ |
| CAM-GJ-AHM-SG-0150 | SG Highway / Makarba | 23.0045 | 72.4987 | 350 | highway | Sarkhej | Ahmedabad | ANPR |
| CAM-GJ-AHM-SG-0151 | SG Highway / Prahladnagar | 23.0112 | 72.5023 | 170 | intersection | Anandnagar | Ahmedabad | ANPR, Night Vision |
| CAM-GJ-AHM-SG-0152 | SG Highway / YMCA | 23.0089 | 72.5011 | 350 | highway | Anandnagar | Ahmedabad | ANPR |
| CAM-GJ-AHM-132-0901 | 132ft Ring / Shivranjani | 23.0245 | 72.5256 | 0 | intersection | Satellite | Ahmedabad | ANPR, PTZ |
| CAM-GJ-AHM-132-0902 | 132ft Ring / Nehrunagar | 23.0189 | 72.5345 | 0 | intersection | Ellis Bridge | Ahmedabad | ANPR |
| CAM-GJ-AHM-132-0903 | 132ft Ring / AEC | 23.0567 | 72.5456 | 180 | intersection | Naranpura | Ahmedabad | ANPR |
| CAM-GJ-AHM-132-0904 | 132ft Ring / Helmet Cir | 23.0456 | 72.5389 | 90 | intersection | Vastrapur | Ahmedabad | ANPR, Night Vision |
| CAM-GJ-AHM-132-0905 | 132ft Ring / Akhbar Nagar | 23.0678 | 72.5567 | 180 | intersection | Vadaj | Ahmedabad | ANPR |
| CAM-GJ-AHM-132-0906 | 132ft Ring / Vadaj Cir | 23.0612 | 72.5678 | 90 | intersection | Vadaj | Ahmedabad | ANPR, PTZ |
| CAM-GJ-AHM-RTO-1001 | RTO Circle / North | 23.0745 | 72.5789 | 180 | intersection | Sabarmati | Ahmedabad | ANPR |
| CAM-GJ-AHM-RTO-1002 | RTO Circle / South | 23.0740 | 72.5789 | 0 | intersection | Sabarmati | Ahmedabad | ANPR |
| CAM-GJ-AHM-RTO-1003 | RTO / Subhash Bridge | 23.0712 | 72.5834 | 90 | highway | Sabarmati | Ahmedabad | ANPR, Night Vision |
| CAM-GJ-AHM-RTO-1004 | RTO / Collector Office | 23.0756 | 72.5812 | 270 | building_entry | Sabarmati | Ahmedabad | Detection Only |

## 2. Pre-computed Distance Matrix

The spatio-temporal feasibility engine relies on realistic road network distances. To enable the demo without requiring a full OSM routing engine deployment during the hackathon, the following pre-computed distance matrix must be populated in the database.

**Demo Sequence (SG Highway Trajectory):**
- **C101** (`CAM-GJ-AHM-SG-0101`) to **C113** (`CAM-GJ-AHM-SG-0113`): 3.2 km
- **C113** (`CAM-GJ-AHM-SG-0113`) to **C127** (`CAM-GJ-AHM-SG-0127`): 2.8 km
- **C127** (`CAM-GJ-AHM-SG-0127`) to **C144** (`CAM-GJ-AHM-SG-0144`): 4.1 km
- **C144** (`CAM-GJ-AHM-SG-0144`) to **C171** (`CAM-GJ-AHM-SP-0171`): 8.7 km

A full NxN matrix for the 50 cameras will be generated as a CSV (using Haversine distances scaled by a ~1.3 tortuosity factor to simulate road networks) and loaded into PostgreSQL/Redis.

## 3. Test Scenarios

These 5 scenarios form the core of the hackathon evaluation and demo script. The synthetic data generator will inject these exact scenarios into the background noise.

### Scenario 1: Vehicle trajectory on SG Highway (Demo Scenario)
- **Subject**: Vehicle `GJ01AB1234` (White Sedan)
- **Story**: A suspect vehicle travels linearly up SG Highway.
- **Expected Observations**:
  1. `CAM-GJ-AHM-SG-0101` at 19:14:02 (Conf: 0.96)
  2. `CAM-GJ-AHM-SG-0113` at 19:21:17 (Conf: 0.98)
  3. `CAM-GJ-AHM-SG-0127` at 19:29:44 (Conf: 0.94)
  4. `CAM-GJ-AHM-SG-0144` at 19:37:08 (Conf: 0.97)
  5. `CAM-GJ-AHM-SP-0171` at 19:48:31 (Conf: 0.93)
- **Expected Output**: Trajectory graph linking the 5 cameras; all transitions scored as "PLAUSIBLE".

### Scenario 2: City transit & park
- **Subject**: Vehicle `GJ05YY5678` (Red Hatchback)
- **Story**: Enters from SG Highway, drives into the city via IIM Road, parks at Law Garden.
- **Expected Observations**: `CAM-GJ-AHM-SG-0130` → `CAM-GJ-AHM-IM-0501` → `CAM-GJ-AHM-CG-0203` → `CAM-GJ-AHM-LG-0402`.
- **Expected Output**: Successful entity resolution across highway and market cameras.

### Scenario 3: Co-travel detection
- **Subject**: `GJ27CC9999` (Black SUV) and `GJ01DD1111` (Silver Sedan)
- **Story**: Two vehicles traveling in convoy across 4 intersections, always appearing within 10 seconds of each other.
- **Expected Output**: Graph correlation showing `[:ASSOCIATED_WITH {type: "co-travel"}]` between the two vehicle entities.

### Scenario 4: Person ReID
- **Subject**: Person `P-9988` (Red shirt, backpack)
- **Story**: Observed walking near RTO circle, later observed entering Kalupur station.
- **Expected Observations**: `CAM-GJ-AHM-RTO-1001` (10:15) → `CAM-GJ-AHM-KS-0801` (11:30).
- **Expected Output**: ReID feature matching links the two observations to a single candidate person entity.

### Scenario 5: Watchlist alert
- **Subject**: Vehicle `GJ01XX0000` (Stolen Motorcycle)
- **Story**: Appears on `CAM-GJ-AHM-132-0901`. Plate matches watchlist entry exactly.
- **Expected Output**: Real-time pub/sub alert generated, incident automatically created.

## 4. Synthetic Observation Generator

A Python script (`generate_test_data.py`) will be provided in the Starter Kit to populate the database with realistic observations.

**Specifications:**
- **Time Range**: 24-hour period (e.g., 2026-08-19 00:00:00 to 23:59:59).
- **Volume**: ~50–200 observations per camera per hour, resulting in ~150,000 baseline observations.
- **Noise Characteristics**:
  - 70% vehicles, 30% persons.
  - Realistic plates (e.g., `GJ01...`, `GJ05...`).
  - 10% of plates are partial reads (e.g., `GJ01AB12_4`).
  - Confidence scores normally distributed between 0.70 and 0.99.
- **Injection**: The script will deterministically overlay the 5 Test Scenarios on top of the random noise.

## 5. Video Recording Requirements

For the hackathon, we need 50 short video clips (one for each simulated camera) to represent "live" or recent footage when participants build the UI.

- **Resolution**: 1080p (or at least 720p).
- **Duration**: ~30 seconds to 1 minute per clip, set to loop.
- **Content**: Representative public traffic/CCTV footage matching the camera's `location_type` (highway, intersection, market).
- **Sources**: Open-source traffic datasets, royalty-free stock footage, or synthetically generated video.
- **Storage**: Hosted on an S3-compatible public bucket (e.g., AWS S3 or Google Cloud Storage) and linked in the starter kit.
- **Format**: `cam_id.mp4` (e.g., `CAM-GJ-AHM-SG-0101.mp4`).

## 6. Seed Data SQL

The Starter Kit will include a `V1__Seed_Data.sql` script containing:
1. `INSERT` statements for the 50 cameras (populating the `cameras` table).
2. `INSERT` statements for the pre-computed distance matrix.
3. `INSERT` statements for a basic watchlist (including `GJ01XX0000`).

*(Full SQL omitted here for brevity, to be generated by the `generate_test_data.py` script.)*

## 7. Gujarat GeoJSON

To render the map UI correctly, the Starter Kit will include:
- `ahmedabad_wards.geojson`: Boundaries for the police station jurisdictions.
- `gujarat_districts.geojson`: State-wide boundaries for the command dashboard view.

These files must be loaded into the frontend (React/Leaflet) or served via the backend GIS endpoints.
