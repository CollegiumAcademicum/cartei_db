from enum import Enum


class AGStatus(Enum):
    ZU_AKTIV = "ZU_AKTIV"
    AKTIV = "AKTIV"
    NICHT_AUSREICHEND = "NICHT_AUSREICHEND"
    IM_GESPRAECH = "IM_GESPRAECH"
    INAKTIV = "INAKTIV"


class ChangeSource(Enum):
    HUMAN = "HUMAN"
    SERVICE = "SERVICE"


class EnrollmentType(Enum):
    STUDY = "STUDY"
    APPRENTICESHIP = "APPRENTICESHIP"


class NoteSourceGroup(str, Enum):
    mietverwaltung = "mietverwaltung"
    clustersprechende = "clustersprechende"


class NoteSubjectType(str, Enum):
    tenant = "tenant"
    cluster = "cluster"
    wg = "wg"
