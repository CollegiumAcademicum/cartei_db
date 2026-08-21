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


class DamageSize(str, Enum):
    LT1 = "LT1"   # < 1 cm
    MID = "MID"   # 1–5 cm
    GT = "GT"     # > 5 cm


class RoomDamageLine(str, Enum):
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


class WGDamageLine(str, Enum):
    BAD_FLECK = "BAD_FLECK"
    BAD_LOCH = "BAD_LOCH"
    BAD_KLEBER = "BAD_KLEBER"
    BAD_SONSTIGES = "BAD_SONSTIGES"
    KUECHE_FLECK = "KUECHE_FLECK"
    KUECHE_LOCH = "KUECHE_LOCH"
    KUECHE_KLEBER = "KUECHE_KLEBER"
    KUECHE_SONSTIGES = "KUECHE_SONSTIGES"
    GEMEINSCHAFT_FLECK = "GEMEINSCHAFT_FLECK"
    GEMEINSCHAFT_LOCH = "GEMEINSCHAFT_LOCH"
    GEMEINSCHAFT_KLEBER = "GEMEINSCHAFT_KLEBER"
    GEMEINSCHAFT_SONSTIGES = "GEMEINSCHAFT_SONSTIGES"
