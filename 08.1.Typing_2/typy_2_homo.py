import collections.abc
import typing as tp

Alpha = tp.TypeVar('Alpha', complex, float, int)
Beta = tp.TypeVar('Beta', complex, float, int)
Gamma = tp.TypeVar('Gamma', complex, float, int)

def f(callback: collections.abc.Callable[[Alpha, Beta, Gamma], float], x: Alpha, y: Beta, z: Gamma) -> float:
    return callback(x, y, z)
