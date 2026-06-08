from collections import UserList
import typing as tp


class ListTwist(UserList[tp.Any]):
    def __init__(self, elements: tp.Iterable[tp.Any] | None = None):
        super().__init__(list(elements) if elements is not None else [])

    def __getattr__(self, item: str) -> tp.Any:
        if item in ("reversed", "R"):
            return self.data[::-1]
        if item in ("first", "F"):
            return self.data[0]
        if item in ("last", "L"):
            return self.data[-1]
        if item in ("size", "S"):
            return len(self.data)
        raise AttributeError(item)

    def __setattr__(self, key: str, value: tp.Any) -> None:
        if key == "data":
            object.__setattr__(self, key, value)
            return

        if key in ("first", "F"):
            self.data[0] = value
            return

        if key in ("last", "L"):
            self.data[-1] = value
            return

        if key in ("size", "S"):
            new_size = int(value)
            cur_size = len(self.data)
            if new_size < cur_size:
                del self.data[new_size:]
            elif new_size > cur_size:
                self.data.extend([None] * (new_size - cur_size))
            return

        object.__setattr__(self, key, value)
