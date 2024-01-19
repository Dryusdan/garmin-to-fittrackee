import pytest

from garmin_to_fittrackee.sports import Sports


def test_get_fittrackee_sport_by_garmin_id_2():
    sport = Sports.get_fittrackee_sport_by_garmin_id(2)
    assert sport == 1


def test_get_fittrackee_sport_by_garmin_id_175():
    sport = Sports.get_fittrackee_sport_by_garmin_id(175)
    assert sport == 7


def test_get_fittrackee_sport_by_garmin_id_143():
    sport = Sports.get_fittrackee_sport_by_garmin_id(143)
    assert sport == 4


def test_get_fittrackee_sport_by_garmin_id_152():
    sport = Sports.get_fittrackee_sport_by_garmin_id(152)
    assert sport == 13


def test_get_fittrackee_sport_by_garmin_id_8():
    sport = Sports.get_fittrackee_sport_by_garmin_id(8)
    assert sport == 5


def test_get_fittrackee_sport_by_garmin_id_9():
    sport = Sports.get_fittrackee_sport_by_garmin_id(9)
    assert sport == 6


def test_get_fittrackee_sport_by_garmin_id_167():
    sport = Sports.get_fittrackee_sport_by_garmin_id(167)
    assert sport == 12


def test_get_fittrackee_sport_by_garmin_id_204():
    sport = Sports.get_fittrackee_sport_by_garmin_id(204)
    assert sport == 10


def test_get_fittrackee_sport_by_garmin_id_37():
    sport = Sports.get_fittrackee_sport_by_garmin_id(37)
    assert sport == 14


def test_get_fittrackee_sport_by_garmin_id_28():
    sport = Sports.get_fittrackee_sport_by_garmin_id(28)
    assert sport == 16


def test_get_fittrackee_sport_by_garmin_id_6():
    sport = Sports.get_fittrackee_sport_by_garmin_id(6)
    assert sport == 8


def test_get_fittrackee_sport_by_garmin_id_237():
    sport = Sports.get_fittrackee_sport_by_garmin_id(237)
    assert sport == 11


def test_get_fittrackee_sport_by_garmin_id_3():
    sport = Sports.get_fittrackee_sport_by_garmin_id(3)
    assert sport == 3


def test_get_fittrackee_sport_by_garmin_id_252():
    sport = Sports.get_fittrackee_sport_by_garmin_id(252)
    assert sport == 9


def test_get_fittrackee_sport_by_garmin_id_wrong_id():
    sport = Sports.get_fittrackee_sport_by_garmin_id(358)
    assert sport == 1


def test_get_fittrackee_sport_by_garmin_id_wrong():
    with pytest.raises(ValueError, match=r"garmin_sport_id Hello is not an int"):
        Sports.get_fittrackee_sport_by_garmin_id("Hello")
