import zoneinfo
from datetime import datetime

DEFAULT_TZ_NAME = "Europe/Moscow"
MOSCOW_TZ = zoneinfo.ZoneInfo(DEFAULT_TZ_NAME)


def _to_moscow(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=MOSCOW_TZ)
    return dt.astimezone(MOSCOW_TZ)


def now() -> datetime:
    return datetime.now(MOSCOW_TZ)


def strftime(dt: datetime, fmt: str) -> str:
    return _to_moscow(dt).strftime(fmt)


def strptime(dt_str: str, fmt: str) -> datetime:
    parsed = datetime.strptime(dt_str, fmt)
    return _to_moscow(parsed)


def diff(first_dt: datetime, second_dt: datetime) -> int:
    return int((_to_moscow(second_dt) - _to_moscow(first_dt)).total_seconds())


def timestamp(dt: datetime) -> int:
    return int(_to_moscow(dt).timestamp())


def from_timestamp(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, tz=MOSCOW_TZ)
