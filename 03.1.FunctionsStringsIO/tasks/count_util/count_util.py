def count_util(text: str, flags: str | None = None) -> dict[str, int]:
    """
    :param text: text to count entities
    :param flags: flags in command-like format - can be:
        * -m stands for counting characters
        * -l stands for counting lines
        * -L stands for getting length of the longest line
        * -w stands for counting words
    More than one flag can be passed at the same time, for example:
        * "-l -m"
        * "-lLw"
    Ommiting flags or passing empty string is equivalent to "-mlLw"
    :return: mapping from string keys to corresponding counter, where
    keys are selected according to the received flags:
        * "chars" - amount of characters
        * "lines" - amount of lines
        * "longest_line" - the longest line length
        * "words" - amount of words
    """
    result: dict[str, int] = {}

    all_flags = {'m', 'l', 'L', 'w'}
    active_flags = set()

    if flags is None or flags == "":
        active_flags = all_flags
    else:
        for part in flags.split():
            if part.startswith('-'):
                for c in part[1:]:
                    if c in all_flags:
                        active_flags.add(c)

    if 'm' in active_flags:
        result['chars'] = len(text)

    if 'l' in active_flags:
        result['lines'] = text.count('\n')

    if 'L' in active_flags:
        lines = text.split('\n')
        if text:
            result['longest_line'] = max(len(line) for line in lines) if lines else 0
        else:
            result['longest_line'] = 0

    if 'w' in active_flags:
        result['words'] = len(text.split())

    return result
