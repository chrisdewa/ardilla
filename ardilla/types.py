

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

def get_annotation_type(annotation) -> type | None:
    origin = typing.get_origin(annotation)
    if origin is not None:
        if origin in {typing.Union, types.UnionType}:
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
