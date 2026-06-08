import enum


class Status(enum.Enum):
    NEW = 0
    IN_PROGRESS = 1
    FINISHED = 2


def extract_alphabet(
        graph: dict[str, set[str]]
        ) -> list[str]:
    """
    Extract alphabet from graph
    :param graph: graph with partial order
    :return: alphabet
    """
    status: dict[str, Status] = {node: Status.NEW for node in graph}
    result: list[str] = []

    def dfs(node: str) -> None:
        if status[node] is Status.FINISHED:
            return
        if status[node] is Status.IN_PROGRESS:
            raise ValueError("Cycle detected in graph")

        status[node] = Status.IN_PROGRESS
        for neighbor in graph[node]:
            dfs(neighbor)
        status[node] = Status.FINISHED
        result.append(node)

    for node in graph:
        if status[node] is Status.NEW:
            dfs(node)

    return result[::-1]


def build_graph(
        words: list[str]
        ) -> dict[str, set[str]]:
    """
    Build graph from ordered words. Graph should contain all letters from words
    :param words: ordered words
    :return: graph
    """
    graph = {}

    for word in words:
        for char in word:
            if char not in graph:
                graph[char] = set()

    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        for c1, c2 in zip(w1, w2):
            if c1 != c2:
                graph[c1].add(c2)
                break

    return graph


#########################
# Don't change this code
#########################

def get_alphabet(
        words: list[str]
        ) -> list[str]:
    """
    Extract alphabet from sorted words
    :param words: sorted words
    :return: alphabet
    """
    graph = build_graph(words)
    return extract_alphabet(graph)

#########################
