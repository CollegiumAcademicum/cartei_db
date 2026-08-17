from enum import Enum


class AGStatus(Enum):
    ZU_AKTIV = "ZU_AKTIV"
    AKTIV = "AKTIV"
    NICHT_AUSREICHEND = "NICHT_AUSREICHEND"
    IM_GESPRAECH = "IM_GESPRAECH"
    INAKTIV = "INAKTIV"


class AGHealth(Enum):
    GESUND = "GESUND"
    KERNAUFGABEN = "KERNAUFGABEN"
    KRITISCH = "KRITISCH"
    TOT = "TOT"


class ChangeSource(Enum):
    HUMAN = "HUMAN"
    SERVICE = "SERVICE"


class EnrollmentType(Enum):
    STUDY = "STUDY"
    APPRENTICESHIP = "APPRENTICESHIP"
    SCHUELER = "SCHUELER"
    FSJ = "FSJ"


class NoteSourceGroup(str, Enum):
    mietverwaltung = "mietverwaltung"
    clustersprechende = "clustersprechende"


class NoteSubjectType(str, Enum):
    tenant = "tenant"
    cluster = "cluster"
    wg = "wg"


class DocumentType(str, Enum):
    datenschutz = "datenschutz"
    photoerlaubnis = "photoerlaubnis"
    vertraulichkeitserklaerung = "vertraulichkeitserklaerung"
