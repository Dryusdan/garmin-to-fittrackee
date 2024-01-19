from pathlib import Path

from garmin_to_fittrackee.logs import Log

config_yaml = Path(f"{Path().resolve()}/tests/files/config.yml").read_text()


def test_log_without_args(mocker):
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pathlib.Path.is_file", return_value=True)
    mocker.patch("pathlib.Path.open", mocker.mock_open(read_data=config_yaml))
    log = Log(name="test", level="INFO")
    assert log.level == 0


config_without_logs_yaml = Path(
    f"{Path().resolve()}/tests/files/config_without_logs.yml"
).read_text()


def test_log_without_args_without_logs(mocker):
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pathlib.Path.is_file", return_value=True)
    mocker.patch(
        "pathlib.Path.open", mocker.mock_open(read_data=config_without_logs_yaml)
    )
    log = Log(name="test", level="INFO")
    assert log.level == 0


def test_log_without_args_without_config(mocker):
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("pathlib.Path.is_file", return_value=False)
    log = Log()
    assert log.level == 0


def test_log_info():
    log = Log(name="test", level="INFO")
    assert log.level == 0
