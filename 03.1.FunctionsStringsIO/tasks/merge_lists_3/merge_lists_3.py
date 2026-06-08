import heapq
import typing as tp


def merge(input_streams: tp.Sequence[tp.IO[bytes]], output_stream: tp.IO[bytes]) -> None:
    """
    Merge input_streams in output_stream
    :param input_streams: list of input streams. Contains byte-strings separated by "\n". Nonempty stream ends with "\n"
    :param output_stream: output stream. Contains byte-strings separated by "\n". Nonempty stream ends with "\n"
    :return: None
    """
    heap = []

    for i, stream in enumerate(input_streams):
        line = stream.readline()
        if line:
            val = int(line.decode().strip())
            heapq.heappush(heap, (val, i))

    while heap:
        val, stream_idx = heapq.heappop(heap)
        output_stream.write(f"{val}\n".encode())

        line = input_streams[stream_idx].readline()
        if line:
            new_val = int(line.decode().strip())
            heapq.heappush(heap, (new_val, stream_idx))
