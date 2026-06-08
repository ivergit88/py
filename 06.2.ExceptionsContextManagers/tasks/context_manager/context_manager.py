from contextlib import contextmanager
import sys
import traceback
from typing import Iterator, TextIO, Type


@contextmanager
def supresser(*types_: Type[BaseException]) -> Iterator[None]:
    try:
        yield
    except types_:
        pass


@contextmanager
def retyper(type_from: Type[BaseException], type_to: Type[BaseException]) -> Iterator[None]:
    try:
        yield
    except type_from as exc:
        raise type_to(*exc.args).with_traceback(exc.__traceback__)


@contextmanager
def dumper(stream: TextIO | None = None) -> Iterator[None]:
    target = sys.stderr if stream is None else stream
    try:
        yield
    except Exception as exc:
        target.write("".join(traceback.format_exception_only(type(exc), exc)))
        target.flush()
        raise
