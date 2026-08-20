from cartei_db.enums import (
    DamageLine, FurnitureSource, MattressSource, PartitionPosition, UebergabeProtokollType,
)


def test_enums_have_expected_members():
    assert {e.value for e in UebergabeProtokollType} == {"EINZUG", "AUSZUG"}
    assert {e.value for e in PartitionPosition} == {"SQM_7", "SQM_14"}
    assert {e.value for e in FurnitureSource} == {"GEFRAEST", "MOEBELSPENDE", "NICHT_VORHANDEN"}
    assert {e.value for e in MattressSource} == {"CA", "NICHT_VORHANDEN"}
    assert len(DamageLine) == 18
    assert DamageLine.FENSTER_RAHMEN_FLECKEN.value == "FENSTER_RAHMEN_FLECKEN"
