import enum


class UserRole(enum.StrEnum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class DomainStatus(enum.StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ScanStatus(enum.StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AssetType(enum.StrEnum):
    A = "A"
    AAAA = "AAAA"
    NS = "NS"
    MX = "MX"


class EventType(enum.StrEnum):
    DOMAIN_CREATED = "DOMAIN_CREATED"
    DOMAIN_DELETED = "DOMAIN_DELETED"
