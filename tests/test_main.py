from types import SimpleNamespace

import pendulum

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


def test_setup_garmin_login_uses_tokenstore(mocker, tmp_path):
    mocker.patch.object(main, "config_path", str(tmp_path))
    garmin_mock = mocker.Mock()
    garmin_class = mocker.patch.object(main, "Garmin", return_value=garmin_mock)
    main.garmin(email="user@example.com", password="secret", store=False)
    args, kwargs = garmin_class.call_args
    assert args == ("user@example.com", "secret")
    assert callable(kwargs["prompt_mfa"])
    garmin_mock.login.assert_called_once_with(f"{tmp_path}/garmintoken")


def test_setup_garmin_prompt_mfa_reads_input(mocker, tmp_path):
    mocker.patch.object(main, "config_path", str(tmp_path))
    mocker.patch.object(main, "Garmin")
    input_mock = mocker.patch("builtins.input", return_value="123456")
    main.garmin(email="user@example.com", password="secret", store=False)
    _, kwargs = main.Garmin.call_args
    assert kwargs["prompt_mfa"]() == "123456"
    input_mock.assert_called_once()


def test_setup_garmin_store_writes_garmin_yml(mocker, tmp_path):
    mocker.patch.object(main, "config_path", str(tmp_path))
    mocker.patch.object(main, "Garmin")
    main.garmin(email="user@example.com", password="secret", store=True)
    config_file = tmp_path / "garmin.yml"
    assert config_file.is_file()
    assert "user@example.com" in config_file.read_text()


def _make_sync_env(mocker, activities):
    mocker.patch.object(main, "config_exists", return_value=True)
    mocker.patch.object(main, "config", {"sqlite": {"use": False}}, create=True)
    db_mock = mocker.Mock()
    db_mock.cursor().execute().fetchone.return_value = None
    mocker.patch.object(main, "db", db_mock, create=True)
    garmin_mock = mocker.Mock()
    garmin_mock.get_activities_by_date.return_value = activities
    mocker.patch.object(main, "Garmin", return_value=garmin_mock)
    last_workout = SimpleNamespace(
        workout_date=pendulum.now().add(days=-1).format("YYYY-MM-DD HH:mm:ss")
    )
    fittrackee_mock = mocker.Mock()
    fittrackee_mock.is_workout_present.return_value = True
    fittrackee_mock.get_last_workout.return_value = last_workout
    mocker.patch.object(main, "Fittrackee", return_value=fittrackee_mock)
    mocker.patch.object(
        main.Sports, "get_fittrackee_sport_by_garmin_id", return_value=13
    )
    mocker.patch.object(
        main, "_fetch_garmin_activity_file", return_value="/tmp/fake_activity.zip"
    )
    return garmin_mock, fittrackee_mock


def _make_activity():
    return {
        "activityId": 20297051253,
        "activityName": "Indoor ride",
        "startTimeLocal": "2025-09-06 12:13:50",
        "distance": 2629.0,
        "duration": 611.63,
        "activityType": {"typeId": 13},
    }


def test_sync_falls_back_to_no_gpx_when_upload_fails(mocker):
    _, fittrackee_mock = _make_sync_env(mocker, [_make_activity()])
    fittrackee_mock.upload_workout.return_value = None
    workout_mock = SimpleNamespace(id="w1")
    fittrackee_mock.add_workout_no_gpx.return_value = workout_mock
    main.sync()
    fittrackee_mock.add_workout_no_gpx.assert_called_once_with(
        sport_id=13,
        workout_date="2025-09-06 12:13",
        distance=2.629,
        duration=611.63,
        title="Indoor ride",
    )


def test_sync_does_not_fall_back_when_upload_succeeds(mocker):
    _, fittrackee_mock = _make_sync_env(mocker, [_make_activity()])
    fittrackee_mock.upload_workout.return_value = SimpleNamespace(id="w1")
    main.sync()
    fittrackee_mock.add_workout_no_gpx.assert_not_called()
