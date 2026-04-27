
import sys
from datetime import date, datetime, time
import types
import typing


FIELD_MAPPING: dict[type, str] = {
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bool: "INTEGER",
    datetime: "DATETIME",
    bytes: "BLOB",
    date: "DATE",
    time: "TIME",
}

# types.UnionType (the type of `X | Y`) exists only on Python 3.10+
_UNION_TYPES: set = {typing.Union}
if sys.version_info >= (3, 10):
    _UNION_TYPES.add(types.UnionType)


def is_nullable(annotation) -> bool:
    """Returns True if the annotation allows None (i.e. Optional[T] or T | None)."""
    origin = typing.get_origin(annotation)
    if origin in _UNION_TYPES:
        return type(None) in typing.get_args(annotation)
    return False


def get_annotation_type(annotation) -> type | None:
    origin = typing.get_origin(annotation)
    if origin is not None:
        if origin in _UNION_TYPES:
            args = typing.get_args(annotation)
            for arg in args:
                if arg is not type(None):
                    return arg
            return None
        return origin
    return annotation

def check_type_annotation(annotation) -> bool:
    type_ = get_annotation_type(annotation)
    return type_ in FIELD_MAPPING
