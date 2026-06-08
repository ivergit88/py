import copy
import heapq
import re
import string
import sys
from abc import abstractmethod, ABC
import typing as tp
from itertools import groupby

TRow = dict[str, tp.Any]
TRowsIterable = tp.Iterable[TRow]
TRowsGenerator = tp.Generator[TRow, None, None]

class Operation(ABC):
    @abstractmethod
    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        pass

class Read(Operation):
    def __init__(self, file_path: str, parser_func: tp.Callable[[str], TRow]) -> None:
        self.file_path = file_path
        self.parser_func = parser_func

    def __call__(self, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        with open(self.file_path) as file_obj:
            for line in file_obj:
                yield self.parser_func(line)

class ReadIterFactory(Operation):
    def __init__(self, source_name: str) -> None:
        self.source_name = source_name

    def __call__(self, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        for record in kwargs[self.source_name]:
            yield record

class Mapper(ABC):
    @abstractmethod
    def __call__(self, row: TRow) -> TRowsGenerator:
        pass

class Map(Operation):
    def __init__(self, mapper_instance: Mapper) -> None:
        self.mapper_instance = mapper_instance

    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        for record in rows:
            yield from self.mapper_instance(record)

class Reducer(ABC):
    @abstractmethod
    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        pass

class Reduce(Operation):
    def __init__(self, reducer_instance: Reducer, key_fields: tp.Sequence[str]) -> None:
        self.reducer_instance = reducer_instance
        self.key_fields = key_fields

    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        primary_key: str = self.key_fields[0]
        for key_val, grouped_data in groupby(rows, key=lambda r: r[primary_key]):
            yield from self.reducer_instance(tuple(self.key_fields), grouped_data)

class Joiner(ABC):
    def __init__(self, suffix_left: str = '_1', suffix_right: str = '_2') -> None:
        self._left_suffix = suffix_left
        self._right_suffix = suffix_right

    @abstractmethod
    def __call__(self, keys: tp.Sequence[str], rows_left: TRowsIterable, rows_right: TRowsIterable) -> TRowsGenerator:
        pass

class Join(Operation):
    def __init__(self, joiner_instance: Joiner, key_fields: tp.Sequence[str]):
        self.key_fields = key_fields
        self.joiner_instance = joiner_instance

    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        primary_key: str = self.key_fields[0]
        is_left_exhausted: bool = False
        is_right_exhausted: bool = False

        left_iter = groupby(rows, key=lambda r: r[primary_key])
        right_iter = groupby(args[0], key=lambda r: r[primary_key])

        left_key, left_group = next(left_iter)
        right_key, right_group = next(right_iter)

        while not is_left_exhausted or not is_right_exhausted:
            if right_key > left_key:
                if not isinstance(self.joiner_instance, InnerJoiner) and not isinstance(self.joiner_instance, RightJoiner):
                    yield from self.joiner_instance(self.key_fields, left_group, iter({}))
                try:
                    left_key, left_group = next(left_iter)
                except StopIteration:
                    is_left_exhausted = True
                    left_key = sys.maxsize
                else:
                    continue
            elif right_key < left_key:
                if not isinstance(self.joiner_instance, InnerJoiner) and not isinstance(self.joiner_instance, LeftJoiner):
                    yield from self.joiner_instance(self.key_fields, iter({}), right_group)
                try:
                    right_key, right_group = next(right_iter)
                except StopIteration:
                    is_right_exhausted = True
                    right_key = sys.maxsize
                else:
                    continue
            elif right_key == left_key:
                yield from self.joiner_instance(self.key_fields, left_group, right_group)
                try:
                    left_key, left_group = next(left_iter)
                except StopIteration:
                    is_left_exhausted = True
                    left_key = sys.maxsize
                try:
                    right_key, right_group = next(right_iter)
                except StopIteration:
                    break
                else:
                    continue
            else:
                try:
                    right_key, right_group = next(right_iter)
                except StopIteration:
                    is_right_exhausted = True
                    right_key = sys.maxsize
                else:
                    continue

class DummyMapper(Mapper):
    def __call__(self, row: TRow) -> TRowsGenerator:
        yield row

class FirstReducer(Reducer):
    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        for record in rows:
            yield record
            break

class FilterPunctuation(Mapper):
    def __init__(self, target_col: str):
        self.target_col = target_col

    def __call__(self, row: TRow) -> TRowsGenerator:
        row[self.target_col] = row[self.target_col].translate(str.maketrans('', '', string.punctuation))
        yield row

class LowerCase(Mapper):
    def __init__(self, target_col: str):
        self.target_col = target_col

    @staticmethod
    def _to_lower(text: str) -> str:
        return text.lower()

    def __call__(self, row: TRow) -> TRowsGenerator:
        row[self.target_col] = self._to_lower(row[self.target_col])
        yield row

class Split(Mapper):
    def __init__(self, target_col: str, delimiter: str | None = None) -> None:
        self.target_col = target_col
        self.delimiter = delimiter

    def __call__(self, row: TRow) -> TRowsGenerator:
        pattern_str: str = ''
        if self.delimiter is not None:
            pattern_str = self.delimiter + '+'
        else:
            pattern_str = r'\s+'

        regex_obj = re.compile(pattern_str)
        prev_end_idx: int = 0

        for match in re.finditer(regex_obj, row[self.target_col]):
            new_row = copy.deepcopy(row)
            new_row.update({self.target_col: row[self.target_col][prev_end_idx:match.start()]})
            prev_end_idx = match.end()
            yield new_row

        if len(row[self.target_col]) != prev_end_idx:
            new_row = copy.deepcopy(row)
            new_row.update({self.target_col: row[self.target_col][prev_end_idx:len(row[self.target_col])]})
            yield new_row

class Product(Mapper):
    def __init__(self, factor_cols: tp.Sequence[str], result_col: str = 'product') -> None:
        self.factor_cols = factor_cols
        self.result_col = result_col

    def __call__(self, row: TRow) -> TRowsGenerator:
        new_row = copy.deepcopy(row)
        product_val: float = 1
        for col_name in self.factor_cols:
            product_val = product_val * new_row[col_name]
        new_row[self.result_col] = product_val
        yield new_row

class Filter(Mapper):
    def __init__(self, condition_func: tp.Callable[[TRow], bool]) -> None:
        self.condition_func = condition_func

    def __call__(self, row: TRow) -> TRowsGenerator:
        if self.condition_func(row):
            yield row

class Project(Mapper):
    def __init__(self, keep_cols: tp.Sequence[str]) -> None:
        self.keep_cols = keep_cols

    def __call__(self, row: TRow) -> TRowsGenerator:
        new_row = copy.deepcopy(row)
        for key_name in row.keys():
            if key_name not in self.keep_cols:
                new_row.pop(key_name)
        yield new_row

class TopN(Reducer):
    def __init__(self, sort_col: str, count: int) -> None:
        self.sort_col = sort_col
        self.count = count

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        sorted_data = heapq.nlargest(self.count, rows, key=lambda r: r[self.sort_col])
        for i in range(self.count):
            yield sorted_data[len(list(rows)) - i - 1]

class TermFrequency(Reducer):
    def __init__(self, word_col: str, result_col: str = 'tf') -> None:
        self.word_col = word_col
        self.result_col = result_col

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        word_counts: dict[str, int] = dict()
        total_words: int = 0
        group_key_vals: dict[str, tp.Any] = {}
        is_first: bool = True

        for record in rows:
            if is_first:
                for k in group_key:
                    group_key_vals[k] = record[k]
                is_first = False

            current_word = record[self.word_col]
            if current_word not in word_counts:
                word_counts[current_word] = 1
            else:
                word_counts[current_word] += 1
            total_words += 1

        for word, cnt in word_counts.items():
            res_row = {self.word_col: word, self.result_col: cnt / total_words}
            res_row.update(group_key_vals)
            yield res_row

class Count(Reducer):
    def __init__(self, target_col: str) -> None:
        self.target_col = target_col

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        total_cnt: int = 0
        res_row: dict[str, tp.Any] = {}
        is_first: bool = True

        for record in rows:
            if is_first:
                for k in group_key:
                    res_row[k] = record[k]
                is_first = False
            total_cnt += 1
            res_row.update({self.target_col: total_cnt})
        yield res_row

class Sum(Reducer):
    def __init__(self, target_col: str) -> None:
        self.target_col = target_col

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        total_sum: int = 0
        res_row: TRow = {}
        is_first: bool = True

        for record in rows:
            total_sum += record[self.target_col]
            if is_first:
                for i in range(len(group_key)):
                    res_row.update({group_key[i]: record[group_key[i]]})
                is_first = False
            res_row.update({self.target_col: total_sum})
        yield res_row

class InnerJoiner(Joiner):
    def __call__(self, keys: tp.Sequence[str], rows_left: TRowsIterable, rows_right: TRowsIterable) -> TRowsGenerator:
        left_list = list(rows_left)
        left_keys = left_list[0].keys()
        common_keys: list[str] = list()
        is_first: bool = True

        for right_rec in rows_right:
            if is_first:
                for k in right_rec.keys():
                    if k in left_keys and k not in keys:
                        common_keys.append(k)
                is_first = False

            for i in range(len(left_list)):
                for ck in common_keys:
                    left_list[i].update({ck + self._left_suffix: left_list[i][ck]})
                    del left_list[i][ck]

            for left_rec in left_list:
                new_right_rec = copy.deepcopy(right_rec)
                for ck in common_keys:
                    new_right_rec.update({ck + self._right_suffix: new_right_rec[ck]})
                    del new_right_rec[ck]
                new_right_rec.update(left_rec)
                yield new_right_rec

class OuterJoiner(Joiner):
    def __call__(self, keys: tp.Sequence[str], rows_left: TRowsIterable, rows_right: TRowsIterable) -> TRowsGenerator:
        right_list = list(rows_right)
        matched: bool = True

        for left_rec in rows_left:
            matched = False
            if len(right_list) == 0:
                yield left_rec
                continue
            for right_rec in right_list:
                left_rec.update(right_rec)
                yield left_rec

        if matched:
            for el in right_list:
                yield el

class LeftJoiner(Joiner):
    def __call__(self, keys: tp.Sequence[str], rows_left: TRowsIterable, rows_right: TRowsIterable) -> TRowsGenerator:
        right_list = list(rows_right)
        for left_rec in rows_left:
            if len(right_list) == 0:
                yield left_rec
                continue
            for right_rec in right_list:
                new_left = copy.deepcopy(left_rec)
                new_left.update(right_rec)
                yield new_left

class RightJoiner(Joiner):
    def __call__(self, keys: tp.Sequence[str], rows_left: TRowsIterable, rows_right: TRowsIterable) -> TRowsGenerator:
        left_list = list(rows_left)
        for right_rec in rows_right:
            if len(left_list) == 0:
                yield right_rec
                continue
            for left_rec in left_list:
                new_right = copy.deepcopy(right_rec)
                new_right.update(left_rec)
                yield new_right
