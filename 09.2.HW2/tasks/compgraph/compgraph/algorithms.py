from . import Graph, operations


def word_count_graph(input_stream_name: str, text_column: str = 'text', count_column: str = 'count') -> Graph:
    """Constructs graph which counts words in text_column of all rows passed"""
    return Graph.graph_from_iter(input_stream_name) \
        .map(operations.FilterPunctuation(text_column)) \
        .map(operations.LowerCase(text_column)) \
        .map(operations.Split(text_column)) \
        .sort([text_column]) \
        .reduce(operations.Count(count_column), [text_column]) \
        .sort([count_column, text_column])


def inverted_index_graph(input_stream_name: str, doc_column: str = 'doc_id', text_column: str = 'text',
                         result_column: str = 'tf_idf') -> Graph:
    """Constructs graph which calculates td-idf for every word/document pair"""
    split_word = Graph.graph_from_iter(input_stream_name) \
        .map(operations.FilterPunctuation(text_column)) \
        .map(operations.LowerCase(text_column)) \
        .map(operations.Split(text_column))

    count_docs = Graph.graph_from_iter(input_stream_name) \
        .reduce(operations.Count('total_docs'), [])

    count_idf = split_word \
        .sort([doc_column, text_column]) \
        .reduce(operations.FirstReducer(), [doc_column, text_column]) \
        .sort([text_column]) \
        .reduce(operations.Count('doc_count'), [text_column]) \
        .join(operations.InnerJoiner(), count_docs, [], []) \
        .map(operations.CalculateIdf())

    tf = split_word \
        .sort([doc_column]) \
        .reduce(operations.TermFrequency(text_column, 'tf'), [doc_column])

    return tf \
        .join(operations.InnerJoiner(), count_idf, [text_column], [text_column]) \
        .map(operations.CalculateTfIdf()) \
        .sort([text_column]) \
        .reduce(operations.TopN('tfidf', 3), [text_column])


def pmi_graph(input_stream_name: str, doc_column: str = 'doc_id', text_column: str = 'text',
              result_column: str = 'pmi') -> Graph:
    """Constructs graph which gives for every document the top 10 words ranked by pointwise mutual information"""
    split_word = Graph.graph_from_iter(input_stream_name) \
        .map(operations.FilterPunctuation(text_column)) \
        .map(operations.LowerCase(text_column)) \
        .map(operations.Split(text_column)) \
        .map(operations.FilterByLength(text_column, 4))

    count_total = split_word \
        .sort([text_column]) \
        .reduce(operations.Count('total_count'), [text_column])

    tf_doc = split_word \
        .sort([doc_column, text_column]) \
        .reduce(operations.CountFilterMin('doc_count', 2), [doc_column, text_column])

    return tf_doc \
        .join(operations.InnerJoiner(), count_total, [text_column], [text_column]) \
        .map(operations.CalculatePmi()) \
        .sort([doc_column]) \
        .reduce(operations.TopN('pmi', 10), [doc_column])


def yandex_maps_graph(input_stream_name_time: str, input_stream_name_length: str,
                      enter_time_column: str = 'enter_time', leave_time_column: str = 'leave_time',
                      edge_id_column: str = 'edge_id', start_coord_column: str = 'start', end_coord_column: str = 'end',
                      weekday_result_column: str = 'weekday', hour_result_column: str = 'hour',
                      speed_result_column: str = 'speed') -> Graph:
    """Constructs graph which measures average speed in km/h depending on the weekday and hour"""
    travel_data = Graph.graph_from_iter(input_stream_name_time) \
        .map(operations.ExtractTimeFeatures(enter_time_column)) \
        .map(operations.CalculateDuration())

    road_data = Graph.graph_from_file(input_stream_name_length,
                                     lambda: operations.read_from_file(input_stream_name_length)) \
        .map(operations.CalculateDistance())

    return travel_data \
        .join(operations.InnerJoiner(), road_data, [edge_id_column], [edge_id_column]) \
        .map(operations.CalculateSpeed()) \
        .sort([weekday_result_column, hour_result_column]) \
        .reduce(operations.AverageSpeed(), [weekday_result_column, hour_result_column])
