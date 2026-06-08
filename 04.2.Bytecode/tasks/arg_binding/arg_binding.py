from types import FunctionType
from typing import Any

CO_VARARGS = 4
CO_VARKEYWORDS = 8

ERR_TOO_MANY_POS_ARGS = 'Too many positional arguments'
ERR_TOO_MANY_KW_ARGS = 'Too many keyword arguments'
ERR_MULT_VALUES_FOR_ARG = 'Multiple values for arguments'
ERR_MISSING_POS_ARGS = 'Missing positional arguments'
ERR_MISSING_KWONLY_ARGS = 'Missing keyword-only arguments'
ERR_POSONLY_PASSED_AS_KW = 'Positional-only argument passed as keyword argument'


def bind_args(func: FunctionType, *args: Any, **kwargs: Any) -> dict[str, Any]:
    code = func.__code__

    posonly_count = code.co_posonlyargcount
    total_pos_count = code.co_argcount
    kwonly_count = code.co_kwonlyargcount

    has_varargs = bool(code.co_flags & CO_VARARGS)
    has_varkw = bool(code.co_flags & CO_VARKEYWORDS)

    varnames = code.co_varnames

    posonly_names = list(varnames[:posonly_count])
    pos_or_kw_names = list(varnames[posonly_count:total_pos_count])
    kwonly_names = list(varnames[total_pos_count:total_pos_count + kwonly_count])

    idx = total_pos_count + kwonly_count

    varargs_name = None
    if has_varargs:
        varargs_name = varnames[idx]
        idx += 1

    varkw_name = None
    if has_varkw:
        varkw_name = varnames[idx]

    positional_names = posonly_names + pos_or_kw_names

    bound: dict[str, Any] = {}
    extra_kwargs: dict[str, Any] = {}

    if len(args) > total_pos_count and not has_varargs:
        raise TypeError(ERR_TOO_MANY_POS_ARGS)

    for i, value in enumerate(args[:total_pos_count]):
        bound[positional_names[i]] = value

    if has_varargs and varargs_name is not None:
        bound[varargs_name] = tuple(args[total_pos_count:])

    for key, value in kwargs.items():
        if key in posonly_names:
            if has_varkw:
                extra_kwargs[key] = value
            else:
                raise TypeError(ERR_POSONLY_PASSED_AS_KW)
        elif key in pos_or_kw_names or key in kwonly_names:
            if key in bound:
                raise TypeError(ERR_MULT_VALUES_FOR_ARG)
            bound[key] = value
        else:
            if has_varkw:
                extra_kwargs[key] = value
            else:
                raise TypeError(ERR_TOO_MANY_KW_ARGS)

    defaults = func.__defaults__ or ()
    defaults_start = len(positional_names) - len(defaults)

    for i, name in enumerate(positional_names):
        if name not in bound:
            if i >= defaults_start:
                bound[name] = defaults[i - defaults_start]
            else:
                raise TypeError(ERR_MISSING_POS_ARGS)

    kwdefaults = func.__kwdefaults__ or {}
    for name in kwonly_names:
        if name not in bound:
            if name in kwdefaults:
                bound[name] = kwdefaults[name]
            else:
                raise TypeError(ERR_MISSING_KWONLY_ARGS)

    if has_varkw and varkw_name is not None:
        bound[varkw_name] = extra_kwargs

    return bound
