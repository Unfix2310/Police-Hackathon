import enum

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
