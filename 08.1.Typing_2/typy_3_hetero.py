import typing as tp

WordType = tp.TypeVar('WordType', bound=str)

def f(data: tuple[tp.Sized, WordType, tp.Sequence[str]]) -> WordType:
    return data[1]
