from types import SimpleNamespace

from garmin_to_fittrackee import main


def test_main_callback_verbose_enables_debug(mocker):
    set_log_level = mocker.patch.object(main, "set_log_level")
    main.main_callback(verbose=True)
    set_log_level.assert_called_once_with("DEBUG")


def test_main_callback_not_verbose_keeps_level(mocker):
    set_log_level = mocker.patch.object(main, "set_log_level")
    main.main_callback(verbose=False)
    set_log_level.assert_not_called()


def _make_fittrackee(mocker, workouts):
    mocker.patch.object(main, "config_exists", return_value=True)
    fittrackee_mock = mocker.Mock()
    fittrackee_mock.get_all_workouts.return_value = workouts
    mocker.patch.object(main, "Fittrackee", return_value=fittrackee_mock)
    return fittrackee_mock


def test_refresh_all(mocker):
    workouts = [
        SimpleNamespace(id="w1", workout_date="2024-01-14 13:09:59"),
        SimpleNamespace(id="w2", workout_date="2024-02-20 08:00:00"),
    ]
    fittrackee_mock = _make_fittrackee(mocker, workouts)
    main.refresh()
    assert fittrackee_mock.refresh_workout.call_count == 2


def test_refresh_workout_id(mocker):
    workouts = [
        SimpleNamespace(id="w1", workout_date="2024-01-14 13:09:59"),
        SimpleNamespace(id="w2", workout_date="2024-02-20 08:00:00"),
    ]
    fittrackee_mock = _make_fittrackee(mocker, workouts)
    main.refresh(workout_id="w2")
    fittrackee_mock.refresh_workout.assert_called_once_with("w2")


def test_refresh_from_date(mocker):
    workouts = [
        SimpleNamespace(id="w1", workout_date="2024-01-14 13:09:59"),
        SimpleNamespace(id="w2", workout_date="2024-02-20 08:00:00"),
    ]
    fittrackee_mock = _make_fittrackee(mocker, workouts)
    main.refresh(from_date="2024-02-01")
    assert fittrackee_mock.refresh_workout.call_args_list[0].args == ("w2",)
    assert fittrackee_mock.refresh_workout.call_count == 1


def test_refresh_limit(mocker):
    workouts = [
        SimpleNamespace(id="w1", workout_date="2024-01-14 13:09:59"),
        SimpleNamespace(id="w2", workout_date="2024-02-20 08:00:00"),
        SimpleNamespace(id="w3", workout_date="2024-03-01 10:00:00"),
    ]
    fittrackee_mock = _make_fittrackee(mocker, workouts)
    main.refresh(limit=2)
    assert fittrackee_mock.refresh_workout.call_count == 2


def test_refresh_no_workouts(mocker):
    fittrackee_mock = _make_fittrackee(mocker, [])
    main.refresh()
    fittrackee_mock.refresh_workout.assert_not_called()


def test_refresh_config_missing(mocker):
    mocker.patch.object(main, "config_exists", return_value=False)
    fittrackee_mock = mocker.patch.object(main, "Fittrackee")
    main.refresh()
    fittrackee_mock.assert_not_called()
