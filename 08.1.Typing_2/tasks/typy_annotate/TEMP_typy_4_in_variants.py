import numbers
import typing as tp

U = tp.TypeVar("U", str, numbers.Real, int)


def f1(collection: tp.Container[U], item: U) -> tp.Optional[U]:
    return item if item in collection else None


def f2(collection: tp.Container[object], item: U) -> tp.Optional[U]:
    return item if item in collection else None


class AContainer(tp.Protocol[U]):
    def __contains__(self, item: object, /) -> bool: ...


def f3(collection: tp.Container[U], item: U) -> tp.Optional[U]:
    return item if item in collection else None


def f4(collection: tp.Container[object], item: U) -> tp.Optional[U]:
    return item if item in collection else None

