# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import importlib
import operator
import random
import string
import sys
import typing
from collections.abc import Callable, Collection, Sequence
from functools import partial
from math import ceil

from . import (
    cache,
    checker,
    convert,
    hash,
    merge,
    sorting,
    splitter,
)

T = typing.TypeVar("T")

concat: typing.Callable[[typing.Any], str] = "".join


def operate(x):  # no cove
    return getattr(operator, x)


def is_generic(t: type):
    """Return True if type in the generic alias type."""
    return hasattr(t, "__origin__")


def not_generic(check: typing.Any, instance):
    if instance is typing.NoReturn:
        return check is None
    elif instance is typing.Any:
        return True
    return isinstance(check, instance)


def isinstance_check(check: typing.Any, instance) -> bool:
    """Return True if check data is instance.

    Examples:
        >>> import typing as t
        ... assert isinstance_check(['s', ], t.List[str])
        ... assert isinstance_check(('s', 't', ), t.Tuple[str, ...])
        ... assert not isinstance_check(('s', 't', ), t.Tuple[str])
        ... assert isinstance_check({'s': 1, 'd': 'r'}, t.Dict[
        ...     str, t.Union[int, str]]
        ... )
        ... assert isinstance_check('s', t.Optional[str])
        ... assert isinstance_check(1, t.Optional[t.Union[str, int]])
        ... assert not isinstance_check('s', t.List[str])
        ... assert isinstance_check([1, '2'], t.List[t.Union[str, int]])
        ... assert not isinstance_check('s', t.NoReturn)
        ... assert isinstance_check(None, t.NoReturn)
        ... assert isinstance_check('A', t.Any)
        ... assert isinstance_check([1, [1, 2, 3]], t.List[
        ...     t.Union[t.List[int], int]
        ... ])
    """
    if not is_generic(instance):
        return not_generic(check, instance)

    origin = typing.get_origin(instance)
    if origin == typing.Union:
        return any(
            isinstance_check(check, typ) for typ in typing.get_args(instance)
        )

    if not issubclass(check.__class__, origin):
        return False

    if origin == dict:
        _dict = typing.get_args(instance)
        return all(
            (isinstance_check(k, _dict[0]) and isinstance_check(v, _dict[1]))
            for k, v in check.items()
        )
    elif origin in {
        tuple,
        list,
    }:
        _dict = typing.get_args(instance)
        if Ellipsis in _dict or (origin is not tuple):
            return all(isinstance_check(i, _dict[0]) for i in iter(check))
        try:
            return all(
                isinstance_check(i[0], i[1])
                for i in merge.zip_equal(check, _dict)
            )
        except ValueError:
            return False
    elif origin is Callable:
        return callable(check)
    raise NotImplementedError("It can not check typing instance of this pair.")


def cached_import(module_path, class_name):
    """Cached import package"""
    modules = sys.modules
    if (
        module_path not in modules
        or getattr(modules[module_path], "__spec__", None) is not None
        and getattr(modules[module_path].__spec__, "_initializing", False)
    ):
        importlib.import_module(module_path)
    return getattr(modules[module_path], class_name)


def import_string(dotted_path: str):
    """Import a dotted module path and return the attribute/class designated by
    the last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError(
            f"{dotted_path} doesn't look like a module path"
        ) from err

    try:
        return cached_import(module_path, class_name)
    except AttributeError as err:
        raise ImportError(
            f'Module "{module_path}" does not define a "{class_name}" '
            f"attribute/class"
        ) from err


def lazy(module: str):
    """Lazy use import_string function that warpped with partial function."""
    return partial(import_string, module)


def round_up(number: float, decimals):
    """
    Examples:
        >>> round_up(1.00406, 2)
        1.01
        >>> round_up(1.00001, 1)
        1.1
    """
    assert isinstance(number, float)
    assert isinstance(decimals, int)
    assert decimals >= 0
    if decimals == 0:
        return ceil(number)
    factor = 10**decimals
    return ceil(number * factor) / factor


def remove_pad(value: str) -> str:
    """Remove zero padding of string
    Examples:
        >>> remove_pad('000')
        '0'
        >>> remove_pad('0123')
        '123'
        >>> remove_pad('0000123')
        '123'
    """
    return _last_char if (_last_char := value[-1]) == "0" else value.lstrip("0")


def first(iterable, default=None, condition=lambda x: True):
    """Returns the first item in the `iterable` that satisfies the `condition`.
    If the condition is not given, returns the first item of the iterable.

        If the `default` argument is given and the iterable is empty, or if it
    has no items matching the condition, the `default` argument is returned if
    it matches the condition.

    The `default` argument being None is the same as it not being given.

    Raises `StopIteration` if no item satisfying the condition is found
    and default is not given or doesn't satisfy the condition.

    Examples:
        >>> first( (1,2,3), condition=lambda _: _ % 2 == 0)
        2
        >>> first(range(3, 100))
        3
        >>> first( () )
        Traceback (most recent call last):
        ...
        StopIteration
        >>> first([], default=1)
        1
        >>> first([], default=1, condition=lambda _: _ % 2 == 0)
        Traceback (most recent call last):
        ...
        StopIteration
        >>> first([1,3,5], default=1, condition=lambda _: _ % 2 == 0)
        Traceback (most recent call last):
        ...
        StopIteration

    References: https://stackoverflow.com/questions/2361426/ -
            get-the-first-item-from-an-iterable-that-matches-a-condition
    """
    try:
        return next(x for x in iterable if condition(x))
    except StopIteration:
        if default is not None and condition(default):
            return default
        else:
            raise


def onlyone(
    check: Sequence[T],
    value: Sequence[T],
    *,
    default: bool = True,
) -> T | None:
    """Get only one element from check list that exists in match list.

    :param check: A sequence of value to check if it exists only one.
    :param value: A value that want to get only one value.
    :param default: A flag that use the first value of the value param if it
        does not exist any only one. Otherwise, it will return None.
    :type default: bool(=True)

    Examples:
        >>> onlyone(['a', 'b'], ['a', 'b', 'c'])
        'a'
        >>> onlyone(('a', 'b'), ['c', 'e', 'f'])
        'c'
        >>> onlyone(['a', 'b'], ['c', 'e', 'f'], default=False)

    """
    if isinstance(check, set) or isinstance(value, set):
        raise TypeError("The onlyone should able to fix position index type")
    if len(exist := set(check).intersection(set(value))) == 1:
        return list(exist)[0]
    return next(
        (_ for _ in value if _ in check),
        (value[0] if default else None),
    )


def hasdot(search: str, content: dict[typing.Any, typing.Any]) -> bool:
    """Return True value if dot searching exists in content data.

    Examples:
        >>> hasdot('data.value', {'data': {'value': 2}})
        True
        >>> hasdot('data.value.key', {'data': {'value': 2}})
        False
        >>> hasdot('item.value.key', {'data': {'value': 2}})
        False
    """
    _search, _else = splitter.must_split(search, ".", maxsplit=1)
    if _search in content and isinstance(content, dict):
        if not _else:
            return True
        elif isinstance((result := content[_search]), dict):
            return hasdot(_else, result)
    return False


def getdot(
    search: str,
    content: dict[typing.Any, typing.Any],
    *args,
    ignore: bool = False,
    **kwargs,
) -> typing.Any:
    """Return the value if dot searching exists in content data.

    Examples:
        >>> getdot('data.value', {'data': {'value': 1}})
        1
        >>> getdot('data', {'data': 'test'})
        'test'
        >>> getdot('data.value', {'data': 'test'})
        Traceback (most recent call last):
        ...
        ValueError: 'value' does not exists in test
        >>> getdot('data.value', {'data': {'key': 1}}, None)

        >>> getdot(
        ...     'data.value.getter',
        ...     {'data': {'value': {'getter': 'success', 'put': 'fail'}}},
        ... )
        'success'
        >>> getdot('foo.bar', {"foo": {"baz": 1}}, ignore=True)

        >>> getdot('foo.bar', {"foo": {"baz": 1}}, 2, 3)
        2
        >>> getdot('foo.bar', {"foo": {"baz": 1}}, 2, 3, ignore=True)
        2
    """
    # NOTE: Start search the first key.
    _search, _else = splitter.must_split(search, ".", maxsplit=1)

    if isinstance(content, dict):
        is_optional: bool = _search.endswith("?")
        _search: str = _search.rstrip("?")

        if _search in content:
            if not _else:
                return content[_search]
            if isinstance((sub_content := content[_search]), dict):
                return getdot(
                    _else, sub_content, *args, ignore=ignore, **kwargs
                )
            if ignore:
                return None
            raise ValueError(f"{_else!r} does not exists in {sub_content}")

        elif is_optional:
            return None

    if args:
        return args[0]
    elif ignore:
        return None
    raise ValueError(f"{_search!r} does not exists in {content}")


def setdot(search: str, content: dict, value: typing.Any, **kwargs) -> dict:
    """
    Examples:
        >>> setdot('data.value', {'data': {'value': 1}}, 2)
        {'data': {'value': 2}}
        >>> setdot('data.value.key', {'data': {'value': 1}}, 2, ignore=True)
        {'data': {'value': 1}}
    """
    _ignore: bool = kwargs.get("ignore", False)
    _search, _else = splitter.must_split(search, ".", maxsplit=1)
    if _search in content and isinstance(content, dict):
        if not _else:
            content[_search] = value
            return content
        if isinstance((result := content[_search]), dict):
            content[_search] = setdot(_else, result, value, **kwargs)
            return content
        if _ignore:
            return content
        raise ValueError(f"{_else!r} does not exists in {result}")
    if _ignore:
        return content
    raise ValueError(f"{_search} does not exists in {content}")


def filter_dict(
    value: T,
    included: Collection | None = None,
    excluded: Collection | None = None,
) -> T:
    """
    Examples:
        >>> filter_dict({"foo": "bar"}, included={}, excluded={"foo"})
        {}
        >>> filter_dict(
        ...     {"foo": 1, "bar": 2, "baz": 3},
        ...     included=("foo", )
        ... )
        {'foo': 1}
        >>> filter_dict(
        ...     {"foo": 1, "bar": 2, "baz": 3},
        ...     included=("foo", "bar", ),
        ...     excluded=("bar", )
        ... )
        {'foo': 1}
    """
    _exc: Collection = excluded or ()
    return dict(
        filter(
            lambda i: i[0]
            in (v for v in (included or value.keys()) if v not in _exc),
            value.items(),
        )
    )


def random_str(num_length: int = 8) -> str:  # no cov
    """Random string from uppercase ASCII and number 0-9"""
    return "".join(
        random.choices(string.ascii_uppercase + string.digits, k=num_length)
    )


def coalesce(value: typing.Any, default: typing.Any) -> typing.Any:  # no cove
    """Coalesce function that is a just naming define function."""
    return default if value is None else value
