import typing as tp

NumericType = tp.TypeVar('NumericType', float, int)

class Pair(tp.Generic[NumericType]):
    def __init__(self, val1: NumericType, val2: NumericType) -> None:
        self.val1: NumericType = val1
        self.val2: NumericType = val2

    def sum(self) -> NumericType:
        return self.val1 + self.val2

    def first(self) -> NumericType:
        return self.val1

    def second(self) -> NumericType:
        return self.val2

    def __iadd__(self, other: "Pair[NumericType]") -> "Pair[NumericType]":
        res1: NumericType = self.val1 + other.val1
        res2: NumericType = self.val2 + other.val2
        return Pair[NumericType](res1, res2)
