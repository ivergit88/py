from collections.abc import Iterable, Iterator, Sized


class RangeIterator(Iterator[int]):
    """The iterator class for Range"""
    def __init__(self, range_: 'Range') -> None:
        self._range = range_
        self._index = 0

    def __iter__(self) -> 'RangeIterator':
        return self

    def __next__(self) -> int:
        if self._index >= len(self._range):
            raise StopIteration
        value = self._range[self._index]
        self._index += 1
        return value


class Range(Sized, Iterable[int]):
    """The range-like type, which represents an immutable sequence of numbers"""

    def __init__(self, *args: int) -> None:
        """
        :param args: either it's a single `stop` argument
            or sequence of `start, stop[, step]` arguments.
        If the `step` argument is omitted, it defaults to 1.
        If the `start` argument is omitted, it defaults to 0.
        If `step` is zero, ValueError is raised.
        """
        if len(args) == 1:
            self.start = 0
            self.stop = args[0]
            self.step = 1
        elif len(args) == 2:
            self.start, self.stop = args
            self.step = 1
        elif len(args) == 3:
            self.start, self.stop, self.step = args
        else:
            raise TypeError(f'Range expected 1-3 arguments, got {len(args)}')

        if self.step == 0:
            raise ValueError('Range() arg 3 must not be zero')
        self._len = self._calc_len()

    def _calc_len(self) -> int:
        if self.step > 0:
            if self.start >= self.stop:
                return 0
            return (self.stop - self.start + self.step - 1) // self.step
        if self.start <= self.stop:
            return 0
        step = -self.step
        return (self.start - self.stop + step - 1) // step

    def __iter__(self) -> 'RangeIterator':
        return RangeIterator(self)

    def __repr__(self) -> str:
        if self.step == 1:
            return f'range({self.start}, {self.stop})'
        return f'range({self.start}, {self.stop}, {self.step})'

    def __str__(self) -> str:
        return repr(self)

    def __contains__(self, key: int) -> bool:
        if len(self) == 0:
            return False
        if self.step > 0:
            if key < self.start or key >= self.stop:
                return False
        elif key > self.start or key <= self.stop:
            return False
        return (key - self.start) % self.step == 0

    def __getitem__(self, key: int) -> int:
        if key < 0:
            key += len(self)
        if key < 0 or key >= len(self):
            raise IndexError('Range object index out of range')
        return self.start + key * self.step

    def __len__(self) -> int:
        return self._len
