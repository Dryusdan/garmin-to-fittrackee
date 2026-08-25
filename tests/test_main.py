from pathlib import Path
from types import SimpleNamespace

import pendulum
import pytest
import typer

from garmin_to_fittrackee import main
from garmin_to_fittrackee.fittrackee import WorkoutNotFoundError


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
    fittrackee_mock.get_all_workouts.assert_not_called()
    fittrackee_mock.refresh_workout.assert_called_once_with("w2")


def test_refresh_workout_id_not_found(mocker):
    fittrackee_mock = _make_fittrackee(mocker, [])
    fittrackee_mock.refresh_workout.side_effect = WorkoutNotFoundError("w2")
    with pytest.raises(typer.Exit) as excinfo:
        main.refresh(workout_id="w2")
    assert excinfo.value.exit_code == 1
    fittrackee_mock.get_all_workouts.assert_not_called()


def test_refresh_skips_missing_workout(mocker):
    workouts = [
        SimpleNamespace(id="w1", workout_date="2024-01-14 13:09:59"),
        SimpleNamespace(id="w2", workout_date="2024-02-20 08:00:00"),
    ]
    fittrackee_mock = _make_fittrackee(mocker, workouts)
    fittrackee_mock.refresh_workout.side_effect = WorkoutNotFoundError("w1")
    main.refresh()
    assert fittrackee_mock.refresh_workout.call_count == 2


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


def _make_sync_env(
    mocker,
    activities,
    is_workout_present=True,
    fetch_file="/tmp/fake_activity.zip",
):
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
    fittrackee_mock.is_workout_present.return_value = is_workout_present
    fittrackee_mock.get_last_workout.return_value = last_workout
    mocker.patch.object(main, "Fittrackee", return_value=fittrackee_mock)
    mocker.patch.object(
        main.Sports, "get_fittrackee_sport_by_garmin_id", return_value=13
    )
    mocker.patch.object(main, "_fetch_garmin_activity_file", return_value=fetch_file)
    return garmin_mock, fittrackee_mock, db_mock


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
    _, fittrackee_mock, _ = _make_sync_env(mocker, [_make_activity()])
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
    _, fittrackee_mock, _ = _make_sync_env(mocker, [_make_activity()])
    fittrackee_mock.upload_workout.return_value = SimpleNamespace(id="w1")
    main.sync()
    fittrackee_mock.add_workout_no_gpx.assert_not_called()


def test_sync_config_missing(mocker):
    mocker.patch.object(main, "config_exists", return_value=False)
    fittrackee_mock = mocker.patch.object(main, "Fittrackee")
    main.sync()
    fittrackee_mock.assert_not_called()


def test_sync_invalid_activity_format(mocker):
    mocker.patch.object(main, "config_exists", return_value=True)
    with pytest.raises(typer.Exit):
        main.sync(activity_format="nope")


def test_sync_skips_existing_activity(mocker):
    _, fittrackee_mock, db_mock = _make_sync_env(mocker, [_make_activity()])
    db_mock.cursor().execute().fetchone.return_value = ("existing",)
    main.sync()
    fittrackee_mock.upload_workout.assert_not_called()
    fittrackee_mock.add_workout_no_gpx.assert_not_called()


def test_sync_activity_format_filter(mocker):
    _, fittrackee_mock, _ = _make_sync_env(mocker, [_make_activity()])
    fittrackee_mock.upload_workout.return_value = SimpleNamespace(id="w1")
    main.sync(activity_format="gpx")
    assert fittrackee_mock.upload_workout.call_count == 1


def test_sync_fetch_file_none_falls_back(mocker):
    _, fittrackee_mock, _ = _make_sync_env(mocker, [_make_activity()], fetch_file=None)
    fittrackee_mock.add_workout_no_gpx.return_value = SimpleNamespace(id="w1")
    main.sync()
    fittrackee_mock.upload_workout.assert_not_called()
    fittrackee_mock.add_workout_no_gpx.assert_called_once()


def test_sync_no_workout_interactive(mocker):
    garmin_mock, _, _ = _make_sync_env(mocker, [], is_workout_present=False)
    mocker.patch("typer.prompt", return_value="2020")
    main.sync(interactive=True)
    garmin_mock.login.assert_called_once()


def test_sync_no_workout_noninteractive_start_year(mocker):
    garmin_mock, _, _ = _make_sync_env(mocker, [], is_workout_present=False)
    main.sync(interactive=False, start_year=2020)
    garmin_mock.login.assert_called_once()


def test_sync_no_workout_noninteractive_no_year(mocker):
    _make_sync_env(mocker, [], is_workout_present=False)
    with pytest.raises(typer.Exit):
        main.sync(interactive=False, start_year=None)


def test_sync_start_year_too_old(mocker):
    _make_sync_env(mocker, [], is_workout_present=False)
    with pytest.raises(typer.Exit):
        main.sync(interactive=False, start_year=1980)


def test_fetch_garmin_activity_file(mocker, tmp_path):
    mocker.patch.object(main, "default_tmp_path", str(tmp_path))
    garmin_mock = mocker.Mock()
    garmin_mock.download_activity.return_value = b"fake-data"
    file = main._fetch_garmin_activity_file(
        garmin_mock, 123, main.Garmin.ActivityDownloadFormat.ORIGINAL
    )
    assert file == f"{tmp_path}/123.zip"
    assert Path(file).read_bytes() == b"fake-data"


def test_save_activity_mapping_sqlite_enabled(mocker):
    db_mock = mocker.Mock()
    workout = SimpleNamespace(id="w1")
    activity = {"activityId": 123}
    main._save_activity_mapping(db_mock, workout, activity, {"sqlite": {"use": True}})
    db_mock.cursor().execute.assert_called_once()
    db_mock.commit.assert_called_once()


def test_send_to_fittrackee():
    main._send_to_fittrackee()


def test_reset_no_force():
    main.reset(force=False)


def test_reset_force(mocker):
    db_mock = mocker.Mock()
    mocker.patch.object(main, "db", db_mock, create=True)
    fittrackee_mock = mocker.Mock()
    fittrackee_mock.get_all_workouts.return_value = [
        SimpleNamespace(id="w1"),
        SimpleNamespace(id="w2"),
    ]
    mocker.patch.object(main, "Fittrackee", return_value=fittrackee_mock)
    main.reset(force=True)
    assert db_mock.commit.call_count == 2
    assert fittrackee_mock.delete_workout.call_count == 2


def test_setup_fittrackee_success(mocker, tmp_path):
    mocker.patch.object(main, "config_path", str(tmp_path))
    fittrackee_class = mocker.patch.object(main, "Fittrackee")
    fittrackee_class.is_instance_is_supported.return_value = True
    main.fittrackee(
        client_id="cid",
        client_secret="cs",
        fittrackee_domain="https://ft.example.com",
        force=False,
    )
    fittrackee_class.assert_called_once_with(
        config_path=str(tmp_path),
        client_id="cid",
        client_secret="cs",
        host="ft.example.com",
    )


def test_setup_fittrackee_unsupported(mocker, tmp_path):
    mocker.patch.object(main, "config_path", str(tmp_path))
    fittrackee_class = mocker.patch.object(main, "Fittrackee")
    fittrackee_class.is_instance_is_supported.return_value = False
    with pytest.raises(typer.Exit):
        main.fittrackee(
            client_id="c",
            client_secret="s",
            fittrackee_domain="ft.example.com",
            force=False,
        )


def test_setup_fittrackee_prompts_when_args_missing(mocker, tmp_path):
    mocker.patch.object(main, "config_path", str(tmp_path))
    prompt = mocker.patch(
        "typer.prompt",
        side_effect=["cid", "cs", "https://ft.example.com"],
    )
    fittrackee_class = mocker.patch.object(main, "Fittrackee")
    fittrackee_class.is_instance_is_supported.return_value = True
    main.fittrackee()
    assert prompt.call_count == 3
    fittrackee_class.assert_called_once_with(
        config_path=str(tmp_path),
        client_id="cid",
        client_secret="cs",
        host="ft.example.com",
    )


def test_setup_fittrackee_force_unlinks_config(mocker, tmp_path):
    config_file = tmp_path / "fittrackee.yml"
    config_file.write_text("old")
    mocker.patch.object(main, "config_path", str(tmp_path))
    fittrackee_class = mocker.patch.object(main, "Fittrackee")
    fittrackee_class.is_instance_is_supported.return_value = True
    main.fittrackee(
        client_id="c",
        client_secret="s",
        fittrackee_domain="ft.example.com",
        force=True,
    )
    assert not config_file.exists()


def test_config_tool(mocker, tmp_path):
    mocker.patch.object(main, "config_path", str(tmp_path))
    db_mock = mocker.Mock()
    mocker.patch("sqlite3.connect", return_value=db_mock)
    db_path = str(tmp_path / "db")
    main.config_tool(database_path=db_path, verbose_level="DEBUG")
    assert "DEBUG" in (tmp_path / "config.yml").read_text()
    db_mock.cursor().execute.assert_called_once()


def test_config_exists_true(mocker):
    mocker.patch("pathlib.Path.is_dir", return_value=True)
    mocker.patch("pathlib.Path.is_file", return_value=True)
    assert main.config_exists() is True


def test_config_exists_false(mocker):
    mocker.patch("pathlib.Path.is_dir", return_value=False)
    mocker.patch("pathlib.Path.is_file", return_value=False)
    assert main.config_exists() is False


def test_main_dunder_with_config_import(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yml"
    cfg.write_text(f"log:\n  level: DEBUG\nsqlite:\n  path: '{tmp_path}'\n")
    monkeypatch.setenv("CONFIG_PATH", str(tmp_path))
    import contextlib
    import runpy

    with contextlib.suppress(SystemExit):
        runpy.run_path(main.__file__, run_name="__main__")
