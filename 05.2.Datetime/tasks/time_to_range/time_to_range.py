import datetime
import enum


class GranularityEnum(enum.Enum):
    DAY = datetime.timedelta(days=1)
    TWELVE_HOURS = datetime.timedelta(hours=12)
    HOUR = datetime.timedelta(hours=1)
    THIRTY_MIN = datetime.timedelta(minutes=30)
    FIVE_MIN = datetime.timedelta(minutes=5)


def truncate_to_granularity(
    dt: datetime.datetime,
    gtd: GranularityEnum
) -> datetime.datetime:
    if gtd is GranularityEnum.DAY:
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    if gtd is GranularityEnum.TWELVE_HOURS:
        return dt.replace(
            hour=(dt.hour // 12) * 12,
            minute=0,
            second=0,
            microsecond=0,
        )

    if gtd is GranularityEnum.HOUR:
        return dt.replace(minute=0, second=0, microsecond=0)

    if gtd is GranularityEnum.THIRTY_MIN:
        return dt.replace(
            minute=(dt.minute // 30) * 30,
            second=0,
            microsecond=0,
        )

    if gtd is GranularityEnum.FIVE_MIN:
        return dt.replace(
            minute=(dt.minute // 5) * 5,
            second=0,
            microsecond=0,
        )

    raise ValueError("Unknown granularity")


class DtRange:
    def __init__(
        self,
        before: int,
        after: int,
        shift: int,
        gtd: GranularityEnum
    ) -> None:
        self._before = before
        self._after = after
        self._shift = shift
        self._gtd = gtd

    def __call__(self, dt: datetime.datetime) -> list[datetime.datetime]:
        step = self._gtd.value
        center = truncate_to_granularity(dt + self._shift * step, self._gtd)

        result = []
        for offset in range(-self._before, self._after + 1):
            result.append(center + offset * step)
        return result


def get_interval(
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    gtd: GranularityEnum
) -> list[datetime.datetime]:
    step = gtd.value
    current = truncate_to_granularity(start_time, gtd)

    if current < start_time:
        current += step

    result = []
    while current <= end_time:
        result.append(current)
        current += step

    return result
