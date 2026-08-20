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


class UebergabeProtokollType(str, Enum):
    EINZUG = "EINZUG"
    AUSZUG = "AUSZUG"


class PartitionPosition(str, Enum):
    SQM_7 = "SQM_7"
    SQM_14 = "SQM_14"


class FurnitureSource(str, Enum):
    GEFRAEST = "GEFRAEST"
    MOEBELSPENDE = "MOEBELSPENDE"
    NICHT_VORHANDEN = "NICHT_VORHANDEN"


class MattressSource(str, Enum):
    CA = "CA"
    NICHT_VORHANDEN = "NICHT_VORHANDEN"


class DamageLine(str, Enum):
    BODEN_FLECKEN = "BODEN_FLECKEN"
    BODEN_LOECHER = "BODEN_LOECHER"
    FUSSLEISTE_FLECKEN = "FUSSLEISTE_FLECKEN"
    WAND_FLECKEN = "WAND_FLECKEN"
    WAND_LOECHER = "WAND_LOECHER"
    WAND_KLEBER = "WAND_KLEBER"
    TUER_FLECKEN = "TUER_FLECKEN"
    TUER_LOECHER = "TUER_LOECHER"
    FENSTER_RAHMEN_FLECKEN = "FENSTER_RAHMEN_FLECKEN"
    FENSTER_BANK_FLECKEN = "FENSTER_BANK_FLECKEN"
    FENSTER_KLEBER = "FENSTER_KLEBER"
    BETT_FLECKEN = "BETT_FLECKEN"
    BETT_LOECHER = "BETT_LOECHER"
    MATRATZE_FLECKEN = "MATRATZE_FLECKEN"
    SCHREIBTISCH_FLECKEN = "SCHREIBTISCH_FLECKEN"
    SCHREIBTISCH_LOECHER = "SCHREIBTISCH_LOECHER"
    SCHRANK_FLECKEN = "SCHRANK_FLECKEN"
    SCHRANK_LOECHER = "SCHRANK_LOECHER"
