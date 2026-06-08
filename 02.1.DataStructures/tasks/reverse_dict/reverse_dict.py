import typing as tp


def revert(dct: tp.Mapping[str, str]) -> dict[str, list[str]]:
    """
    :param dct: dictionary to revert in format {key: value}
    :return: reverted dictionary {value: [key1, key2, key3]}
    """
    from collections import defaultdict
    result = defaultdict(list)
    for key, value in dct.items():
        result[value].append(key)
    return dict(result)
