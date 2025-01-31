import json
from pathlib import Path
from typing import Union

import pendulum
import requests
import typer
import yaml
from packaging.version import Version
from requests_oauthlib import OAuth2Session
from rich import print

from garmin_to_fittrackee.logs import Log
from garmin_to_fittrackee.workout import Workout

log = Log(__name__)


class Fittrackee:
    def __init__(
        self,
        config_path: str,
        client_id: str = None,
        client_secret: str = None,
        host: str = None,
        timezone: str = None,
        verify: bool = True,
    ):
        log.debug("Initializing FitTrackeeConnector")
        self.config_path = config_path
        self.tokens = None
        self.host = host
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = None
        self.sports = None
        if timezone is None:
            dt = pendulum.now()
            timezone = dt.timezone.name
        self.timezone = timezone
        self.__load_config()
        self.client = self.__auth()

    def __save_config(self):
        log.debug("Saving data")
        data = {
            "fittrackee": {
                "host": self.host,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            "tokens": self.tokens,
        }
        fittrackee_config = Path(f"{self.config_path}/fittrackee.yml")
        with fittrackee_config.open("w", encoding="utf-8") as file:
            yaml.dump(data, file, default_flow_style=False)
        return

    def __load_config(self):
        fittrackee_config = Path(f"{self.config_path}/fittrackee.yml")
        if fittrackee_config.is_file():
            with fittrackee_config.open() as stream:
                try:
                    config = yaml.load(stream, Loader=yaml.Loader)
                except (yaml.YAMLError, yaml.scanner.ScannerError) as exc:
                    log.error(
                        "Can't load configuration."
                        "Please check {self.config_path}/fittrackee.yml"
                        "or remove this file"
                    )
                    log.error(exc)
                    raise typer.Exit(code=1) from None

            self.tokens = config["tokens"]
            self.client_id = config["fittrackee"]["client_id"]
            self.client_secret = config["fittrackee"]["client_secret"]
            self.host = config["fittrackee"]["host"]
            self.api_url = f"https://{self.host}/api"

    def __auth(self):
        """
        Checks if a valid access token exists in the token file;
        if not, tries to get a new one via a refresh token (if present)
        or prompts the user to authenticate in order to get a brand new
        token.
        """
        log.debug("Setting up FitTrackee auth")
        if self.tokens is None:
            log.debug("No FitTrackee tokens found; fetching new ones")
            return self.__web_application_flow()
        else:
            log.debug("Using existing FitTrackee tokens with self-refreshing client")
            return self.__get_refreshing_client()

    def __web_application_flow(self):
        authorize_url = f"https://{self.host}/profile/apps/authorize"
        self.api_url = f"https://{self.host}/api"

        redirect_uri = "https://localhost/"
        scope = "workouts:read workouts:write profile:read"
        oauth = OAuth2Session(self.client_id, redirect_uri=redirect_uri, scope=scope)
        authorization_url, state = oauth.authorization_url(authorize_url)
        print(f"Please go to {authorization_url} and authorize access.\n")
        authorization_response = typer.prompt(
            "Enter the full callback URL from the browser address bar"
            "after you are redirected and press <enter>"
        )
        print(authorization_response)
        log.debug("Logging to fittrackee instance")
        self.tokens = oauth.fetch_token(
            f"{self.api_url}/oauth/token",
            authorization_response=authorization_response,
            client_secret=self.client_secret,
            include_client_id=True,
            verify=True,
        )
        log.info("Logging successfull. Saving configuration")
        self.__save_config()
        return oauth

    def __get_refreshing_client(self):
        refresh_params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        client = OAuth2Session(
            self.client_id,
            token=self.tokens,
            auto_refresh_url=f"{self.api_url}/oauth/token",
            auto_refresh_kwargs=refresh_params,
            token_updater=self.__token_update,
        )
        return client

    def __token_update(self, token):
        log.debug("New token receive. Save it")
        self.tokens = token
        self.__save_config()

    def is_workout_present(self):
        try:
            r = self.client.get(
                f"{self.api_url}/workouts", params={"per_page": 1, "page": 1}
            )
            r.raise_for_status()
        except requests.exceptions.HTTPError as error:
            error_code = error.response.status_code
            log.debug(error.response.headers)
            log.error(
                "Failed to get all workouts."
                f"Return code {error_code}. Error {error.response.text}"
            )
            return
        except requests.RequestException as e:
            log.error(str(e))
            return
        results = r.json()
        log.debug(f"Workkouts: {results['data']['workouts']}")
        log.debug(f"Count workkouts: {len(results['data']['workouts'])}")
        return len(results["data"]["workouts"]) != 0

    def get_all_workouts(self, pagination: int = 50):
        workouts = []
        log.info(f"Get all workout from fittrackee (in page of {pagination})")
        results = {"pagination": {"has_next": True}}
        page = 1
        while results["pagination"]["has_next"]:
            try:
                r = self.client.get(
                    f"{self.api_url}/workouts",
                    params={"per_page": pagination, "page": page},
                )
                r.raise_for_status()
            except requests.exceptions.HTTPError as error:
                error_code = error.response.status_code
                log.debug(error.response.headers)
                log.error(
                    "Failed to get all workouts."
                    f"Return code {error_code}. Error {error.response.text}"
                )
                return
            except requests.RequestException as e:
                log.error(str(e))
                return
            results = r.json()
            for workout in results["data"]["workouts"]:
                workout_object = object.__new__(Workout)
                workout_object.__dict__ = workout
                workout_object.set_present_in_fittrackee()
                workouts.append(workout_object)
            log.debug(
                f"Fetched page {page} of workouts " f"(fetched {len(workouts)} so far)"
            )
            page += 1
            return workouts

    def get_last_workout(self):
        try:
            r = self.client.get(
                f"{self.api_url}/workouts",
                params={"per_page": 1, "page": 1, "order": "desc"},
            )
            r.raise_for_status()
        except requests.exceptions.HTTPError as error:
            error_code = error.response.status_code
            log.debug(error.response.headers)
            log.error(
                "Failed to get workout."
                f"Return code {error_code}. Error {error.response.text}"
            )
            return
        except requests.RequestException as e:
            log.error(str(e))
            return
        results = r.json()
        for workout in results["data"]["workouts"]:
            workout_object = object.__new__(Workout)
            workout_object.__dict__ = workout
            workout_object.set_present_in_fittrackee()
            return workout_object

    def upload_gpx(self, gpx_file: Union[str, Path], sport_id: int, notes: str = None):
        """
        Higly inspired of https://github.com/jat255/strava-to-fittrackee/blob/main/strava_to_fittrackee/s2f.py#L805
        """
        if not Path(gpx_file).is_file():
            log.error(f"{gpx_file} is not exist or is not a file")
            return

        # with open(gpx_file, "r") as f:
        #    gpx = gpxpy.parse(f)
        log.debug(f"posting {gpx_file} to FitTrackee")
        data = {"sport_id": sport_id, "notes": ""}
        gpx = Path(gpx_file)
        try:
            r = self.client.post(
                f"{self.api_url}/workouts",
                files=dict(file=gpx.open("rb")),
                data=dict(data=json.dumps(data)),
            )
            r.raise_for_status()
        except requests.exceptions.HTTPError as error:
            error_code = error.response.status_code
            log.debug(error.response.headers)
            log.error(
                f"Failed to post {gpx_file}."
                f"Return code {error_code}. Error {error.response.text}"
            )
            return
        except requests.RequestException as e:
            log.error(str(e))
            return
        results = r.json()
        workout = object.__new__(Workout)
        workout.__dict__ = results["data"]["workouts"][0]
        workout.set_present_in_fittrackee()
        workout.set_present_in_garmin()
        log.info(f"Activity added on Fittrackee with id {workout.id}")
        return workout

    def get_sports(self):
        """
        Needed only during development
        """
        r = self.client.get(f"{self.api_url}/sports")
        results = r.json()
        return results

    def delete_workout(self, workout_id: int):
        try:
            r = self.client.delete(f"{self.api_url}/workouts/{workout_id}")
            r.raise_for_status()
        except requests.exceptions.HTTPError as error:
            error_code = error.response.status_code
            log.debug(error.response.headers)
            log.error(
                "Failed to get sports's list."
                f"Return code {error_code}. Error {error.response.text}"
            )
            return
        except requests.RequestException as e:
            log.error(str(e))
            return
        log.warning(f"Workout {workout_id} deleted")

    @staticmethod
    def get_instance_config(host: str):
        try:
            r = requests.get(f"https://{host}/api/config")
            r.raise_for_status()
        except requests.exceptions.HTTPError as error:
            error_code = error.response.status_code
            log.debug(error.response.headers)
            log.error(
                "Failed to get instance config."
                f"Return code {error_code}. Error {error.response.text}"
            )
            return
        except requests.RequestException as e:
            log.error(str(e))
            return
        return r.json()

    @staticmethod
    def is_instance_is_supported(host: str):
        config = Fittrackee.get_instance_config(host=host)
        if not (
            config
            and "data" in config
            and "version" in config["data"]
            and Version(config["data"]["version"]) >= Version("0.7.29")
            and Version(config["data"]["version"]) < Version("0.10")
        ):
            return False
        return True
