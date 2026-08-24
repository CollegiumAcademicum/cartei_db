from cartei_db.enums import AGStatus, ChangeSource, EnrollmentType, DamageSize, RoomDamageLine, WGDamageLine


def test_ag_status_values():
    assert AGStatus.ZU_AKTIV.value == "ZU_AKTIV"
    assert AGStatus.AKTIV.value == "AKTIV"
    assert AGStatus.NICHT_AUSREICHEND.value == "NICHT_AUSREICHEND"
    assert AGStatus.IM_GESPRAECH.value == "IM_GESPRAECH"
    assert AGStatus.INAKTIV.value == "INAKTIV"


def test_change_source_values():
    assert ChangeSource.HUMAN.value == "HUMAN"
    assert ChangeSource.SERVICE.value == "SERVICE"


def test_enrollment_type_values():
    assert EnrollmentType.STUDY.value == "STUDY"
    assert EnrollmentType.APPRENTICESHIP.value == "APPRENTICESHIP"


def test_damage_size_values():
    assert [s.value for s in DamageSize] == ["LT1", "MID", "GT"]


def test_room_damage_line_has_furniture_and_surfaces():
    vals = {l.value for l in RoomDamageLine}
    assert {"BODEN_FLECKEN", "WAND_KLEBER", "BETT_LOECHER", "SCHRANK_FLECKEN", "SONSTIGES"} <= vals
    assert len(vals) == 19


def test_wg_damage_line_is_area_by_defect():
    vals = {l.value for l in WGDamageLine}
    assert {"BAD_FLECK", "KUECHE_LOCH", "GEMEINSCHAFT_KLEBER", "GEMEINSCHAFT_SONSTIGES"} <= vals
    assert len(vals) == 12
