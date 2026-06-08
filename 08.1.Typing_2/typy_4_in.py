import numbers
import typing as tp

ValueType = tp.TypeVar('ValueType', str, numbers.Real, int)

def f(collection: tp.Container[ValueType], item: ValueType) -> tp.Optional[ValueType]:
    return item if item in collection else None
