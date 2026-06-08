def get_common_type(type1: type, type2: type) -> type:
    """
    Calculate common type according to rule, that it must have the most adequate interpretation after conversion.
    Look in tests for adequacy calibration.
    :param type1: one of [bool, int, float, complex, list, range, tuple, str] types
    :param type2: one of [bool, int, float, complex, list, range, tuple, str] types
    :return: the most concrete common type, which can be used to convert both input values
    """
    numeric_hierarchy = {bool: 0, int: 1, float: 2, complex: 3}
    sequence_types = {list, tuple, range}

    if type1 is type2:
        if type1 is range:
            return tuple
        return type1

    if type1 in numeric_hierarchy and type2 in numeric_hierarchy:
        return [bool, int, float, complex][max(numeric_hierarchy[type1], numeric_hierarchy[type2])]

    if type1 is str or type2 is str:
        return str

    if type1 in sequence_types and type2 in sequence_types:
        if type1 is list or type2 is list:
            return list
        if (type1 is tuple and type2 is range) or (type1 is range and type2 is tuple):
            return tuple
        return tuple

    return str

