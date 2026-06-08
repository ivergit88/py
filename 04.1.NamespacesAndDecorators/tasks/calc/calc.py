import sys
import math
from typing import Any

PROMPT = '>>> '


def run_calc(context: dict[str, Any] | None = None) -> None:
    """Run interactive calculator session in specified namespace"""
    namespace: dict[str, Any] = dict(context) if context is not None else {}
    namespace['__builtins__'] = {}
    for line in sys.stdin:
        line = line.rstrip('\n')
        if not line:
            print(PROMPT)
            continue
        result = eval(line, namespace)
        print(f"{PROMPT}{result}")
    print(PROMPT)

if __name__ == '__main__':
    context = {'math': math}
    run_calc(context)
