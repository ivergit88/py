import typing as tp


def convert_to_common_type(data: list[tp.Any]) -> list[tp.Any]:
    """
    Takes list of multiple types' elements and convert each element to common type according to given rules
    :param data: list of multiple types' elements
    :return: list with elements converted to common type
    """
    if not data:
        return []

    def is_no_info(val):
        return val is None or (isinstance(val, str) and val == "")

    non_empty = [x for x in data if not is_no_info(x)]

    if not non_empty:
        return ["" for _ in data]

    has_list_or_tuple = any(isinstance(x, (list, tuple)) for x in non_empty)
    has_bool = any(isinstance(x, bool) for x in non_empty)
    has_int = any(isinstance(x, int) and not isinstance(x, bool) for x in non_empty)
    has_float = any(isinstance(x, float) for x in non_empty)

    if has_list_or_tuple:
        result = []
        for val in data:
            if is_no_info(val):
                result.append([])
            elif isinstance(val, tuple):
                result.append(list(val))
            elif isinstance(val, list):
                result.append(val)
            else:
                result.append([val])
        return result

    if has_bool:
        result = []
        for val in data:
            if is_no_info(val):
                result.append(False)
            elif isinstance(val, bool):
                result.append(val)
            else:
                result.append(bool(val))
        return result

    if has_float:
        result = []
        for val in data:
            if is_no_info(val):
                result.append(0.0)
            else:
                result.append(float(val))
        return result

    if has_int:
        result = []
        for val in data:
            if is_no_info(val):
                result.append(0)
            else:
                result.append(int(val))
        return result

    result = []
    for val in data:
        if is_no_info(val):
            result.append("")
        else:
            result.append(str(val))
    return result
