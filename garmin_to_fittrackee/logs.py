import logging
from rich.logging import RichHandler


class Log:
    def __new__(self, name: str = "default", level: str = "DEBUG"):
        # handler = logging.StreamHandler()

        log = logging.basicConfig(
            level=level,
            format="%(message)s %(module)s %(funcName)s",
            handlers=[RichHandler(rich_tracebacks=True)],
        )
        log = logging.getLogger(name=name)

        return log
