import heapq
import string


def normalize(
        text: str
        ) -> str:
    """
    Removes punctuation and digits and convert to lower case
    :param text: text to normalize
    :return: normalized query
    """
    return ''.join(c.lower() for c in text if c not in string.punctuation and not c.isdigit())


def get_words(
        query: str
        ) -> list[str]:
    """
    Split by words and leave only words with letters greater than 3
    :param query: query to split
    :return: filtered and split query by words
    """
    words = query.split()
    return [w for w in words if len(w) > 3]


def build_index(
        banners: list[str]
        ) -> dict[str, list[int]]:
    """
    Create index from words to banners ids with preserving order and without repetitions
    :param banners: list of banners for indexation
    :return: mapping from word to banners ids
    """
    index = {}
    for i, banner in enumerate(banners):
        normalized = normalize(banner)
        words = get_words(normalized)
        seen = set()
        for word in words:
            if word not in index:
                index[word] = []
            if word not in seen:
                index[word].append(i)
                seen.add(word)
    return index


def get_banner_indices_by_query(
        query: str,
        index: dict[str, list[int]]
        ) -> list[int]:
    """
    Extract banners indices from index, if all words from query contains in indexed banner
    :param query: query to find banners
    :param index: index to search banners
    :return: list of indices of suitable banners
    """
    normalized = normalize(query)
    words = get_words(normalized)

    if not words:
        return []

    lists = []
    for word in words:
        if word not in index:
            return []
        lists.append(index[word])

    k = len(lists)
    heap = []

    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], i, 0))

    result: list[int] = []
    current_val: int | None = None
    current_count = 0

    while heap:
        val, list_idx, elem_idx = heapq.heappop(heap)

        if val != current_val:
            if current_count == k and current_val is not None:
                result.append(current_val)
            current_val = val
            current_count = 1
        else:
            current_count += 1

        if elem_idx + 1 < len(lists[list_idx]):
            heapq.heappush(heap, (lists[list_idx][elem_idx + 1], list_idx, elem_idx + 1))

    if current_count == k and current_val is not None:
        result.append(current_val)

    return result


#########################
# Don't change this code
#########################

def get_banners(
        query: str,
        index: dict[str, list[int]],
        banners: list[str]
        ) -> list[str]:
    """
    Extract banners matched to queries
    :param query: query to match
    :param index: word-banner_ids index
    :param banners: list of banners
    :return: list of matched banners
    """
    indices = get_banner_indices_by_query(query, index)
    return [banners[i] for i in indices]

#########################
