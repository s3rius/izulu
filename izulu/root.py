import copy
import enum
import functools
import typing as t

from izulu import _utils


class CheckFlags(enum.Flag):
    MISSING_FIELDS = enum.auto()
    UNDECLARED_FIELDS = enum.auto()

    DEFAULT = MISSING_FIELDS | UNDECLARED_FIELDS


class Error(Exception):
    _template_ = "Unknown exception"
    _checks_ = CheckFlags.DEFAULT

    __fields = __hints = frozenset()  # type: ignore[var-annotated]
    __registered = __defaults = frozenset()  # type: ignore[var-annotated]

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.__fields = frozenset(_utils.extract_fields(cls._template_))
        cls.__hints = frozenset(t.get_type_hints(cls))
        cls.__registered = cls.__hints | cls.__fields
        cls.__defaults = frozenset(attr for attr in cls.__hints
                                   if hasattr(cls, attr))

    def __init__(self, **kwargs: t.Any) -> None:
        self.__kwargs = kwargs
        self.__validate_kwargs(self.__kwargs)
        self.__set_attrs(self.__kwargs)
        # evaluate factories with *enriched* `.get_kwargs()`
        self.__msg = self._template_.format(**self.get_kwargs(True))
        super().__init__(self.__msg)

    def __validate_kwargs(self, kwargs: dict[str, t.Any]) -> None:
        if not self._checks_:
            return

        kws = frozenset(kwargs)
        if CheckFlags.MISSING_FIELDS in self._checks_:
            if missing := (self.__registered - self.__defaults - kws):
                raise TypeError(f"Missing arguments: {_utils.join(missing)}")

        if CheckFlags.UNDECLARED_FIELDS in self._checks_:
            if undeclared := (kws - self.__registered):
                msg = f"Undeclared arguments: {_utils.join(undeclared)}"
                raise TypeError(msg)

    def __set_attrs(self, kwargs: dict[str, t.Any]) -> None:
        for k, v in kwargs.items():
            if k in self.__hints:
                setattr(self, k, v)

    def __repr__(self) -> str:
        kwargs = _utils.join_kwargs(**self.get_kwargs(True))
        return f"{type(self).__name__}({kwargs})"

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.__msg}"

    def __copy__(self):
        return type(self)(**self.get_kwargs(True))

    def __deepcopy__(self, memo):
        if self not in memo:
            memo[self] = type(self)(**{k: copy.deepcopy(v)
                                       for k, v in self.get_kwargs(True)})
        return memo[self]

    def __reduce__(self):
        parent = list(super().__reduce__())
        parent[1] = tuple()
        return tuple(parent)

    def get_message(self) -> str:
        return self.__msg

    def get_kwargs(self, enriched: bool = False) -> dict[str, t.Any]:
        kwargs = self.__kwargs.copy()
        if enriched:
            for field in self.__defaults:
                kwargs.setdefault(field, getattr(self, field))
        return kwargs


def factory(func, self: bool = False) -> functools.cached_property:
    target = func if self else (lambda obj: func())
    return functools.cached_property(target)
