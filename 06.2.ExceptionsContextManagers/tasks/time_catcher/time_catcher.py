import time


class TimeoutException(Exception):
    pass


class SoftTimeoutException(TimeoutException):
    pass


class HardTimeoutException(TimeoutException):
    pass


class TimeCatcher:
    def __init__(
        self,
        soft_timeout: float | None = None,
        hard_timeout: float | None = None,
    ) -> None:
        assert soft_timeout is None or soft_timeout > 0
        assert hard_timeout is None or hard_timeout > 0
        assert soft_timeout is None or hard_timeout is None or soft_timeout <= hard_timeout

        self.soft_timeout = soft_timeout
        self.hard_timeout = hard_timeout
        self._start: float | None = None
        self._elapsed: float | None = None

    def __enter__(self) -> "TimeCatcher":
        self._start = time.perf_counter()
        self._elapsed = None
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._elapsed = float(self)

        if self.hard_timeout is not None and self._elapsed > self.hard_timeout:
            raise HardTimeoutException
        if self.soft_timeout is not None and self._elapsed > self.soft_timeout:
            raise SoftTimeoutException
        return False

    def __float__(self) -> float:
        if self._elapsed is not None:
            return self._elapsed
        if self._start is None:
            return 0.0
        return time.perf_counter() - self._start

    def __str__(self) -> str:
        return f"Time consumed: {float(self):.4f}"
