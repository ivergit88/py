import typing as tp

from . import operations as ops


class Graph:
    """Computational graph implementation"""

    def __init__(self, source: tp.Optional['Graph'] = None):
        self._source = source
        self._operations = []

    @staticmethod
    def graph_from_iter(name: str) -> 'Graph':
        """Construct new graph which reads data from row iterator (in form of sequence of Rows
        from 'kwargs' passed to 'run' method) into graph data-flow
        Use ops.ReadIterFactory
        :param name: name of kwarg to use as data source
        """
        graph = Graph()
        graph._operations.append(('iter_factory', name))
        return graph

    @staticmethod
    def graph_from_file(filename: str, parser: tp.Callable[[str], ops.TRow]) -> 'Graph':
        """Construct new graph extended with operation for reading rows from file
        Use ops.Read
        :param filename: filename to read from
        :param parser: parser from string to Row
        """
        graph = Graph()
        graph._operations.append(('read', filename, parser))
        return graph

    def map(self, mapper: ops.Mapper) -> 'Graph':
        """Construct new graph extended with map operation with particular mapper
        :param mapper: mapper to use
        """
        new_graph = Graph(self)
        new_graph._operations.append(('map', mapper))
        return new_graph

    def reduce(self, reducer: ops.Reducer, keys: tp.Sequence[str]) -> 'Graph':
        """Construct new graph extended with reduce operation with particular reducer
        :param reducer: reducer to use
        :param keys: keys for grouping
        """
        new_graph = Graph(self)
        new_graph._operations.append(('reduce', reducer, keys))
        return new_graph

    def sort(self, keys: tp.Sequence[str]) -> 'Graph':
        """Construct new graph extended with sort operation
        :param keys: sorting keys (typical is tuple of strings)
        """
        new_graph = Graph(self)
        new_graph._operations.append(('sort', keys))
        return new_graph

    def join(self, joiner: ops.Joiner, join_graph: 'Graph', keys: tp.Sequence[str]) -> 'Graph':
        """Construct new graph extended with join operation with another graph
        :param joiner: join strategy to use
        :param join_graph: other graph to join with
        :param keys: keys for grouping
        """
        new_graph = Graph(self)
        new_graph._operations.append(('join', joiner, join_graph, keys))
        return new_graph

    def run(self, **kwargs: tp.Any) -> ops.TRowsIterable:
        """Single method to start execution; data sources passed as kwargs"""
        result = None

        for op in self._operations:
            op_type = op[0]

            if op_type == 'iter_factory':
                name = op[1]
                result = kwargs[name]()

            elif op_type == 'read':
                filename, parser = op[1], op[2]
                result = ops.Read(filename, parser)()

            elif op_type == 'map':
                mapper = op[1]
                result = ops.Map(mapper)(result, **kwargs)

            elif op_type == 'reduce':
                reducer, keys = op[1], op[2]
                result = ops.Reduce(reducer, keys)(result, **kwargs)

            elif op_type == 'sort':
                keys = op[1]
                # Simple sort implementation
                result = sorted(result, key=lambda x: tuple(x[k] for k in keys))

            elif op_type == 'join':
                joiner, join_graph, keys = op[1], op[2], op[3]
                # Get stream_b from join_graph
                stream_b = join_graph.run(**kwargs)
                result = ops.Join(joiner, keys)(result, stream_b=stream_b, **kwargs)

        return result
