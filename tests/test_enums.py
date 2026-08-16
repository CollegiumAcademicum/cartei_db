from cartei_db.enums import AGStatus, ChangeSource, EnrollmentType


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
