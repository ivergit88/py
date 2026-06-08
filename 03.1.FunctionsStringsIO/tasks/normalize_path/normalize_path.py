def normalize_path(path: str) -> str:
    """
    :param path: unix path to normalize
    :return: normalized path
    """
    parts = path.split('/')
    result: list[str] = []

    is_absolute = path.startswith('/')

    for part in parts:
        if part == '' or part == '.':
            continue
        elif part == '..':
            if result and result[-1] != '..':
                result.pop()
            elif not is_absolute:
                result.append('..')
        else:
            result.append(part)

    if is_absolute:
        return '/' + '/'.join(result)
    elif not result:
        return '.'
    else:
        return '/'.join(result)
