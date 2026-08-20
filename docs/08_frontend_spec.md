# 08: Frontend Component Specification

This document details the frontend architecture, component hierarchy, state management, and design system for the Gujarat CCTV Intelligence Platform (Hackathon MVP). 

## 1. Application Architecture

The frontend is built as a Single Page Application (SPA) focusing on rapid development, responsive design, and real-time updates.

*   **Framework:** React 18
*   **Routing:** React Router v6
*   **State Management:** React Context + `useReducer` (no Redux for MVP to reduce boilerplate). Contexts will be divided by domain (AuthContext, AlertContext, MapContext).
*   **Styling:** Tailwind CSS (utility-first styling for rapid UI development)
*   **Maps:** React-Leaflet with OpenStreetMap tiles (free, no API key required for MVP)
*   **Charts:** Recharts (simple, React-native charting library)
*   **Icons:** Lucide React
*   **HTTP Client:** Axios with interceptors (for JWT injection, automatic token refresh, and global error handling)
*   **WebSocket:** Native WebSocket API (`WebSocket` object) for real-time alerts from the Redis pub/sub backend via FastAPI.

## 2. Route Structure

The application uses role-based routing. Unauthorized access to specific routes redirects to the dashboard or login page.

*   **Public Routes:**
    *   `/` → Login
*   **Operator Routes:**
    *   `/operator` → Operator Console (Default view)
    *   `/operator/cameras` → Camera Grid
    *   `/operator/alerts` → Alert Management
*   **Investigator Routes:**
    *   `/investigator` → Investigator Workspace (Default view)
    *   `/investigator/search` → Entity/Plate Search
    *   `/investigator/case/:caseId` → Case View
    *   `/investigator/trajectory/:entityType/:entityId` → Trajectory View (Spatio-temporal mapping)
    *   `/investigator/evidence/:evidenceId` → Evidence Package View
*   **Command Routes:**
    *   `/command` → Command Dashboard (Statewide view)
    *   `/command/district/:districtId` → District Drill-down
*   **Admin Routes:**
    *   `/admin` → Admin Dashboard
    *   `/admin/cameras` → Camera Management
    *   `/admin/users` → User Management

## 3. Component Tree & 4. Component Details

### 3.1. Layout Components

**`AppShell`**
*   **Behavior:** Main application wrapper. Handles the overall page layout, integrating the sidebar, header, and main content area.
*   **Props:** `children: React.ReactNode`
*   **Children:** `Sidebar`, `Header`, `MainContent`

**`Sidebar`**
*   **Behavior:** Left-side navigation menu. Renders links dynamically based on the current user's role (extracted from AuthContext).
*   **Props:** `role: 'operator' | 'investigator' | 'command' | 'admin'`

**`Header`**
*   **Behavior:** Top navigation bar containing user profile summary, role badge, and notification bell for unread alerts.
*   **Props:** `userName: string`, `role: string`, `unreadAlertCount: number`

### 3.2. Operator Components

**`CameraGrid`**
*   **Behavior:** Displays a responsive grid of camera feeds. Allows the operator to configure layout (e.g., 2x2, 3x3, 4x4).
*   **Props:** `layout: '2x2' | '3x3' | '4x4'`, `cameras: Camera[]`
*   **API:** `GET /api/v1/cameras`
*   **Children:** `CameraCard`

**`CameraCard`**
*   **Behavior:** Displays a single simulated camera feed (or static image for MVP), camera name, location, and a status indicator.
*   **Props:** `camera: Camera`, `onClick: (cameraId: string) => void`
*   **Children:** `StatusIndicator`

**`AlertPanel`**
*   **Behavior:** A side panel or dedicated view listing active, unacknowledged alerts in real-time.
*   **Props:** `alerts: Alert[]`, `onAcknowledge: (alertId: string) => void`
*   **API:** WebSocket connection to `/api/v1/ws/alerts`, `POST /api/v1/alerts/{id}/acknowledge`
*   **Children:** `AlertItem`

**`AlertItem`**
*   **Behavior:** Represents a single alert (e.g., Watchlist hit, Crowd anomaly). Includes timestamp, camera details, and an acknowledge action.
*   **Props:** `alert: Alert`, `onAcknowledge: () => void`

**`CameraHealthSummary`**
*   **Behavior:** A compact widget showing the count of cameras by status (Online, Offline, Degraded).
*   **Props:** `onlineCount: number`, `offlineCount: number`, `degradedCount: number`
*   **API:** `GET /api/v1/cameras/health-summary`

### 3.3. Investigator Components

**`SearchPanel`**
*   **Behavior:** Complex search form for finding entities (vehicles via plate, persons via attributes). Includes time range and geospatial area selectors.
*   **Props:** `onSearch: (params: SearchParams) => void`
*   **Children:** `DateTimeRangePicker`

**`SearchResults`**
*   **Behavior:** Renders the list of results returned from the search, paginated.
*   **Props:** `results: Entity[]`, `isLoading: boolean`
*   **API:** `GET /api/v1/search/observations`
*   **Children:** `EntityCard`

**`EntityCard`**
*   **Behavior:** Summary card for a vehicle or person observation. Shows cropped image, confidence score, and timestamp.
*   **Props:** `entity: Entity`, `onClick: () => void`
*   **Children:** `ConfidenceBadge`

**`TrajectoryTimeline`**
*   **Behavior:** A vertical timeline displaying a sequence of observations for a specific entity, annotated with spatio-temporal feasibility scores.
*   **Props:** `observations: Observation[]`
*   **Children:** `ObservationDetail`, `FeasibilityBadge`

**`TrajectoryMap`**
*   **Behavior:** A Leaflet map instances visualizing the path of an entity across multiple cameras over time. Draws lines between camera markers and arrows indicating direction.
*   **Props:** `observations: Observation[]`
*   **API:** `GET /api/v1/investigation/trajectory/{entityId}`
*   **Children:** `Map`, `CameraMarker`

**`InvestigationGraph`**
*   **Behavior:** A force-directed graph (using a library like `react-force-graph` or D3) showing relationships between cases, entities, and incidents.
*   **Props:** `graphData: GraphData` (nodes and links)
*   **API:** `GET /api/v1/investigation/graph/{caseId}`

**`EvidenceViewer`**
*   **Behavior:** Displays a compiled evidence package, including a chronological list of clips, Section 65B hash/metadata, and download options.
*   **Props:** `evidencePackageId: string`
*   **API:** `GET /api/v1/evidence/{id}`
*   **Children:** `VideoPlayer`, `ObservationDetail`

**`VideoPlayer`**
*   **Behavior:** A standard HTML5 video player wrapper with a timestamp overlay.
*   **Props:** `url: string`, `timestamp: string`, `watermarkText: string`

**`ObservationDetail`**
*   **Behavior:** Detailed view of a single observation, showing the full frame, cropped entity, attributes extracted (color, make), confidence, and system provenance.
*   **Props:** `observation: Observation`

**`CasePanel`**
*   **Behavior:** A sidebar within the investigator workspace showing details of the active case, linked entities, and quick actions.
*   **Props:** `caseDetails: Case`

### 3.4. Command Components

**`StateOverview`**
*   **Behavior:** Top-level metrics bar showing total cameras, active incidents, total alerts today, and observations logged.
*   **Props:** `metrics: StateMetrics`
*   **API:** `GET /api/v1/command/metrics`

**`StateMap`**
*   **Behavior:** A large map of Gujarat with choropleth coloring by district health (camera uptime) and markers for high-severity incidents. Includes a heat map toggle.
*   **Props:** `districtData: DistrictData[]`, `incidents: Incident[]`
*   **Children:** `Map`

**`DistrictHealthTable`**
*   **Behavior:** A sortable table listing all districts and their respective camera uptime percentages and active alerts.
*   **Props:** `districts: DistrictHealth[]`
*   **Children:** `DataTable`

**`TrendCharts`**
*   **Behavior:** Line or bar charts showing 7-day historical trends for incidents, alerts, or camera uptime.
*   **Props:** `trendData: TrendData[]`
*   **API:** `GET /api/v1/command/trends`

**`CriticalAlerts`**
*   **Behavior:** A highlighted widget showing only the most critical, unhandled alerts requiring command attention.
*   **Props:** `alerts: Alert[]`
*   **Children:** `AlertItem`

### 3.5. Shared Components

*   **`Map`:** Base React-Leaflet wrapper handling initialization and tile layers.
    *   `Props`: `center: [number, number]`, `zoom: number`, `children: ReactNode`
*   **`CameraMarker`:** Custom Leaflet marker showing a camera icon, colored by status.
    *   `Props`: `camera: Camera`, `position: [number, number]`, `status: 'online' | 'offline' | 'degraded'`
*   **`ConfidenceBadge`:** Small pill showing percentage. Green (>80%), Yellow (50-80%), Red (<50%).
    *   `Props`: `score: number`
*   **`FeasibilityBadge`:** Small pill indicating spatio-temporal engine results.
    *   `Props`: `status: 'plausible' | 'possible' | 'implausible'`
*   **`StatusIndicator`:** A simple colored dot.
    *   `Props`: `status: 'online' | 'offline' | 'degraded'`
*   **`DataTable`:** Generic table component supporting sorting and basic filtering.
    *   `Props`: `columns: ColumnDef[]`, `data: any[]`
*   **`LoadingSpinner`:** Full-screen or container-level loading animation.
*   **`EmptyState`:** Standard UI for empty lists or missing data.
    *   `Props`: `message: string`, `icon?: ReactNode`, `action?: ReactNode`
*   **`ErrorBoundary`:** React Error Boundary to catch UI crashes and show a fallback.
*   **`DateTimeRangePicker`:** Input for selecting a start and end datetime.
    *   `Props`: `value: [Date, Date]`, `onChange: (val: [Date, Date]) => void`
*   **`Modal`:** Generic modal overlay.
    *   `Props`: `isOpen: boolean`, `onClose: () => void`, `title: string`, `children: ReactNode`

## 5. Color Scheme and Design Tokens

The MVP uses Tailwind CSS configured with specific theme colors to match the Gujarat Police branding and status indicators.

**Tailwind `tailwind.config.js` extension:**
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1E3A5F', // Police Blue
          light: '#2A4D7C',
          dark: '#12253F'
        },
        accent: {
          DEFAULT: '#FF6B35', // Gujarat Saffron
          light: '#FF8A5E',
          dark: '#E05520'
        },
        status: {
          success: '#22C55E', // Online / Plausible
          warning: '#F59E0B', // Degraded / Possible
          error: '#EF4444',   // Offline / Implausible
        },
        background: {
          DEFAULT: '#F8FAFC',
          card: '#FFFFFF',
        },
        text: {
          main: '#1E293B',
          muted: '#64748B'
        }
      }
    }
  }
}
```

## 6. Responsive Breakpoints & Mobile Considerations

*   **Mobile (`< 640px` / Tailwind `sm`):** Stacked layouts. Sidebar becomes a hamburger menu drawer. Maps and camera grids take full width. Operator camera grids default to 1x1 or 1x2.
*   **Tablet (`640px - 1024px` / Tailwind `md` / `lg`):** Sidebar can be collapsed to icons only. Camera grid defaults to 2x2. Search panels move to the top rather than side.
*   **Desktop (`> 1024px` / Tailwind `xl` / `2xl`):** Full sidebar. Complex investigator workspaces split into multiple panes (e.g., Map on left, Timeline on right). Camera grid supports 3x3 and 4x4.

## 7. Authentication Flow

1.  **Login (`/`):** User submits credentials via the login form.
2.  **API Call:** `POST /api/v1/auth/login`.
3.  **Response:** Server returns a JWT (JSON Web Token) and user metadata (ID, Role, Jurisdiction).
4.  **Storage:** JWT is stored securely (SessionStorage or HttpOnly cookie if backend supports it; for hackathon MVP, LocalStorage is acceptable).
5.  **Context Update:** `AuthContext` is updated with user details and `isAuthenticated = true`.
6.  **Redirection:** Router intercepts the state change and redirects the user to their default dashboard based on their role (`/operator`, `/investigator`, `/command`, or `/admin`).
7.  **Subsequent Requests:** Axios interceptor automatically attaches `Authorization: Bearer <token>` to all outgoing API requests.
8.  **Logout:** Token is cleared, state is reset, user is redirected to `/`.

## 8. WebSocket Integration (Real-time Alerts)

The platform requires real-time push notifications for alerts (e.g., Watchlist hits) to avoid heavy API polling.

1.  **Connection:** Upon successful login and initialization of the `AppShell`, a WebSocket connection is established to `ws://<backend-url>/api/v1/ws/alerts?token=<jwt>`.
2.  **Heartbeat:** Frontend sends a ping every 30s to keep the connection alive.
3.  **Message Handling:**
    *   Messages received via WebSocket are parsed as JSON.
    *   The `AlertContext` reducer processes the message.
    *   If a new alert arrives, it is appended to the global alert state, triggering an update in the `Header` (bell icon counter) and `AlertPanel` components.
    *   Optional: Trigger a browser notification or soft audio chime.
4.  **Reconnection:** If the connection drops, a backoff retry mechanism attempts to reconnect automatically.
