from abc import abstractmethod, ABC
import typing as tp
import re
import math
import json
from datetime import datetime

TRow = dict[str, tp.Any]
TRowsIterable = tp.Iterable[TRow]
TRowsGenerator = tp.Generator[TRow, None, None]


class Operation(ABC):
    @abstractmethod
    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        pass


class Read(Operation):
    def __init__(self, filename: str, parser: tp.Callable[[str], TRow]) -> None:
        self._filename = filename
        self._parser = parser

    def __call__(self, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        with open(self._filename) as f:
            for line in f:
                yield self._parser(line)


class ReadIterFactory(Operation):
    def __init__(self, name: str) -> None:
        self._name = name

    def __call__(self, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        for row in kwargs[self._name]():
            yield row


class Mapper(ABC):
    """Base class for mappers"""
    @abstractmethod
    def __call__(self, row: TRow) -> TRowsGenerator:
        """
        :param row: one table row
        """
        pass


class Map(Operation):
    def __init__(self, mapper: Mapper) -> None:
        self._mapper = mapper

    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        for row in rows:
            yield from self._mapper(row)


class Reducer(ABC):
    """Base class for reducers"""
    @abstractmethod
    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        """
        :param rows: table rows
        """
        pass


class Reduce(Operation):
    def __init__(self, reducer: Reducer, keys: tp.Sequence[str]) -> None:
        self._reducer = reducer
        self._keys = keys

    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        from itertools import groupby

        def key_func(row: TRow) -> tuple:
            return tuple(row[k] for k in self._keys)

        for key, group in groupby(rows, key=key_func):
            yield from self._reducer(key, group)


class Joiner(ABC):
    """Base class for joiners"""
    def __init__(self, suffix_a: str = '_1', suffix_b: str = '_2') -> None:
        self._a_suffix = suffix_a
        self._b_suffix = suffix_b

    @abstractmethod
    def __call__(self, keys: tp.Sequence[str], rows_a: TRowsIterable, rows_b: TRowsIterable) -> TRowsGenerator:
        """
        :param keys: join keys
        :param rows_a: left table rows
        :param rows_b: right table rows
        """
        pass


class Join(Operation):
    def __init__(self, joiner: Joiner, keys: tp.Sequence[str]):
        self._keys = keys
        self._joiner = joiner

    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:

        # Extract first stream and second stream from kwargs
        stream_a = rows
        stream_b = kwargs['stream_b']

        # Convert to lists to support multiple passes
        list_a = list(stream_a)
        list_b = list(stream_b)

        # Create index for stream_b
        index = {}
        for row in list_b:
            key = tuple(row[k] for k in self._keys)
            if key not in index:
                index[key] = []
            index[key].append(row)

        # Join
        for row_a in list_a:
            key = tuple(row_a[k] for k in self._keys)
            if key in index:
                for row_b in index[key]:
                    new_row = dict(row_a)
                    new_row.update(row_b)
                    yield new_row


class DummyMapper(Mapper):
    """Yield exactly the row passed"""
    def __call__(self, row: TRow) -> TRowsGenerator:
        yield row


class FirstReducer(Reducer):
    """Yield only first row from passed ones"""
    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        for row in rows:
            yield row
            break


class FilterPunctuation(Mapper):
    """Left only non-punctuation symbols"""
    def __init__(self, column: str):
        """
        :param column: name of column to process
        """
        self._column = column

    def __call__(self, row: TRow) -> TRowsGenerator:
        new_row = dict(row)
        new_row[self._column] = re.sub(r'[^\w\s]', '', new_row[self._column])
        yield new_row


class LowerCase(Mapper):
    """Replace column value with value in lower case"""
    def __init__(self, column: str):
        """
        :param column: name of column to process
        """
        self._column = column

    def __call__(self, row: TRow) -> TRowsGenerator:
        new_row = dict(row)
        new_row[self._column] = new_row[self._column].lower()
        yield new_row


class Split(Mapper):
    """Split row on multiple rows by separator"""
    def __init__(self, column: str, separator: str | None = None) -> None:
        """
        :param column: name of column to split
        :param separator: string to separate by
        """
        self._column = column
        self._separator = separator

    def __call__(self, row: TRow) -> TRowsGenerator:
        for word in row[self._column].split():
            new_row = dict(row)
            new_row[self._column] = word
            yield new_row


class Product(Mapper):
    """Calculates product of multiple columns"""
    def __init__(self, columns: tp.Sequence[str], result_column: str = 'product') -> None:
        """
        :param columns: column names to product
        :param result_column: column name to save product in
        """
        self._columns = columns
        self._result_column = result_column

    def __call__(self, row: TRow) -> TRowsGenerator:
        new_row = dict(row)
        product = 1
        for col in self._columns:
            product *= row[col]
        new_row[self._result_column] = product
        yield new_row


class Filter(Mapper):
    """Remove records that don't satisfy some condition"""
    def __init__(self, condition: tp.Callable[[TRow], bool]) -> None:
        """
        :param condition: if condition is not true - remove record
        """
        self._condition = condition

    def __call__(self, row: TRow) -> TRowsGenerator:
        if self._condition(row):
            yield row


class Project(Mapper):
    """Leave only mentioned columns"""
    def __init__(self, columns: tp.Sequence[str]) -> None:
        """
        :param columns: names of columns
        """
        self._columns = columns

    def __call__(self, row: TRow) -> TRowsGenerator:
        new_row = {}
        for col in self._columns:
            if col in row:
                new_row[col] = row[col]
        yield new_row


class TopN(Reducer):
    """Calculate top N by value"""
    def __init__(self, column: str, n: int) -> None:
        """
        :param column: column name to get top by
        :param n: number of top values to extract
        """
        self._column_max = column
        self._n = n

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        rows_list = list(rows)
        rows_list.sort(key=lambda x: x[self._column_max], reverse=True)
        for row in rows_list[:self._n]:
            yield row


class TermFrequency(Reducer):
    """Calculate frequency of values in column"""
    def __init__(self, words_column: str, result_column: str = 'tf') -> None:
        """
        :param words_column: name for column with words
        :param result_column: name for result column
        """
        self._words_column = words_column
        self._result_column = result_column

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        rows_list = list(rows)
        total = len(rows_list)
        counts = {}
        for row in rows_list:
            word = row[self._words_column]
            counts[word] = counts.get(word, 0) + 1

        for word, count in counts.items():
            yield {rows_list[0]['doc_id']: rows_list[0]['doc_id'], 'text': word, self._result_column: count / total}


class Count(Reducer):
    """
    Count records by key
    Example for group_key=('a',) and column='d'
        {'a': 1, 'b': 5, 'c': 2}
        {'a': 1, 'b': 6, 'c': 1}
        =>
        {'a': 1, 'd': 2}
    """
    def __init__(self, column: str) -> None:
        """
        :param column: name for result column
        """
        self._column = column

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        count = 0
        first_row = None
        for row in rows:
            if first_row is None:
                first_row = dict(row)
            count += 1

        if first_row is not None:
            first_row[self._column] = count
            yield first_row


class Sum(Reducer):
    """
    Sum values aggregated by key
    Example for key=('a',) and column='b'
        {'a': 1, 'b': 2, 'c': 4}
        {'a': 1, 'b': 3, 'c': 5}
        =>
        {'a': 1, 'b': 5}
    """
    def __init__(self, column: str) -> None:
        """
        :param column: name for sum column
        """
        self._column = column

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        total = 0
        first_row = None
        for row in rows:
            if first_row is None:
                first_row = dict(row)
            total += row[self._column]

        if first_row is not None:
            first_row[self._column] = total
            yield first_row


class InnerJoiner(Joiner):
    """Join with inner strategy"""
    def __call__(self, keys: tp.Sequence[str], rows_a: TRowsIterable, rows_b: TRowsIterable) -> TRowsGenerator:
        hash_map = {}
        for row in rows_b:
            key = tuple(row[k] for k in keys)
            if key not in hash_map:
                hash_map[key] = []
            hash_map[key].append(row)

        for row in rows_a:
            key = tuple(row[k] for k in keys)
            if key in hash_map:
                for r2 in hash_map[key]:
                    new_row = dict(row)
                    new_row.update(r2)
                    yield new_row


class OuterJoiner(Joiner):
    """Join with outer strategy"""
    def __call__(self, keys: tp.Sequence[str], rows_a: TRowsIterable, rows_b: TRowsIterable) -> TRowsGenerator:
        hash_map = {}
        used_keys = set()

        for row in rows_b:
            key = tuple(row[k] for k in keys)
            if key not in hash_map:
                hash_map[key] = []
            hash_map[key].append(row)

        for row in rows_a:
            key = tuple(row[k] for k in keys)
            if key in hash_map:
                used_keys.add(key)
                for r2 in hash_map[key]:
                    new_row = dict(row)
                    new_row.update(r2)
                    yield new_row
            else:
                yield row

        for key, rows in hash_map.items():
            if key not in used_keys:
                for r2 in rows:
                    yield r2


class LeftJoiner(Joiner):
    """Join with left strategy"""
    def __call__(self, keys: tp.Sequence[str], rows_a: TRowsIterable, rows_b: TRowsIterable) -> TRowsGenerator:
        hash_map = {}
        for row in rows_b:
            key = tuple(row[k] for k in keys)
            if key not in hash_map:
                hash_map[key] = []
            hash_map[key].append(row)

        for row in rows_a:
            key = tuple(row[k] for k in keys)
            if key in hash_map:
                for r2 in hash_map[key]:
                    new_row = dict(row)
                    new_row.update(r2)
                    yield new_row
            else:
                yield row


class RightJoiner(Joiner):
    """Join with right strategy"""
    def __call__(self, keys: tp.Sequence[str], rows_a: TRowsIterable, rows_b: TRowsIterable) -> TRowsGenerator:
        hash_map = {}
        for row in rows_a:
            key = tuple(row[k] for k in keys)
            if key not in hash_map:
                hash_map[key] = []
            hash_map[key].append(row)

        for row in rows_b:
            key = tuple(row[k] for k in keys)
            if key in hash_map:
                for r1 in hash_map[key]:
                    new_row = dict(r1)
                    new_row.update(row)
                    yield new_row
            else:
                yield row


# Additional operations
class FilterByLength(Mapper):
    """Filter by minimum length"""
    def __init__(self, column: str, min_len: int):
        self.column = column
        self.min_len = min_len

    def __call__(self, row: TRow) -> TRowsGenerator:
        if len(row[self.column]) >= self.min_len:
            yield row


class CalculateIdf(Mapper):
    """Calculate IDF"""
    def __init__(self):
        pass

    def __call__(self, row: TRow) -> TRowsGenerator:
        new_row = dict(row)
        new_row['idf'] = math.log(new_row['total_docs'] / new_row['doc_count'])
        yield new_row


class CalculateTfIdf(Mapper):
    """Calculate TF-IDF"""
    def __init__(self):
        pass

    def __call__(self, row: TRow) -> TRowsGenerator:
        new_row = dict(row)
        new_row['tfidf'] = new_row['tf'] * new_row['idf']
        yield new_row


class CalculatePmi(Mapper):
    """Calculate PMI"""
    def __init__(self):
        pass

    def __call__(self, row: TRow) -> TRowsGenerator:
        new_row = dict(row)
        new_row['pmi'] = math.log(new_row['doc_count'] / new_row['total_count'])
        yield new_row


class CountFilterMin(Reducer):
    """Count with minimum filter"""
    def __init__(self, column: str, min_count: int):
        self.column = column
        self.min_count = min_count

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        count = 0
        first_row = None
        for row in rows:
            if first_row is None:
                first_row = dict(row)
            count += 1

        if count >= self.min_count and first_row is not None:
            first_row[self.column] = count
            yield first_row


class ExtractTimeFeatures(Mapper):
    """Extract time features"""
    def __init__(self, column: str):
        self.column = column

    def __call__(self, row: TRow) -> TRowsGenerator:
        dt = datetime.strptime(row[self.column], '%Y%m%dT%H%M%S.%f')
        new_row = dict(row)
        new_row['weekday'] = dt.strftime('%a')
        new_row['hour'] = dt.hour
        yield new_row


class CalculateDuration(Mapper):
    """Calculate duration"""
    def __init__(self):
        pass

    def __call__(self, row: TRow) -> TRowsGenerator:
        enter = datetime.strptime(row['enter_time'], '%Y%m%dT%H%M%S.%f')
        leave = datetime.strptime(row['leave_time'], '%Y%m%dT%H%M%S.%f')
        new_row = dict(row)
        new_row['duration'] = (leave - enter).total_seconds()
        yield new_row


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculate distance between two points"""
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return 6373 * c


class CalculateDistance(Mapper):
    """Calculate distance"""
    def __init__(self):
        pass

    def __call__(self, row: TRow) -> TRowsGenerator:
        lon1, lat1 = row['start']
        lon2, lat2 = row['end']
        new_row = dict(row)
        new_row['distance'] = haversine(lon1, lat1, lon2, lat2)
        yield new_row


class CalculateSpeed(Mapper):
    """Calculate speed"""
    def __init__(self):
        pass

    def __call__(self, row: TRow) -> TRowsGenerator:
        new_row = dict(row)
        if new_row['duration'] > 0:
            new_row['speed'] = new_row['distance'] / (new_row['duration'] / 3600.0)
            yield new_row


class AverageSpeed(Reducer):
    """Calculate average speed"""
    def __init__(self):
        pass

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        total_speed = 0.0
        count = 0
        first_row = None
        for row in rows:
            if first_row is None:
                first_row = dict(row)
            if 'speed' in row and row['speed'] is not None:
                total_speed += row['speed']
                count += 1

        if count > 0 and first_row is not None:
            first_row['speed'] = total_speed / count
            yield {'weekday': first_row['weekday'], 'hour': first_row['hour'], 'speed': first_row['speed']}


def read_from_file(filename: str) -> TRowsIterable:
    """Read from file"""
    with open(filename, 'r') as f:
        for line in f:
            yield json.loads(line.strip())
