import time
import threading
import multiprocessing


def very_slow_function(x: int) -> int:
    """Function which calculates square of given number really slowly
    :param x: given number
    :return: number ** 2
    """
    time.sleep(0.3)
    return x ** 2


def calc_squares_simple(bound: int) -> list[int]:
    """Function that calculates squares of numbers in range [0; bound)
    :param bound: positive upper bound for range
    :return: list of squared numbers
    """
    result = []
    for x in range(bound):
        result.append(very_slow_function(x))
    return result


def calc_squares_multithreading(bound: int) -> list[int]:
    """Function that calculates squares of numbers in range [0; bound)
    using threading.Thread
    :param bound: positive upper bound for range
    :return: list of squared numbers
    """
    result = []
    lock = threading.Lock()

    def worker(start, end):
        local_result = []
        for x in range(start, end):
            local_result.append(very_slow_function(x))
        with lock:
            result.extend(local_result)

    threads = []
    chunk_size = bound // 4  # Use 4 threads

    for i in range(0, bound, chunk_size):
        end = min(i + chunk_size, bound)
        thread = threading.Thread(target=worker, args=(i, end))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return result


def square_func(x):
    return very_slow_function(x)


def calc_squares_multiprocessing(bound: int) -> list[int]:
    """Function that calculates squares of numbers in range [0; bound)
    using multiprocessing.Pool
    :param bound: positive upper bound for range
    :return: list of squared numbers
    """
    with multiprocessing.Pool() as pool:
        return pool.map(square_func, range(bound))
