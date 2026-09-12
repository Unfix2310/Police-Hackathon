import enum

# ── v4.1 §24: Five-Way Camera Gap Semantics ──────────────────────────────────
# "No observation" MUST NOT be confused with evidence of absence.
class ObservationStatus(str, enum.Enum):
    OBSERVED_PRESENT = 'OBSERVED_PRESENT'
    # Camera active, entity detected in FOV → positive evidence of presence

    OBSERVED_ABSENT = 'OBSERVED_ABSENT'
    # Camera active, clear FOV, entity NOT detected → positive evidence of absence

    NOT_OBSERVED = 'NOT_OBSERVED'
    # No camera coverage in this area → entity MAY have passed; cannot confirm or deny

    CAMERA_OFFLINE = 'CAMERA_OFFLINE'
    # System fault, no video feed → log as system event, cannot infer anything

    UNKNOWN = 'UNKNOWN'
    # Degraded quality / occlusion → flag for human review


# ── v4.1 §10: Generic Relationship Lifecycle States ───────────────────────────
class GenericLifecycleState(str, enum.Enum):
    NO_ASSOCIATION = 'NO_ASSOCIATION'
    CANDIDATE = 'CANDIDATE'
    PROBABLE = 'PROBABLE'
    ACTIVE = 'ACTIVE'
    ENDED = 'ENDED'
    RE_EVALUATED = 'RE_EVALUATED'


# ── v4.1 §10: Person–Vehicle Domain States ────────────────────────────────────
class PersonVehicleDomainState(str, enum.Enum):
    UNKNOWN = 'UNKNOWN'
    POSSIBLE_PROXIMITY = 'POSSIBLE_PROXIMITY'
    POSSIBLE_ENTRY = 'POSSIBLE_ENTRY'
    ENTERED = 'ENTERED'
    RIDING_IN = 'RIDING_IN'
    POSSIBLE_EXIT = 'POSSIBLE_EXIT'
    EXITED = 'EXITED'
    ENDED = 'ENDED'


# ── v4.1 §21: Interaction Classes ─────────────────────────────────────────────
class InteractionClass(str, enum.Enum):
    PERSON_VEHICLE = 'PERSON_VEHICLE'
    PERSON_PERSON = 'PERSON_PERSON'
    VEHICLE_VEHICLE = 'VEHICLE_VEHICLE'
    ENTITY_LOCATION = 'ENTITY_LOCATION'
    ENTITY_EVENT = 'ENTITY_EVENT'


# ── v4.1 §21: Event Types per Interaction Class ───────────────────────────────
class EventType(str, enum.Enum):
    # Person ↔ Vehicle
    ENTERED = 'ENTERED'
    EXITED = 'EXITED'
    RIDING_IN = 'RIDING_IN'
    APPROACHED = 'APPROACHED'
    LEFT_VEHICLE = 'LEFT_VEHICLE'
    REJOINED = 'REJOINED'
    # Person ↔ Person
    CO_LOCATED = 'CO_LOCATED'
    FOLLOWED = 'FOLLOWED'
    TRAVELLED_WITH = 'TRAVELLED_WITH'
    SEPARATED = 'SEPARATED'
    # Vehicle ↔ Vehicle
    CONVOYED = 'CONVOYED'
    CONVERGED = 'CONVERGED'
    DIVERGED = 'DIVERGED'
    STOPPED_NEAR = 'STOPPED_NEAR'
    # Entity ↔ Location
    ENTERED_AREA = 'ENTERED_AREA'
    EXITED_AREA = 'EXITED_AREA'
    STOPPED_AT = 'STOPPED_AT'
    PASSED_THROUGH = 'PASSED_THROUGH'
    # Entity ↔ Event
    PARTICIPATED_IN = 'PARTICIPATED_IN'
    ASSOCIATED_WITH = 'ASSOCIATED_WITH'


# ── v4.1 §25: Hypothesis Types ────────────────────────────────────────────────
class HypothesisType(str, enum.Enum):
    PERSON_VEHICLE_ASSOCIATION = 'PERSON_VEHICLE_ASSOCIATION'
    VEHICLE_SWITCH = 'VEHICLE_SWITCH'
    TRAJECTORY_LINK = 'TRAJECTORY_LINK'
    GROUP_MEMBERSHIP = 'GROUP_MEMBERSHIP'
    CONVOY = 'CONVOY'
    WATCHLIST_ASSOCIATION = 'WATCHLIST_ASSOCIATION'


# ── v4.1 §25: Confidence Bands ────────────────────────────────────────────────
class ConfidenceBand(str, enum.Enum):
    VERY_HIGH = 'VERY_HIGH'   # 0.95 – 1.00: Auto-surface to investigator
    HIGH = 'HIGH'             # 0.80 – 0.94: Surface with supporting detail
    MEDIUM = 'MEDIUM'         # 0.60 – 0.79: Present as candidate, recommend verification
    LOW = 'LOW'               # 0.00 – 0.59: Present only if explicitly requested

    @classmethod
    def from_score(cls, score: float) -> "ConfidenceBand":
        if score >= 0.95:
            return cls.VERY_HIGH
        elif score >= 0.80:
            return cls.HIGH
        elif score >= 0.60:
            return cls.MEDIUM
        else:
            return cls.LOW


# ── v4.1 §25: Hypothesis Status ───────────────────────────────────────────────
class HypothesisStatus(str, enum.Enum):
    GENERATED = 'GENERATED'
    PENDING_REVIEW = 'PENDING_REVIEW'
    ACCEPTED = 'ACCEPTED'
    REJECTED = 'REJECTED'
    SUPERSEDED = 'SUPERSEDED'


class ObservationType(str, enum.Enum):
    PERSON = 'PERSON'
    VEHICLE = 'VEHICLE'
    OBJECT = 'OBJECT'
    EVENT = 'EVENT'

class EntityStatus(str, enum.Enum):
    CANDIDATE = 'CANDIDATE'
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    DETECTED = 'DETECTED'
    OBSERVED = 'OBSERVED'
    ASSOCIATED = 'ASSOCIATED'
    PROBABLE_MATCH = 'PROBABLE_MATCH'
    CONFIRMED = 'CONFIRMED'

class CameraStatus(str, enum.Enum):
    ONLINE = 'ONLINE'
    OFFLINE = 'OFFLINE'
    DEGRADED = 'DEGRADED'
    MAINTENANCE = 'MAINTENANCE'

class IncidentSeverity(str, enum.Enum):
    P1 = 'P1'
    P2 = 'P2'
    P3 = 'P3'
    P4 = 'P4'
    P1_CRITICAL = 'P1_CRITICAL'
    P2_HIGH = 'P2_HIGH'
    P3_MEDIUM = 'P3_MEDIUM'
    P4_LOW = 'P4_LOW'

class CaseStatus(str, enum.Enum):
    OPEN = 'OPEN'
    UNDER_INVESTIGATION = 'UNDER_INVESTIGATION'
    CHARGE_SHEET = 'CHARGE_SHEET'
    CLOSED = 'CLOSED'

class AlertType(str, enum.Enum):
    WATCHLIST_MATCH = 'WATCHLIST_MATCH'
    ZONE_INTRUSION = 'ZONE_INTRUSION'
    ANOMALY = 'ANOMALY'
    CAMERA_HEALTH = 'CAMERA_HEALTH'
    SYSTEM = 'SYSTEM'

class AlertPriority(str, enum.Enum):
    P1 = 'P1'
    P2 = 'P2'
    P3 = 'P3'
    P4 = 'P4'

class FeasibilityLabel(str, enum.Enum):
    PLAUSIBLE = 'PLAUSIBLE'
    POSSIBLE = 'POSSIBLE'
    LOW_PLAUSIBILITY = 'LOW_PLAUSIBILITY'
    IMPLAUSIBLE = 'IMPLAUSIBLE'
    PHYSICALLY_IMPOSSIBLE = 'PHYSICALLY_IMPOSSIBLE'

class UserRoleEnum(str, enum.Enum):
    OPERATOR = 'OPERATOR'
    INVESTIGATOR = 'INVESTIGATOR'
    COMMAND = 'COMMAND'
    FIELD_OFFICER = 'FIELD_OFFICER'
    ADMIN = 'ADMIN'
    SECURITY_ADMIN = 'SECURITY_ADMIN'
    AUDITOR = 'AUDITOR'

class VehicleClass(str, enum.Enum):
    SEDAN = 'SEDAN'
    SUV = 'SUV'
    HATCHBACK = 'HATCHBACK'
    TWO_WHEELER = 'TWO_WHEELER'
    AUTO_RICKSHAW = 'AUTO_RICKSHAW'
    BUS = 'BUS'
    TRUCK = 'TRUCK'
    TRACTOR = 'TRACTOR'
    BULLOCK_CART = 'BULLOCK_CART'
    OTHER = 'OTHER'
    UNKNOWN = 'UNKNOWN'

class CameraType(str, enum.Enum):
    FIXED = 'FIXED'
    PTZ = 'PTZ'
    DOME = 'DOME'
    BULLET = 'BULLET'
    OTHER = 'OTHER'

class CapabilityQuality(str, enum.Enum):
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'
    NONE = 'NONE'

class LocationType(str, enum.Enum):
    HIGHWAY = 'HIGHWAY'
    INTERSECTION = 'INTERSECTION'
    STREET = 'STREET'
    PUBLIC_SQUARE = 'PUBLIC_SQUARE'
    TOLL_PLAZA = 'TOLL_PLAZA'
    OTHER = 'OTHER'
