def filter_list_by_list(lst_a: list[int] | range, lst_b: list[int] | range) -> list[int]:
    """
    Filter first sorted list by other sorted list
    :param lst_a: first sorted list
    :param lst_b: second sorted list
    :return: filtered sorted list
    """
    result = []
    i, j = 0, 0
    while i < len(lst_a):
        while j < len(lst_b) and lst_b[j] < lst_a[i]:
            j += 1
        if j >= len(lst_b) or lst_b[j] != lst_a[i]:
            result.append(lst_a[i])
        i += 1
    return result
