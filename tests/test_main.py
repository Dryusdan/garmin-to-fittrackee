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
