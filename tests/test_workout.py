import pytest

from garmin_to_fittrackee.workout import Workout


@pytest.fixture
def workout():
    return Workout(
        ascent=29.4,
        ave_speed=15.39,
        bounds=[
            47.197706094011664,
            -1.5946481097489595,
            47.20924596302211,
            -1.5719065815210342,
        ],
        creation_date="Sun, 14 Jan 2024 21:37:06 GMT",
        descent=26.2,
        distance=5.306,
        duration="0:33:57",
        id="Ab6jry6Gbntn4Z33tEttgj",
        map="14d3bec291bffc9bfb70f03e90c6ca12",
        max_alt=20.4,
        max_speed=20.57,
        min_alt=10.4,
        moving="0:20:41",
        notes="",
        pauses="0:13:15",
        records=[],
        segments=[
            {
                "ascent": 29.4,
                "ave_speed": 15.39,
                "descent": 26.2,
                "distance": 5.306,
                "duration": "0:33:57",
                "max_alt": 20.4,
                "max_speed": 20.57,
                "min_alt": 10.4,
                "moving": "0:20:41",
                "pauses": "0:13:15",
                "segment_id": 0,
                "workout_id": "Ab6jry6Gbntn4Z33tEttgj",
            }
        ],
        sport_id=1,
        title="Nantes Cyclisme sur route",
        user="Dryusdan",
        weather_end=None,
        weather_start=None,
        with_gpx=True,
        workout_date="Sun, 14 Jan 2024 13:09:59 GMT",
    )


def test_workout_id(workout):
    assert (workout.id) == "Ab6jry6Gbntn4Z33tEttgj"


def test_workout_ave_speed(workout):
    assert (workout.ave_speed) == 15.39


def test_not_present_in_fittrackee(workout):
    assert (workout.present_in_fittrackee) is False


def test_present_in_fittrackee(workout):
    workout.set_present_in_fittrackee()
    assert (workout.present_in_fittrackee) is True


def test_present_in_garmin(workout):
    workout.set_present_in_garmin()
    assert (workout.present_in_garmin) is True
