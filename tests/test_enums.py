from cartei_db.enums import AGStatus, ChangeSource, EnrollmentType


def test_ag_status_values():
    assert AGStatus.ACTIVE.value == "ACTIVE"
    assert AGStatus.NOT_ACTIVE_ENOUGH.value == "NOT_ACTIVE_ENOUGH"
    assert AGStatus.CONTACTED.value == "CONTACTED"
    assert AGStatus.INACTIVE.value == "INACTIVE"


def test_change_source_values():
    assert ChangeSource.HUMAN.value == "HUMAN"
    assert ChangeSource.SERVICE.value == "SERVICE"


def test_enrollment_type_values():
    assert EnrollmentType.STUDY.value == "STUDY"
    assert EnrollmentType.APPRENTICESHIP.value == "APPRENTICESHIP"
