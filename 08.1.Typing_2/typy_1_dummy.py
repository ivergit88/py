import typing

def f(items: tuple[typing.Optional[float], ...]) -> typing.Optional[float]:
    return items[0] if items else None

TEST_SAMPLES = """
SUCCESS
f((1, 1, 2, 4))

SUCCESS
f((1,))

SUCCESS
f((1.2, 3.4))

ERROR
f((1j, 3j, 6j, 7j))

SUCCESS
f((True, False))

ERROR
f(("there", "are", "no", "reason"))

ERROR
f(("there", 1))
"""
