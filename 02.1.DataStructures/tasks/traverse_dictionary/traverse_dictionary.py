from collections.abc import Mapping
import typing as tp


def traverse_dictionary_immutable(
        dct: tp.Mapping[str, tp.Any],
        prefix: str = "") -> list[tuple[str, int]]:
    """
    :param dct: dictionary of undefined depth with integers or other dicts as leaves with same properties
    :param prefix: prefix for key used for passing total path through recursion
    :return: list with pairs: (full key from root to leaf joined by ".", value)
    """
    result: list[tuple[str, int]] = []

    def _recruit(current_dct: tp.Mapping[str, tp.Any], path_parts: list[str]) -> None:
        for key, value in current_dct.items():
            path_parts.append(key)
            if isinstance(value, Mapping):
                _recruit(value, path_parts)
            else:
                result.append((".".join(path_parts), value))
            path_parts.pop()

    initial_path = prefix.split(".") if prefix else []
    _recruit(dct, initial_path)
    return result


def traverse_dictionary_mutable(
        dct: tp.Mapping[str, tp.Any],
        result: list[tuple[str, int]],
        prefix: str = "") -> None:
    """
    :param dct: dictionary of undefined depth with integers or other dicts as leaves with same properties
    :param result: list with pairs: (full key from root to leaf joined by ".", value)
    :param prefix: prefix for key used for passing total path through recursion
    :return: None
    """
    def _recruit(current_dct: tp.Mapping[str, tp.Any], path_parts: list[str]) -> None:
        for key, value in current_dct.items():
            path_parts.append(key)
            if isinstance(value, Mapping):
                _recruit(value, path_parts)
            else:
                result.append((".".join(path_parts), value))
            path_parts.pop()

    initial_path = prefix.split(".") if prefix else []
    _recruit(dct, initial_path)


def traverse_dictionary_iterative(
        dct: tp.Mapping[str, tp.Any]
        ) -> list[tuple[str, int]]:
    """
    :param dct: dictionary of undefined depth with integers or other dicts as leaves with same properties
    :return: list with pairs: (full key from root to leaf joined by ".", value)
    """
    result: list[tuple[str, int]] = []
    if not dct:
        return result

    # Стек хранит: [итератор, ключ_этого_уровня]
    # Используем список для пути, чтобы не копировать строки
    stack: list[tp.Iterator[tuple[str, tp.Any]]] = [iter(dct.items())]
    path_stack: list[str] = []

    while stack:
        try:
            key, value = next(stack[-1])
            if isinstance(value, Mapping):
                path_stack.append(key)
                stack.append(iter(value.items()))
            else:
                current_path = ".".join(path_stack + [key])
                result.append((current_path, value))
        except StopIteration:
            stack.pop()
            if path_stack:
                path_stack.pop()

    return result
