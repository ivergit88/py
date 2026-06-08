from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Mapping, Sequence
from functools import wraps
from typing import Any, TypeVar


Function = TypeVar('Function', bound=Callable[..., Any])


def cache(max_size: int) -> Callable[[Function], Function]:
    """
    Returns decorator, which stores result of function
    for `max_size` most recent function arguments.
    :param max_size: max amount of unique arguments to store values for
    :return: decorator, which wraps any function passed
    """

    if max_size <= 0:
        raise ValueError('max_size should be positive')

    def decorator(func: Function) -> Function:
        storage: OrderedDict[tuple[Any, ...], Any] = OrderedDict()

        def _to_hashable(obj: Any) -> Any:
            if isinstance(obj, Mapping):
                return tuple((key, _to_hashable(value)) for key, value in sorted(obj.items()))
            if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
                return tuple(_to_hashable(value) for value in obj)
            if isinstance(obj, set):
                return tuple(sorted(_to_hashable(value) for value in obj))
            return obj

        def _make_key(args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[Any, ...]:
            return (_to_hashable(args), _to_hashable(kwargs))

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:  # type: ignore[misc]
            key = _make_key(args, kwargs)
            if key in storage:
                storage.move_to_end(key)
                return storage[key]

            result = func(*args, **kwargs)
            storage[key] = result
            storage.move_to_end(key)
            if len(storage) > max_size:
                storage.popitem(last=False)
            return result

        return wrapper  # type: ignore[misc]

    return decorator
