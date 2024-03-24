from pathlib import Path
from unittest import mock

import pendulum
import pytest
import requests
import requests_mock
import typer
import yaml

from garmin_to_fittrackee.fittrackee import Fittrackee

config_fittrackee_yaml = Path(f"{Path().resolve()}/tests/files/config_fittrackee.yaml")

expire_at = pendulum.now().add(days=7)
with config_fittrackee_yaml.open() as stream:
    data = yaml.load(stream, Loader=yaml.Loader)
data["tokens"]["expires_at"] = expire_at.timestamp()

config_fittrackee_yaml = yaml.dump(data)


@pytest.fixture
def fittrackee(mocker):
    with mock.patch("pathlib.Path.is_file", return_value=True):
        mocker.patch(
            "pathlib.Path.open", mocker.mock_open(read_data=config_fittrackee_yaml)
        )
        return Fittrackee("config/")


def test_fittrackee(fittrackee):
    assert (fittrackee.host) == "dev.localhost.tld"


def test_fittrackee_first_run(mocker):
    mocker.patch("pathlib.Path.is_file", return_value=False)
    mocker.patch("pathlib.Path.open", mocker.mock_open())
    mocker.patch(
        "typer.prompt",
        return_value="https://localhost/?code=UYahh0KeiquohsaidooRohshi2aeveepuu7zeeY6Ois4ZiDetee3quu0vi0eojee&state=eenah7oopahYeec8shi9hepaefae8iem",
    )
    expire_at = pendulum.now().add(days=7)
    mocker.patch(
        "requests_oauthlib.OAuth2Session.fetch_token",
        return_value={
            "access_token": "queeL7pah9tieniexeisoo5kux3ohsa",
            "expires_in": 864000,
            "refresh_token": "Ohsh9jau6ohdeethahp6te1eehivahB",
            "scope": ["workouts:read", "workouts:write", "profile:read"],
            "token_type": "Bearer",
            "expires_at": expire_at.timestamp(),
        },
    )
    fittrackee = Fittrackee(
        config_path="config/",
        client_id="gaiyo8iengim1ohjohqu3Iethaokaeso",
        client_secret="giPahYiechieGhath1fah9lohsh7Thoh",
        host="dev.localhost.tld",
    )
    assert fittrackee.host == "dev.localhost.tld"


config_bad_fittrackee_yaml = Path(
    f"{Path().resolve()}/tests/files/config_bad_fittrackee.yaml"
).read_text()


def bad_fittrackee(mocker):
    print(config_bad_fittrackee_yaml)
    with mocker.patch("pathlib.Path.is_file", return_value=True) and mocker.patch(
        "pathlib.Path.open", mocker.mock_open(read_data=config_bad_fittrackee_yaml)
    ):
        assert Fittrackee("config/") == typer.exceptions.Exit


all_workouts = Path(f"{Path().resolve()}/tests/files/all_workouts.json").read_text()


def test_get_all_workouts(fittrackee):
    with requests_mock.Mocker() as m:
        m.get(
            "https://dev.localhost.tld/api/workouts",
            text=all_workouts,
            status_code=200,
        )
        workouts = fittrackee.get_all_workouts()
        assert type(workouts[0]).__name__ == "Workout"
        assert type(workouts[1]).__name__ == "Workout"


def test_get_all_workouts_http_error(fittrackee):
    with requests_mock.Mocker() as m:
        m.get("https://dev.localhost.tld/api/workouts", status_code=401)
        workouts = fittrackee.get_all_workouts()
        assert workouts is None


def test_get_all_workouts_connection_error(fittrackee):
    with requests_mock.Mocker() as m:
        m.get(
            "https://dev.localhost.tld/api/workouts",
            exc=requests.exceptions.ConnectionError(),
        )
        workouts = fittrackee.get_all_workouts()
        assert workouts is None


def test_is_workout_present(fittrackee):
    with requests_mock.Mocker() as m:
        m.get(
            "https://dev.localhost.tld/api/workouts",
            text=all_workouts,
            status_code=200,
        )
        workout = fittrackee.is_workout_present()
        assert workout is True


def test_is_workout_present_http_error(fittrackee):
    with requests_mock.Mocker() as m:
        m.get("https://dev.localhost.tld/api/workouts", status_code=401)
        workout = fittrackee.is_workout_present()
        assert workout is None


def test_is_workout_present_connection_error(fittrackee):
    with requests_mock.Mocker() as m:
        m.get(
            "https://dev.localhost.tld/api/workouts",
            exc=requests.exceptions.ConnectionError(),
        )
        workout = fittrackee.is_workout_present()
        assert workout is None


def test_get_last_workout(fittrackee):
    with requests_mock.Mocker() as m:
        m.get(
            "https://dev.localhost.tld/api/workouts",
            text=all_workouts,
            status_code=200,
        )
        workout = fittrackee.get_last_workout()
        assert type(workout).__name__ == "Workout"


def test_get_last_workout_http_error(fittrackee):
    with requests_mock.Mocker() as m:
        m.get("https://dev.localhost.tld/api/workouts", status_code=401)
        workout = fittrackee.get_last_workout()
        assert workout is None


def test_get_last_workout_cconnection_error(fittrackee):
    with requests_mock.Mocker() as m:
        m.get(
            "https://dev.localhost.tld/api/workouts",
            exc=requests.exceptions.ConnectionError(),
        )
        workout = fittrackee.get_last_workout()
        assert workout is None


get_sports_json = Path(f"{Path().resolve()}/tests/files/get_sports.json").read_text()


def test_get_sports(fittrackee):
    with requests_mock.Mocker() as m:
        m.get(
            "https://dev.localhost.tld/api/sports",
            text=get_sports_json,
            status_code=200,
        )
        sports = fittrackee.get_sports()
        assert sports["data"]["sports"][0]["label"] == "Cycling (Sport)"


def test_delete_workout(fittrackee):
    workout_id = "eechieshocifah4ohquaiphiThiF9io"
    with requests_mock.Mocker() as m:
        m.delete(
            f"https://dev.localhost.tld/api/workouts/{workout_id}",
            text=all_workouts,
            status_code=200,
        )
        workout = fittrackee.delete_workout(workout_id=workout_id)
        assert workout is None


def test_delete_workout_http_error(fittrackee):
    workout_id = "eechieshocifah4ohquaiphiThiF9io"
    with requests_mock.Mocker() as m:
        m.delete(
            f"https://dev.localhost.tld/api/workouts/{workout_id}", status_code=401
        )
        workout = fittrackee.delete_workout(workout_id=workout_id)
        assert workout is None


def test_delete_workout_connection_error(fittrackee):
    workout_id = "eechieshocifah4ohquaiphiThiF9io"
    with requests_mock.Mocker() as m:
        m.delete(
            f"https://dev.localhost.tld/api/workouts/{workout_id}",
            exc=requests.exceptions.ConnectionError(),
        )
        workout = fittrackee.delete_workout(workout_id=workout_id)
        assert workout is None


saint_herblain_gpx = Path(
    f"{Path().resolve()}/tests/files/Saint-Herblain_58_4km.gpx"
).read_text()

post_gpx_responses = Path(
    f"{Path().resolve()}/tests/files/post_gpx_responses.json"
).read_text()


def test_upload_gpx(mocker, fittrackee):
    mocker.patch("pathlib.Path.open", mocker.mock_open(read_data=saint_herblain_gpx))
    mocker.patch("pathlib.Path.is_file", return_value=True)
    with requests_mock.Mocker() as m:
        m.post(
            "https://dev.localhost.tld/api/workouts",
            text=post_gpx_responses,
            status_code=201,
        )
        workout = fittrackee.upload_gpx(gpx_file="gpx/Saint-herblain.gpx", sport_id=1)
        assert type(workout).__name__ == "Workout"


def test_upload_gpx_no_file(mocker, fittrackee):
    with mocker.patch("pathlib.Path.is_file", return_value=False):
        workout = fittrackee.upload_gpx(gpx_file="gpx/Saint-herblain.gpx", sport_id=1)
        assert workout is None


def test_upload_gpx_http_error(mocker, fittrackee):
    mocker.patch("pathlib.Path.open", mocker.mock_open(read_data=saint_herblain_gpx))
    mocker.patch("pathlib.Path.is_file", return_value=True)
    with requests_mock.Mocker() as m:
        m.post(
            "https://dev.localhost.tld/api/workouts",
            status_code=401,
        )
        workout = fittrackee.upload_gpx(gpx_file="gpx/Saint-herblain.gpx", sport_id=1)
        assert workout is None


def test_upload_connection_error(mocker, fittrackee):
    mocker.patch("pathlib.Path.open", mocker.mock_open(read_data=saint_herblain_gpx))
    mocker.patch("pathlib.Path.is_file", return_value=True)
    with requests_mock.Mocker() as m:
        m.post(
            "https://dev.localhost.tld/api/workouts",
            exc=requests.exceptions.ConnectionError(),
        )
        workout = fittrackee.upload_gpx(gpx_file="gpx/Saint-herblain.gpx", sport_id=1)
        assert workout is None


# def test_fittrackee_token_update(fittrackee):
#    token = {
#        "access_token": "hoh2eu6eikee6Aisi1beez5ue5FieJohn4oeyoo3re2maic7Mee4Phohl",
#        "expires_at": 1705946492.499581,
#        "expires_in": 864000,
#        "refresh_token": "ihee2ieyaidoongoht1Agoo3thaiw9oWaeko5iePhei1Io4ooro6xehu",
#        "scope": ["workouts:read", "workouts:write", "profile:read"],
#        "token_type": "Bearer",
#    }
#    fittrackee.__token_update(token)
get_instance_config_response = Path(
    f"{Path().resolve()}/tests/files/get_config.json"
).read_text()


def test_get_instance_config(fittrackee):
    with requests_mock.Mocker() as m:
        m.get(
            "https://dev.localhost.tld/api/config",
            text=get_instance_config_response,
            status_code=200,
        )
        config = fittrackee.get_instance_config(host="dev.localhost.tld")
        assert config["data"]["version"] == "0.7.29"


def test_get_instance_config_http_error(fittrackee):
    with requests_mock.Mocker() as m:
        m.get(
            "https://dev.localhost.tld/api/config",
            status_code=500,
        )
        config = fittrackee.get_instance_config(host="dev.localhost.tld")
        assert config is None


def test_get_instance_config_connection_error(fittrackee):
    with requests_mock.Mocker() as m:
        m.get(
            "https://dev.localhost.tld/api/config",
            exc=requests.exceptions.ConnectionError(),
        )
        config = fittrackee.get_instance_config(host="dev.localhost.tld")
        assert config is None


def test_is_instance_is_supported():
    with requests_mock.Mocker() as m:
        m.get(
            "https://dev.localhost.tld/api/config",
            text=get_instance_config_response,
            status_code=200,
        )
        is_supported = Fittrackee.is_instance_is_supported(host="dev.localhost.tld")
        assert is_supported is True


get_instance_config_bad_response = Path(
    f"{Path().resolve()}/tests/files/get_bad_config.json"
).read_text()


def test_is_instance_is_supported_bad_version():
    with requests_mock.Mocker() as m:
        m.get(
            "https://dev.localhost.tld/api/config",
            text=get_instance_config_bad_response,
            status_code=200,
        )
        is_supported = Fittrackee.is_instance_is_supported(host="dev.localhost.tld")
        assert is_supported is False
