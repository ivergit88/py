import heapq
import typing as tp


def merge(seq: tp.Sequence[tp.Sequence[int]]) -> list[int]:
    """
    :param seq: sequence of sorted sequences
    :return: merged sorted list
    """
    result: list[int] = []
    heap: list[tuple[int, int, int]] = []

    for list_idx, lst in enumerate(seq):
        if lst:
            heapq.heappush(heap, (lst[0], list_idx, 0))

    while heap:
        value, list_idx, elem_idx = heapq.heappop(heap)
        result.append(value)
        next_idx = elem_idx + 1
        if next_idx < len(seq[list_idx]):
            heapq.heappush(heap, (seq[list_idx][next_idx], list_idx, next_idx))

    return result
