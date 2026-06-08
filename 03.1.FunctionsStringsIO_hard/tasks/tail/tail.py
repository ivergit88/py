import sys
import typing as tp
from pathlib import Path


def tail(filename: Path, lines_amount: int = 10, output: tp.IO[bytes] | None = None) -> None:
    """
    :param filename: file to read lines from (the file can be very large)
    :param lines_amount: number of lines to read
    :param output: stream to write requested amount of last lines from file
                   (if nothing specified stdout will be used)
    """
    if output is None:
        output = sys.stdout.buffer

    with open(filename, 'rb') as f:
        f.seek(0, 2)
        file_size = f.tell()

        if file_size == 0:
            return

        chunk_size = 4096
        lines_found = 0
        position = file_size
        buffer = bytearray()

        while lines_found <= lines_amount and position > 0:
            read_size = min(chunk_size, position)
            position -= read_size
            f.seek(position)
            chunk = f.read(read_size)
            buffer = chunk + buffer

            lines_found = buffer.count(b'\n')

        lines = buffer.split(b'\n')

        if buffer.endswith(b'\n'):
            result_lines = lines[-(lines_amount + 1):-1]
        else:
            result_lines = lines[-lines_amount:]

        for line in result_lines:
            if line:
                output.write(line + b'\n')
