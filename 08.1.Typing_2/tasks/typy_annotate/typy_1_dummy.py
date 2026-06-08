import typing

def f(value: typing.Optional[float]) -> typing.Optional[float]:
    return value

TEST_SAMPLES = """
# ERROR
f("dd")

# ERROR
f(1j)

# SUCCESS
f(1)

# SUCCESS
f(1.0)

# SUCCESS
class R(float):
    pass

f(R(1))
"""

