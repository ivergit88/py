from datetime import datetime
from functools import wraps


def profiler(func):  # type: ignore
    """Measure execution time and recursive calls count for the last invocation."""

    call_depth = 0
    call_counter = 0
    start_time = datetime.now()

    @wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore
        nonlocal call_depth, call_counter, start_time
        is_outer_call = call_depth == 0
        if is_outer_call:
            call_counter = 0
            start_time = datetime.now()

        call_depth += 1
        call_counter += 1

        try:
            return func(*args, **kwargs)
        finally:
            call_depth -= 1
            if call_depth == 0:
                duration = datetime.now() - start_time
                wrapper.calls = call_counter
                wrapper.last_time_taken = duration.total_seconds()

    wrapper.calls = 0  # type: ignore[attr-defined]
    wrapper.last_time_taken = 0.0  # type: ignore[attr-defined]
    return wrapper
