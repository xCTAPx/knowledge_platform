import logging
from pathlib import Path

_FILE = Path(__file__).resolve().parents[2] / "logs" / "app.log"


def logger(name: str) -> logging.Logger:
    log = logging.getLogger(name)
    if log.handlers:
        return log
    _FILE.parent.mkdir(exist_ok=True)
    handler = logging.FileHandler(_FILE, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    log.setLevel(logging.INFO)
    log.addHandler(handler)
    log.propagate = False
    return log
