import typing as tp


@tp.overload
def f(container: list[int], item: int) -> tp.Optional[int]: ...

@tp.overload
def f(container: set[int], item: int) -> tp.Optional[int]: ...

@tp.overload
def f(container: str, item: str) -> tp.Optional[str]: ...

@tp.overload
def f(container: list[float], item: float) -> tp.Optional[float]: ...

@tp.overload
def f(container: set[float], item: float) -> tp.Optional[float]: ...

@tp.overload
def f(container: list[str], item: str) -> tp.Optional[str]: ...

@tp.overload
def f(container: set[str], item: str) -> tp.Optional[str]: ...

@tp.overload
def f(container: tp.Sized, item: int) -> tp.Optional[int]: ...

@tp.overload
def f(container: tp.Sized, item: str) -> tp.Optional[str]: ...

def f(container: object, item: object) -> tp.Optional[object]:
    return item if item in container else None  # type: ignore


TEST_SAMPLES = """
# SUCCESS
a: float | None
a = f([1, 2, 3], 1)
if a is not None:
    a += 1

# SUCCESS
a: float | None
a = f({1, 2, 3}, 1)

# SUCCESS
a: str | None
a = f("abcd", "a")

# SUCCESS
class A:
    def __contains__(self, a: object) -> bool:
        return True

a: int | None
a = f(A(), 10)

b: str | None
b = f(A(), "qwerty")

# ERROR
f([1, 2, 3], "h")

# ERROR
f([1, 2, 3], 1.3)

# ERROR
f([1.4, 2, 3], 1)

# ERROR
f(["a", "b", "c"], 1)
"""
