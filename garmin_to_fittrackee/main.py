import os
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import pendulum
import typer
import yaml
from garminconnect import Garmin
from typing_extensions import Annotated

from garmin_to_fittrackee.fittrackee import Fittrackee
from garmin_to_fittrackee.logs import Log
from garmin_to_fittrackee.sports import Sports

log = Log(name=__name__)

app = typer.Typer()


def default_config_path():
    home = str(Path.home())
    return f"{home}/.config/garmin-to-fittrackee"


def default_database_path():
    home = str(Path.home())
    return f"{home}/.local/share/garmin_to_fittrackee"


config_path = os.environ.get("CONFIG_PATH", default_config_path())
database_path = os.environ.get("DATABASE_PATH", default_database_path())
Path(config_path).mkdir(parents=True, exist_ok=True)

setup = typer.Typer()
app.add_typer(setup, name="setup")

if Path(f"{config_path}/config.yml").is_file():
    log.debug("Import config")
    with open(f"{config_path}/config.yml") as file:
        config = yaml.safe_load(file)

    db = sqlite3.connect(f"{config['sqlite']['path']}/db.sqlite3")


@app.command()
def sync(
    start_year: Annotated[
        int,
        typer.Option(
            help=(
                "Year of your first record."
                "Only used when no workouts found on Fittrackee."
            )
        ),
    ] = None,
    interactive: Annotated[
        bool, typer.Option(help="Can ask question during the sync")
    ] = True,
):
    """
    Synchronise Garmin's activities in Fittrackee.
    First run, all of gamin's activities will be fetch.
    """
    if not config_exists():
        return

    fittrackee = Fittrackee(config_path)
    if fittrackee.is_workout_present():
        workout = fittrackee.get_last_workout()
        start_datetime = pendulum.parse(workout.workout_date, strict=False)
        log.debug(f"Start date is {start_datetime.isoformat()}")
        start_datetime = start_datetime.add(minutes=1)
        end_datetime = start_datetime.add(days=1)
    else:
        if interactive:
            log.warning("No workout present on Fittrackee")
            start_year = int(typer.prompt("What year was your first Garmin activity?"))
            log.info(f"Okay, fetching activity on Garmin from year {start_year}")
        elif not interactive and start_year is not None:
            log.warning(
                "No workout present on Fittrackee."
                f"Fetch all workouts on Garmin from year {start_year}"
            )
        else:
            log.error(
                "Not workout found on Fittrackee and --no-interactive set."
                "Please specify a year to start with --start-year"
            )
            raise typer.Exit(code=1)
        if start_year < 1990:
            log.error(
                "Garmin was created at the end of the year 1989 only for US army."
                "I'm sure you don't have GPX file from this date"
            )
            raise typer.Exit(code=1)
        start_datetime = pendulum.datetime(start_year, 1, 1, 0, 0, 0)
        end_datetime = start_datetime.add(days=1)

    today = pendulum.now()
    if today.diff(end_datetime, False).in_seconds() > 0:
        end_datetime = today
    garmin = Garmin()
    garmin.login(f"{config_path}/garmintoken")
    log.debug(
        f"Condition in while : {today.diff(start_datetime, False).in_seconds()} < 0"
    )
    while today.diff(start_datetime, False).in_seconds() < 0:
        log.info(
            "Fetching activities on Garmin"
            f"from {start_datetime.to_formatted_date_string()}"
            f"to {end_datetime.to_formatted_date_string()}"
        )
        activities = garmin.get_activities_by_date(
            start_datetime.isoformat(), end_datetime.isoformat()
        )
        if activities:
            for activity in activities:
                cur = db.cursor()
                res = cur.execute(
                    f"SELECT garmin_id "
                    f"FROM activities_ids "
                    f"WHERE garmin_id='{activity['activityId']}'"
                )
                if res.fetchone() is not None:
                    continue
                activityType_id = activity["activityType"]["typeId"]
                fittrackee_sport_id = Sports.get_fittrackee_sport_by_garmin_id(
                    activityType_id
                )
                gpx_data = garmin.download_activity(
                    activity["activityId"], Garmin.ActivityDownloadFormat.GPX
                )
                gpx_file = f"/tmp/{str(activity['activityId'])}.gpx"
                with open(gpx_file, "wb") as fb:
                    fb.write(gpx_data)
                    log.info(f"Activity data downloaded to file {gpx_file}")
                workout = fittrackee.upload_gpx(
                    gpx_file=gpx_file, sport_id=fittrackee_sport_id
                )
                if workout is not None:
                    log.debug(f"Deleting {gpx_file}")
                    Path(gpx_file).unlink(missing_ok=True)
                    if config["sqlite"]["use"]:
                        log.debug(
                            "Adding workout and activity matches in tool database"
                        )
                        log.debug(
                            f"Using Fittrackee ID {workout.id}"
                            f"and Garmin ID {activity['activityId']}"
                        )
                        data_insert = (workout.id, activity["activityId"])
                        cur = db.cursor()
                        cur.execute(
                            "INSERT INTO activities_ids (fittrackee_id, garmin_id)"
                            "VALUES(?, ?)",
                            data_insert,
                        )
                        db.commit()
        start_datetime = start_datetime.add(days=2)
        end_datetime = start_datetime.add(days=1)
        if today.diff(end_datetime, False).in_seconds() > 0:
            end_datetime = today


@app.command()
def reset(
    force: Annotated[
        bool,
        typer.Option(help="Security reason, you need to force the reset"),
    ] = False,
):
    """
    Reset database and remove ALL of workouts in Fittrackee. (Usefull for development)
    """
    if not force:
        log.warning("No force, no chocolate")
        return
    cur = db.cursor()
    cur.execute("DROP TABLE activities_ids")
    db.commit()
    cur = db.cursor()
    cur.execute(
        "CREATE TABLE"
        "activities_ids(fittrackee_id VARCHAR(255) UNIQUE,"
        "garmin_id INTEGER(100) UNIQUE"
        ")"
    )
    db.commit()
    fittrackee = Fittrackee(config_path)
    workouts = fittrackee.get_all_workouts()
    if workouts:
        for workout in workouts:
            fittrackee.delete_workout(workout.id)


@setup.command()
def garmin(
    email: Annotated[
        str,
        typer.Option(
            help="Email of your Garmin account. If not specify, we use prompt."
        )
        == "",
        typer.Option(prompt=True),
    ],
    password: Annotated[
        str,
        typer.Option(
            help="Password of your Garmin account. If not specify, we use prompt."
        )
        == "",
        typer.Option(prompt=True, hide_input=True),
    ],
    store: bool = True,
):
    garmin = Garmin(email, password)
    garmin.login()
    if store:
        data = {"garmin": {"username": email, "password": password}}
        with open(f"{config_path}/garmin.yml", "w") as file:
            yaml.dump(data, file, default_flow_style=False)

    garmin.garth.dump(f"{config_path}/garmintoken")


@setup.command()
def fittrackee(
    client_id: Annotated[
        str,
        typer.Option(help="Client id of fittrackee. If not specify, we use prompt.")
        == "",
        typer.Option(prompt=True),
    ],
    client_secret: Annotated[
        str,
        typer.Option(help="Client secret of fittrackee. If not specify, we use prompt.")
        == "",
        typer.Option(prompt=True, hide_input=True),
    ],
    fittrackee_domain: Annotated[
        str,
        typer.Option(
            help=(
                "Domain of Fittrackee instance (without https)."
                "If not specify, we use prompt."
            )
        )
        == "",
        typer.Option(prompt=True),
    ],
    force: Annotated[bool, typer.Option(help="Rewrite configuration file")] = False,
):
    if force:
        log.warning("Rewrite configuration file")
        Path(f"{config_path}/fittrackee.yml").unlink(missing_ok=True)
    url = urlparse(fittrackee_domain)
    if url.hostname:
        fittrackee_domain = url.hostname
    if not Fittrackee.is_instance_is_supported(host=fittrackee_domain):
        log.error(
            "Fittrackee instance isn't supported. "
            "Please update your Fittrackee instance"
        )
        raise typer.Exit(code=1)
    Fittrackee(
        config_path=config_path,
        client_id=client_id,
        client_secret=client_secret,
        host=fittrackee_domain,
    )


@setup.command()
def config_tool(
    database_path: Annotated[
        str,
        typer.Option(help="Database location. If not exist, path will be created."),
    ] = database_path,
    verbose_level: Annotated[
        str,
        typer.Option(help="Verbose level. Maybe DEBUG, INFO, WARNING, ERROR, CRITICAL"),
    ] = "INFO",
):
    data = {
        "sqlite": {"use": True, "path": database_path},
        "log": {"level": verbose_level},
    }
    with open(f"{config_path}/config.yml", "w") as file:
        yaml.dump(data, file, default_flow_style=False)
    log.debug("Create database")
    path = Path(database_path)
    path.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(f"{database_path}/db.sqlite3")
    cur = db.cursor()
    cur.execute(
        "CREATE TABLE "
        "activities_ids(fittrackee_id VARCHAR(255) UNIQUE,"
        "garmin_id INTEGER(100) UNIQUE)"
    )


def config_exists():
    if (
        not Path(f"{config_path}/garmintoken").is_dir()
        or not Path(f"{config_path}/fittrackee.yml").is_file()
        or not Path(f"{config_path}/config.yml").is_file()
    ):
        log.error(
            "Config files aren't present."
            "Start using garmin-to-fittrackee with `setup config-tool`,"
            "`setup garmin` and `setup fittrackee` command"
        )
        return False
    else:
        return True


if __name__ == "__main__":
    config_exists()
    app()
