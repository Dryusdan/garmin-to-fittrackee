from pathlib import Path

import pendulum
import typer
import yaml
from requests_oauthlib import OAuth2Session
from rich import print

from garmin_to_fittrackee.logs import Log

log = Log(__name__)


class Workout:
    def __init__(
        ascent: float,
        ave_speed: float,
        bounds: list,
        creation_date: str,
        descent: float,
        distance: float,
        duration: str,
        id: str,
        map: str,
        max_alt: float,
        max_speed: float,
        min_alt: float,
        moving: str,
        notes: str,
        pauses: str,
        records: list,
        segments: list,
        sport_id: int,
        title: str,
        user: str,
        weather_end: dict,
        weather_start: dict,
        with_gpx: bool,
        workout_date: str,
        modification_date: str = None,
    ):
        self.ascent: float = ascent
        self.ave_speed: float = ave_speed
        self.bounds: list = bounds
        self.creation_date: str = creation_date
        self.descent: float = descent
        self.distance: float = distance
        self.duration: str = duration
        self.id: str = id
        self.map: str = map
        self.max_alt: float = max_alt
        self.max_speed: float = max_speed
        self.min_alt: float = min_alt
        self.moving: str = moving
        self.notes: str = notes
        self.pauses: str = pauses
        self.records: list = records
        self.segments: list = segments
        self.sport_id: int = sport_id
        self.title: str = title
        self.user: str = user
        self.weather_end: dict = weather_end
        self.weather_start: dict = weather_start
        self.with_gpx: bool = with_gpx
        self.workout_date: str = workout_date
        self.modification_date: str = modification_date

    def present_in_fittrackee(self):
        self.present_in_fittrackee = True

    def present_in_garmin(self):
        self.present_in_garmin = True
