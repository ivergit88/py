import dis
import types


def count_operations(source_code: types.CodeType) -> dict[str, int]:
    result: dict[str, int] = {}

    def walk(code: types.CodeType) -> None:
        for instr in dis.get_instructions(code):
            result[instr.opname] = result.get(instr.opname, 0) + 1
            if isinstance(instr.argval, types.CodeType):
                walk(instr.argval)

    walk(source_code)
    return result
