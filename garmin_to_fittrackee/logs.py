import logging
from pathlib import Path

import yaml
from rich.logging import RichHandler

home = str(Path.home())
config_path = f"{home}/.config/garmin-to-fittrackee"


class Log:
    def __new__(self, name: str = "default", level: str = None):
        config_file = Path(f"{config_path}/config.yml")
        if config_file.exists() and config_file.is_file():
            with config_file.open("r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
            if (
                config is not None
                and "log" in config
                and "level" in config["log"]
                and level is None
            ):
                level = config["log"]["level"]
            else:
                level = "INFO"
        elif level is None:
            level = "INFO"

        log = logging.basicConfig(
            level=level,
            format="%(message)s %(module)s %(funcName)s",
            handlers=[RichHandler(rich_tracebacks=True)],
        )
        log = logging.getLogger(name=name)

        return log
