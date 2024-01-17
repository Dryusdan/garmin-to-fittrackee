import pytest

from garmin_to_fittrackee.sports import Sports


def test_get_fittrackee_sport_by_garmin_id():
    sport = Sports.get_fittrackee_sport_by_garmin_id(2)
    assert sport == 1
    sport = Sports.get_fittrackee_sport_by_garmin_id(175)
    assert sport == 7


def test_get_fittrackee_sport_by_garmin_id_wrong_id():
    sport = Sports.get_fittrackee_sport_by_garmin_id(358)
    assert sport == 1


def test_get_fittrackee_sport_by_garmin_id_wrong():
    with pytest.raises(ValueError, match=r"garmin_sport_id Hello is not an int"):
        Sports.get_fittrackee_sport_by_garmin_id("Hello")
