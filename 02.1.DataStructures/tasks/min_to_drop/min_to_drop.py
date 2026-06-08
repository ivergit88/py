import typing as tp


def get_min_to_drop(seq: tp.Sequence[tp.Any]) -> int:
    """
    :param seq: sequence of elements
    :return: number of elements need to drop to leave equal elements
    """
    from collections import Counter
    if not seq:
        return 0
    counts = Counter(seq)
    max_count = max(counts.values())
    return len(seq) - max_count

