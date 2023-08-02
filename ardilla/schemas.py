"""
variables and functions here are used to generate and work with the Model's schemas
"""
import re
from typing import Optional, Union
from datetime import datetime, date, time
from pydantic import BaseModel, Json
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from .errors import ModelIntegrityError
from .types import FIELD_MAPPING, get_annotation_type


SCHEMA_TEMPLATE: str = "CREATE TABLE IF NOT EXISTS {tablename} (\n{fields}\n);"

SQLFieldType = Union[int, float, str, bool, datetime, bytes, date, time]

AUTOFIELDS = {
    int: " AUTOINCREMENT",
    datetime: " DEFAULT CURRENT_TIMESTAMP",
    date: " DEFAULT CURRENT_DATE",
    time: " DEFAULT CURRENT_TIME",
}


def get_tablename(model: type[BaseModel]) -> str:
    """returns the tablename of a model either from the attribute __tablenam__
    or from the lowercase model's name

    Args:
        model (type[BaseModel]): the model

    Returns:
        str: the name of the table
    """
    return getattr(model, "__tablename__", model.__name__.lower())


def make_field_schema(name: str, field: FieldInfo) -> dict:
    output = {}
    T = get_annotation_type(field.annotation)
    default = field.default if field.default is not PydanticUndefined else None
    extra = field.json_schema_extra or {}
    auto = output["auto"] = extra.get("auto")
    unique = output["unique"] = extra.get("unique")
    is_pk = False
    constraint = None

    if default and unique:
        raise ModelIntegrityError(
            f"field {name} has both unique and default constrains which are incompatible"
        )

    autoerror = ModelIntegrityError(
        f'field {name} has a type of "{T}" which does not support "auto"'
    )
    schema = f"{name} {FIELD_MAPPING[T]}"

    primary_field_keys = {"pk", "primary", "primary_key"}
    if len(extra.keys() & primary_field_keys) > 1:
        raise ModelIntegrityError(f'Multiple keywords for a primary field in "{name}"')

    for k in primary_field_keys:
        if k in extra and extra[k]:
            is_pk = True

            schema += " PRIMARY KEY"

            if auto and T in AUTOFIELDS:
                schema += AUTOFIELDS[T]
                field.default = None

            elif auto:
                raise autoerror

            break
    else:
        if auto and T in AUTOFIELDS.keys() - {int}:
            schema += AUTOFIELDS[T]
        elif auto:
            raise autoerror
        elif default is not None:
            if T in {int, str, float, bool}:
                schema += f" DEFAULT {default!r}"
            elif T in {datetime, date, time}:
                schema += f" DEFAULT {default}"
            elif T is bytes:
                schema += f" DEFAULT (X'{default.hex()}')"
        elif field.is_required():
            schema += " NOT NULL"
        if unique:
            schema += " UNIQUE"

    if extra.get("references"):
        references, fk, on_delete, on_update = (
            extra.get(f) for f in ["references", "fk", "on_delete", "on_update"]
        )
        constraint = (
            f"FOREIGN KEY ({name}) "
            f"REFERENCES {references}({fk}) "
            f"ON UPDATE {on_update} "
            f"ON DELETE {on_delete}"
        )

    output.update({"pk": is_pk, "schema": schema, "constraint": constraint})
    return output


def make_table_schema(Model: type[BaseModel]) -> str:
    tablename = get_tablename(Model)
    fields = []
    constrains = []
    pk = None
    for name, field in Model.model_fields.items():
        field_schema = make_field_schema(name, field)
        if field_schema["pk"] is True:
            if pk is not None:
                raise ModelIntegrityError(
                    f'field "{name}" is marked as primary but there is already a primary key field "{pk}"'
                )
            pk = name
        fields.append(field_schema["schema"])

        constrains.append(field_schema["constraint"]) if field_schema[
            "constraint"
        ] else None
    
    schema = (
        f"CREATE TABLE IF NOT EXISTS {tablename}(\n"
        + ",\n".join(f"\r    {f}" for f in (fields + constrains))
        + "\n);"
    )
    return schema


def get_pk(schema: str) -> Optional[str]:
    """Gets the primary key field name from the passed schema

    Args:
        schema (str): table schema

    Returns:
        Optional[str]: the name of the primary key if any
    """
    # Check if the schema contains a primary key definition
    if "PRIMARY KEY" in schema:
        # Use a regular expression to extract the primary key column name
        match = re.search(r"(?i)\b(\w+)\b\s+(?:\w+\s+)*PRIMARY\s+KEY", schema)
        if match:
            return match.group(1)
    return None
