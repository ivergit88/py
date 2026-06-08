import builtins
import dis
import operator
import types
import typing as tp

CO_VARARGS = 0x04
CO_VARKEYWORDS = 0x08
CO_GENERATOR = 0x20

NULL = object()

BinaryFunc = tp.Callable[[tp.Any, tp.Any], tp.Any]

_BINARY_OPS: dict[int, BinaryFunc] = {
    0: operator.add,
    1: operator.and_,
    2: operator.floordiv,
    3: operator.lshift,
    4: operator.matmul,
    5: operator.mul,
    6: operator.mod,
    7: operator.or_,
    8: operator.pow,
    9: operator.rshift,
    10: operator.sub,
    11: operator.truediv,
    12: operator.xor,
    13: operator.iadd,
    14: operator.iand,
    15: operator.ifloordiv,
    16: operator.ilshift,
    17: operator.imatmul,
    18: operator.imul,
    19: operator.imod,
    20: operator.ior,
    21: operator.ipow,
    22: operator.irshift,
    23: operator.isub,
    24: operator.itruediv,
    25: operator.ixor,
}


class Cell:
    def __init__(self, value: tp.Any = None) -> None:
        self.value = value

    def get(self) -> tp.Any:
        return self.value

    def set(self, value: tp.Any) -> None:
        self.value = value


def _require_int_arg(instr: dis.Instruction) -> int:
    arg = instr.arg
    if arg is None:
        raise RuntimeError(f"{instr.opname} without arg")
    return arg


def _require_str_argval(instr: dis.Instruction) -> str:
    argval = instr.argval
    if not isinstance(argval, str):
        raise RuntimeError(f"{instr.opname} argval must be str")
    return argval


def _require_tuple_str_argval(instr: dis.Instruction) -> tuple[str, ...]:
    argval = instr.argval
    if not isinstance(argval, tuple) or not all(isinstance(x, str) for x in argval):
        raise RuntimeError(f"{instr.opname} argval must be tuple[str, ...]")
    return tp.cast(tuple[str, ...], argval)


def _is_true(x: tp.Any) -> bool:
    return bool(x)


def _cmp(op: str, a: tp.Any, b: tp.Any) -> bool:
    mapping: dict[str, tp.Callable[[tp.Any, tp.Any], bool]] = {
        "<": operator.lt,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        ">=": operator.ge,
    }
    if op not in mapping:
        raise NotImplementedError(f"COMPARE_OP {op!r} is not implemented")
    return mapping[op](a, b)


def _binary_op(arg: int, lhs: tp.Any, rhs: tp.Any) -> tp.Any:
    func = _BINARY_OPS.get(arg)
    if func is None:
        raise NotImplementedError(f"BINARY_OP {arg!r} is not implemented")
    return func(lhs, rhs)


class Function:
    def __init__(
        self,
        code: types.CodeType,
        globals_: dict[str, tp.Any],
        builtins_: dict[str, tp.Any],
        name: str | None = None,
        defaults: tuple[tp.Any, ...] = (),
        kwdefaults: dict[str, tp.Any] | None = None,
        closure: tuple[Cell, ...] = (),
    ) -> None:
        self.__code__ = code
        self.__globals__ = globals_
        self.__builtins__ = builtins_
        self.__name__ = name or code.co_name
        self.__qualname__ = self.__name__
        self.__defaults__ = defaults
        self.__kwdefaults__ = kwdefaults or {}
        self.__closure__ = closure

    def _bind_args(self, args: tuple[tp.Any, ...], kwargs: dict[str, tp.Any]) -> dict[str, tp.Any]:
        code = self.__code__
        varnames = code.co_varnames

        posonly = code.co_posonlyargcount
        total_pos = code.co_argcount
        kwonly = code.co_kwonlyargcount

        pos_names = list(varnames[:total_pos])
        kwonly_names = list(varnames[total_pos: total_pos + kwonly])

        idx = total_pos + kwonly
        vararg_name: str | None = None
        if code.co_flags & CO_VARARGS:
            vararg_name = varnames[idx]
            idx += 1

        varkw_name: str | None = None
        if code.co_flags & CO_VARKEYWORDS:
            varkw_name = varnames[idx]

        bound: dict[str, tp.Any] = {}

        if len(args) > total_pos and vararg_name is None:
            raise TypeError(f"{self.__name__}() takes {total_pos} positional arguments but {len(args)} were given")

        for name, value in zip(pos_names, args):
            bound[name] = value

        if vararg_name is not None:
            bound[vararg_name] = tuple(args[total_pos:])

        extra_kwargs: dict[str, tp.Any] = {}
        for key, value in kwargs.items():
            if key in bound:
                raise TypeError(f"{self.__name__}() got multiple values for argument {key!r}")

            if key in pos_names:
                if key in pos_names[:posonly]:
                    raise TypeError(f"{self.__name__}() got some positional-only arguments passed as keyword arguments")
                bound[key] = value
            elif key in kwonly_names:
                bound[key] = value
            elif varkw_name is not None:
                extra_kwargs[key] = value
            else:
                raise TypeError(f"{self.__name__}() got an unexpected keyword argument {key!r}")

        if varkw_name is not None:
            bound[varkw_name] = extra_kwargs

        defaults = self.__defaults__ or ()
        if defaults:
            first_default = total_pos - len(defaults)
            for i, value in enumerate(defaults, start=first_default):
                name = pos_names[i]
                if name not in bound:
                    bound[name] = value

        for name in pos_names:
            if name not in bound:
                raise TypeError(f"{self.__name__}() missing required positional argument: {name!r}")

        for name in kwonly_names:
            if name not in bound:
                if name in self.__kwdefaults__:
                    bound[name] = self.__kwdefaults__[name]
                else:
                    raise TypeError(f"{self.__name__}() missing required keyword-only argument: {name!r}")

        return bound

    def __call__(self, *args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        locals_ = self._bind_args(args, kwargs)
        frame = Frame(
            frame_code=self.__code__,
            frame_builtins=self.__builtins__,
            frame_globals=self.__globals__,
            frame_locals=locals_,
            closure=self.__closure__,
        )

        if self.__code__.co_flags & CO_GENERATOR:
            return Generator(frame)

        return frame.run()


class Generator:
    def __init__(self, frame: "Frame") -> None:
        self.frame = frame
        self.started = False
        self.finished = False
        if self.frame.instructions and self.frame.instructions[0].opname == "RETURN_GENERATOR":
            self.frame.instr_index = 1

    def __iter__(self) -> "Generator":
        return self

    def __next__(self) -> tp.Any:
        return self.send(None)

    def send(self, value: tp.Any) -> tp.Any:
        if self.finished:
            raise StopIteration

        if not self.started:
            self.started = True
            if value is not None:
                raise TypeError("can't send non-None value to a just-started generator")
        else:
            self.frame.push(value)

        result, yielded = self.frame.run_generator()
        if yielded:
            return result

        self.finished = True
        raise StopIteration(result)


class Frame:
    def __init__(
        self,
        frame_code: types.CodeType,
        frame_builtins: dict[str, tp.Any],
        frame_globals: dict[str, tp.Any],
        frame_locals: dict[str, tp.Any],
        closure: tuple[Cell, ...] = (),
    ) -> None:
        self.code = frame_code
        self.builtins = frame_builtins
        self.globals = frame_globals
        self.locals = frame_locals

        self.data_stack: list[tp.Any] = []
        self.return_value: tp.Any = None
        self.pending_kw_names: tuple[str, ...] | None = None

        self.instructions: list[dis.Instruction] = list(dis.get_instructions(self.code))
        self.offset_to_index: dict[int, int] = {instr.offset: i for i, instr in enumerate(self.instructions)}
        self.instr_index = 0
        self.jump_to: int | None = None

        self.cells: dict[str, Cell] = {}

        for name in self.code.co_cellvars:
            self.cells[name] = Cell(self.locals.get(name))

        for name, cell in zip(self.code.co_freevars, closure):
            self.cells[name] = cell

    def top(self) -> tp.Any:
        return self.data_stack[-1]

    def pop(self) -> tp.Any:
        return self.data_stack.pop()

    def push(self, *values: tp.Any) -> None:
        self.data_stack.extend(values)

    def popn(self, n: int) -> list[tp.Any]:
        if n <= 0:
            return []
        start = len(self.data_stack) - n
        values = self.data_stack[start:]
        del self.data_stack[start:]
        return values

    def jump(self, target_offset: int) -> None:
        self.jump_to = target_offset

    def load_name(self, name: str) -> tp.Any:
        if name in self.locals:
            return self.locals[name]
        if name in self.globals:
            return self.globals[name]
        if name in self.builtins:
            return self.builtins[name]
        raise NameError(name)

    def store_name(self, name: str, value: tp.Any) -> None:
        self.locals[name] = value
        if name in self.cells:
            self.cells[name].set(value)

    def run(self) -> tp.Any:
        result, _ = self._run()
        return result

    def run_generator(self) -> tuple[tp.Any, bool]:
        return self._run()

    def _run(self) -> tuple[tp.Any, bool]:
        while self.instr_index < len(self.instructions):
            instr = self.instructions[self.instr_index]
            self.instr_index += 1
            self.jump_to = None

            opname = instr.opname.lower() + "_op"
            handler = getattr(self, opname, None)
            if handler is None:
                raise NotImplementedError(f"Opcode {instr.opname} is not implemented")

            out = handler(instr)

            if out == "__yield__":
                return self.return_value, True

            if self.jump_to is not None:
                self.instr_index = self.offset_to_index[self.jump_to]

            if instr.opname == "RETURN_VALUE":
                return self.return_value, False

        return self.return_value, False

    def resume_op(self, instr: dis.Instruction) -> None:
        return None

    def nop_op(self, instr: dis.Instruction) -> None:
        return None

    def push_null_op(self, instr: dis.Instruction) -> None:
        self.push(NULL)

    def pop_top_op(self, instr: dis.Instruction) -> None:
        self.pop()

    def copy_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        self.push(self.data_stack[-arg])

    def swap_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        self.data_stack[-1], self.data_stack[-arg] = self.data_stack[-arg], self.data_stack[-1]

    def return_value_op(self, instr: dis.Instruction) -> None:
        self.return_value = self.pop()

    def return_generator_op(self, instr: dis.Instruction) -> None:
        return None

    def yield_value_op(self, instr: dis.Instruction) -> str:
        self.return_value = self.pop()
        return "__yield__"

    def load_const_op(self, instr: dis.Instruction) -> None:
        self.push(instr.argval)

    def load_name_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        self.push(self.load_name(name))

    def store_name_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        self.store_name(name, self.pop())

    def delete_name_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        del self.locals[name]

    def load_global_op(self, instr: dis.Instruction) -> None:
        arg = 0 if instr.arg is None else instr.arg
        name = _require_str_argval(instr)
        if arg & 1:
            self.push(NULL)
        if name in self.globals:
            self.push(self.globals[name])
        else:
            self.push(self.builtins[name])

    def store_global_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        self.globals[name] = self.pop()

    def delete_global_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        del self.globals[name]

    def load_fast_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        if name in self.cells:
            self.push(self.cells[name].get())
            return
        if name not in self.locals:
            raise UnboundLocalError(name)
        self.push(self.locals[name])

    def store_fast_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        self.store_name(name, self.pop())

    def delete_fast_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        del self.locals[name]

    def load_closure_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        self.push(self.cells[name])

    def make_cell_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        if name not in self.cells:
            self.cells[name] = Cell(self.locals.get(name))

    def load_deref_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        self.push(self.cells[name].get())

    def store_deref_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        self.cells[name].set(self.pop())

    def delete_deref_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        self.cells[name].set(None)

    def copy_free_vars_op(self, instr: dis.Instruction) -> None:
        return None

    def load_classderef_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        if name in self.locals:
            self.push(self.locals[name])
        else:
            self.push(self.cells[name].get())

    def unary_negative_op(self, instr: dis.Instruction) -> None:
        self.push(-self.pop())

    def unary_not_op(self, instr: dis.Instruction) -> None:
        self.push(not self.pop())

    def unary_invert_op(self, instr: dis.Instruction) -> None:
        self.push(~self.pop())

    def binary_op_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        rhs = self.pop()
        lhs = self.pop()
        self.push(_binary_op(arg, lhs, rhs))

    def compare_op_op(self, instr: dis.Instruction) -> None:
        op = instr.argval
        if not isinstance(op, str):
            raise RuntimeError("COMPARE_OP argval must be str")
        rhs = self.pop()
        lhs = self.pop()
        self.push(_cmp(op, lhs, rhs))

    def is_op_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        rhs = self.pop()
        lhs = self.pop()
        value = lhs is rhs
        if arg == 1:
            value = not value
        self.push(value)

    def contains_op_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        rhs = self.pop()
        lhs = self.pop()
        value = lhs in rhs
        if arg == 1:
            value = not value
        self.push(value)

    def jump_forward_op(self, instr: dis.Instruction) -> None:
        argval = instr.argval
        if not isinstance(argval, int):
            raise RuntimeError("JUMP_FORWARD argval must be int")
        self.jump(argval)

    def jump_backward_op(self, instr: dis.Instruction) -> None:
        argval = instr.argval
        if not isinstance(argval, int):
            raise RuntimeError("JUMP_BACKWARD argval must be int")
        self.jump(argval)

    def jump_backward_no_interrupt_op(self, instr: dis.Instruction) -> None:
        argval = instr.argval
        if not isinstance(argval, int):
            raise RuntimeError("JUMP_BACKWARD_NO_INTERRUPT argval must be int")
        self.jump(argval)

    def pop_jump_forward_if_false_op(self, instr: dis.Instruction) -> None:
        argval = instr.argval
        if not isinstance(argval, int):
            raise RuntimeError("POP_JUMP_FORWARD_IF_FALSE argval must be int")
        if not _is_true(self.pop()):
            self.jump(argval)

    def pop_jump_forward_if_true_op(self, instr: dis.Instruction) -> None:
        argval = instr.argval
        if not isinstance(argval, int):
            raise RuntimeError("POP_JUMP_FORWARD_IF_TRUE argval must be int")
        if _is_true(self.pop()):
            self.jump(argval)

    def pop_jump_backward_if_false_op(self, instr: dis.Instruction) -> None:
        argval = instr.argval
        if not isinstance(argval, int):
            raise RuntimeError("POP_JUMP_BACKWARD_IF_FALSE argval must be int")
        if not _is_true(self.pop()):
            self.jump(argval)

    def pop_jump_backward_if_true_op(self, instr: dis.Instruction) -> None:
        argval = instr.argval
        if not isinstance(argval, int):
            raise RuntimeError("POP_JUMP_BACKWARD_IF_TRUE argval must be int")
        if _is_true(self.pop()):
            self.jump(argval)

    def jump_if_false_or_pop_op(self, instr: dis.Instruction) -> None:
        argval = instr.argval
        if not isinstance(argval, int):
            raise RuntimeError("JUMP_IF_FALSE_OR_POP argval must be int")
        if not _is_true(self.top()):
            self.jump(argval)
        else:
            self.pop()

    def jump_if_true_or_pop_op(self, instr: dis.Instruction) -> None:
        argval = instr.argval
        if not isinstance(argval, int):
            raise RuntimeError("JUMP_IF_TRUE_OR_POP argval must be int")
        if _is_true(self.top()):
            self.jump(argval)
        else:
            self.pop()

    def get_iter_op(self, instr: dis.Instruction) -> None:
        self.push(iter(self.pop()))

    def for_iter_op(self, instr: dis.Instruction) -> None:
        argval = instr.argval
        if not isinstance(argval, int):
            raise RuntimeError("FOR_ITER argval must be int")
        it = self.top()
        try:
            self.push(next(it))
        except StopIteration:
            self.pop()
            self.jump(argval)

    def build_tuple_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        self.push(tuple(self.popn(arg)))

    def build_list_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        self.push(list(self.popn(arg)))

    def build_set_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        self.push(set(self.popn(arg)))

    def build_map_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        items = self.popn(2 * arg)
        d: dict[tp.Any, tp.Any] = {}
        for i in range(0, len(items), 2):
            d[items[i]] = items[i + 1]
        self.push(d)

    def build_const_key_map_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        keys_obj = self.pop()
        if not isinstance(keys_obj, tuple):
            raise RuntimeError("BUILD_CONST_KEY_MAP expects tuple keys")
        values = self.popn(arg)
        self.push(dict(zip(keys_obj, values)))

    def list_extend_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        seq = self.pop()
        target = self.data_stack[-arg]
        if not isinstance(target, list):
            raise RuntimeError("LIST_EXTEND target must be list")
        target.extend(seq)

    def set_update_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        seq = self.pop()
        target = self.data_stack[-arg]
        if not isinstance(target, set):
            raise RuntimeError("SET_UPDATE target must be set")
        target.update(seq)

    def dict_update_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        other = self.pop()
        target = self.data_stack[-arg]
        if not isinstance(target, dict):
            raise RuntimeError("DICT_UPDATE target must be dict")
        target.update(other)

    def dict_merge_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        other = self.pop()
        target = self.data_stack[-arg]
        if not isinstance(target, dict):
            raise RuntimeError("DICT_MERGE target must be dict")
        if not isinstance(other, dict):
            raise RuntimeError("DICT_MERGE source must be dict")
        for k, v in other.items():
            if k in target:
                raise TypeError(f"got multiple values for keyword argument {k!r}")
            target[k] = v

    def list_append_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        item = self.pop()
        target = self.data_stack[-arg]
        if not isinstance(target, list):
            raise RuntimeError("LIST_APPEND target must be list")
        target.append(item)

    def set_add_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        item = self.pop()
        target = self.data_stack[-arg]
        if not isinstance(target, set):
            raise RuntimeError("SET_ADD target must be set")
        target.add(item)

    def map_add_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        value = self.pop()
        key = self.pop()
        target = self.data_stack[-arg]
        if not isinstance(target, dict):
            raise RuntimeError("MAP_ADD target must be dict")
        target[key] = value

    def unpack_sequence_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        seq = list(self.pop())
        if len(seq) != arg:
            raise ValueError("unpack length mismatch")
        self.push(*seq)

    def unpack_ex_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        seq = list(self.pop())
        before = arg & 0xFF
        after = arg >> 8
        if len(seq) < before + after:
            raise ValueError("not enough values to unpack")
        middle = seq[before: len(seq) - after]
        tail = seq[len(seq) - after:] if after else []
        self.push(*seq[:before], middle, *tail)

    def build_slice_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        if arg == 2:
            end = self.pop()
            start = self.pop()
            self.push(slice(start, end))
        elif arg == 3:
            step = self.pop()
            end = self.pop()
            start = self.pop()
            self.push(slice(start, end, step))
        else:
            raise NotImplementedError("BUILD_SLICE arg must be 2 or 3")

    def binary_subscr_op(self, instr: dis.Instruction) -> None:
        key = self.pop()
        obj = self.pop()
        self.push(obj[key])

    def store_subscr_op(self, instr: dis.Instruction) -> None:
        key = self.pop()
        obj = self.pop()
        value = self.pop()
        obj[key] = value

    def delete_subscr_op(self, instr: dis.Instruction) -> None:
        key = self.pop()
        obj = self.pop()
        del obj[key]

    def load_attr_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        obj = self.pop()
        arg = 0 if instr.arg is None else instr.arg

        if arg & 1:
            attr = getattr(obj, name)
            if hasattr(attr, "__self__") and getattr(attr, "__self__", None) is obj:
                func = getattr(type(obj), name)
                self.push(func, obj)
            else:
                self.push(NULL, attr)
        else:
            self.push(getattr(obj, name))

    def store_attr_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        value = self.pop()
        obj = self.pop()
        setattr(obj, name, value)

    def delete_attr_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        obj = self.pop()
        delattr(obj, name)

    def build_string_op(self, instr: dis.Instruction) -> None:
        arg = _require_int_arg(instr)
        parts = self.popn(arg)
        self.push("".join(tp.cast(list[str], parts)))

    def format_value_op(self, instr: dis.Instruction) -> None:
        flags = 0 if instr.arg is None else instr.arg
        have_fmt = flags & 0x04
        fmt_spec = self.pop() if have_fmt else ""
        value = self.pop()

        conv = flags & 0x03
        if conv == 0x00:
            pass
        elif conv == 0x01:
            value = str(value)
        elif conv == 0x02:
            value = repr(value)
        elif conv == 0x03:
            value = ascii(value)

        self.push(format(value, fmt_spec))

    def kw_names_op(self, instr: dis.Instruction) -> None:
        self.pending_kw_names = _require_tuple_str_argval(instr)

    def precall_op(self, instr: dis.Instruction) -> None:
        return None

    def call_op(self, instr: dis.Instruction) -> None:
        argc = 0 if instr.arg is None else instr.arg
        args = self.popn(argc)
        func = self.pop()
        maybe_null_or_self = self.pop()

        kwargs: dict[str, tp.Any] = {}
        if self.pending_kw_names is not None:
            kwnames = self.pending_kw_names
            nkw = len(kwnames)
            kwvalues = args[-nkw:] if nkw else []
            posargs = args[:-nkw] if nkw else args
            kwargs = dict(zip(kwnames, kwvalues))
            args = posargs
            self.pending_kw_names = None

        if maybe_null_or_self is not NULL:
            args = [maybe_null_or_self, *args]

        self.push(func(*args, **kwargs))

    def call_function_ex_op(self, instr: dis.Instruction) -> None:
        flags = 0 if instr.arg is None else instr.arg
        if flags & 0x01:
            kwargs_obj = self.pop()
            if not isinstance(kwargs_obj, dict):
                raise RuntimeError("CALL_FUNCTION_EX kwargs must be dict")
            kwargs = kwargs_obj
        else:
            kwargs = {}
        args_obj = self.pop()
        func = self.pop()
        self.push(func(*tuple(args_obj), **kwargs))

    def make_function_op(self, instr: dis.Instruction) -> None:
        flags = 0 if instr.arg is None else instr.arg

        closure: tuple[Cell, ...] = ()
        kwdefaults: dict[str, tp.Any] | None = None
        defaults: tuple[tp.Any, ...] = ()

        if flags & 0x08:
            raw_closure = self.pop()
            if not isinstance(raw_closure, tuple):
                raise RuntimeError("closure must be tuple")
            closure = tp.cast(tuple[Cell, ...], raw_closure)

        if flags & 0x04:
            _ = self.pop()

        if flags & 0x02:
            raw_kwdefaults = self.pop()
            if not isinstance(raw_kwdefaults, dict):
                raise RuntimeError("kwdefaults must be dict")
            kwdefaults = tp.cast(dict[str, tp.Any], raw_kwdefaults)

        if flags & 0x01:
            raw_defaults = self.pop()
            if not isinstance(raw_defaults, tuple):
                raise RuntimeError("defaults must be tuple")
            defaults = tp.cast(tuple[tp.Any, ...], raw_defaults)

        code_obj = self.pop()
        if not isinstance(code_obj, types.CodeType):
            raise RuntimeError("MAKE_FUNCTION expects code object")

        fn = Function(
            code=code_obj,
            globals_=self.globals,
            builtins_=self.builtins,
            name=code_obj.co_name,
            defaults=defaults,
            kwdefaults=kwdefaults,
            closure=closure,
        )
        self.push(fn)

    def load_build_class_op(self, instr: dis.Instruction) -> None:
        self.push(builtins.__build_class__)

    def import_name_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        fromlist = self.pop()
        level = self.pop()
        self.push(builtins.__import__(name, self.globals, self.locals, fromlist, level))

    def import_from_op(self, instr: dis.Instruction) -> None:
        name = _require_str_argval(instr)
        mod = self.top()
        self.push(getattr(mod, name))

    def import_star_op(self, instr: dis.Instruction) -> None:
        mod = self.pop()
        for name in dir(mod):
            if not name.startswith("_"):
                self.locals[name] = getattr(mod, name)

    def load_assertion_error_op(self, instr: dis.Instruction) -> None:
        self.push(AssertionError)

    def raise_varargs_op(self, instr: dis.Instruction) -> None:
        argc = 0 if instr.arg is None else instr.arg
        if argc == 0:
            raise
        if argc == 1:
            exc = self.pop()
            raise exc
        if argc == 2:
            cause = self.pop()
            exc = self.pop()
            raise exc from cause
        raise NotImplementedError("RAISE_VARARGS > 2 not supported")


class VirtualMachine:
    def run(self, code_obj: types.CodeType) -> tp.Any:
        globals_context: dict[str, tp.Any] = {}
        builtins_context: dict[str, tp.Any] = builtins.__dict__

        frame = Frame(
            frame_code=code_obj,
            frame_builtins=builtins_context,
            frame_globals=globals_context,
            frame_locals=globals_context,
        )
        return frame.run()
