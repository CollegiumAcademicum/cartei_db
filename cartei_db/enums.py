from enum import Enum


class AGStatus(Enum):
    ACTIVE = "ACTIVE"
    NOT_ACTIVE_ENOUGH = "NOT_ACTIVE_ENOUGH"
    CONTACTED = "CONTACTED"
    INACTIVE = "INACTIVE"


class ChangeSource(Enum):
    HUMAN = "HUMAN"
    SERVICE = "SERVICE"


class EnrollmentType(Enum):
    STUDY = "STUDY"
    APPRENTICESHIP = "APPRENTICESHIP"
