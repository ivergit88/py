import heapq


def merge(lst: list[list[int]]) -> list[int]:
    """
    Merge k sorted lists into one sorted list
    :param lst: list of sorted lists
    :return: merged sorted list
    """
    heap = []
    result = []

    for i, current_list in enumerate(lst):
        if current_list:
            heapq.heappush(heap, (current_list[0], i, 0))

    while heap:
        val, list_idx, elem_idx = heapq.heappop(heap)
        result.append(val)

        if elem_idx + 1 < len(lst[list_idx]):
            heapq.heappush(heap, (lst[list_idx][elem_idx + 1], list_idx, elem_idx + 1))

    return result
