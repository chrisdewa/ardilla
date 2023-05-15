"""
variables and functions here are used to generate and work with the Model's schemas
"""
import re
from datetime import datetime, date
from pydantic import BaseModel, Json
from .errors import ModelIntegrityError


SCHEMA_TEMPLATE: str = "CREATE TABLE IF NOT EXISTS {tablename} (\n{fields}\n);"


FIELD_MAPPING: dict[type, str] = {
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bytes: "BLOB",
    bool: "INTEGER",
    date: "DATE",
    datetime: "TIMESTAMP",
    Json: "TEXT",
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


def get_fields(model: type[BaseModel]) -> str:
    """Generates the fields for the table schema of the passed model

    Args:
        model (type[BaseModel]): the model

    Raises:
        TypeError: if the field is not listed in ardilla.schemas.FIELD_MAPPING
        ModelIntegrityError: if there's a Model field that is marked as pk but
            the model's __pk__ attr points to a different field

    Returns:
        str: a string containing the formatted fields to be added to a table schema
    """
    fields = []
    for field in model.__fields__.values():
        if field.type_ not in FIELD_MAPPING:
            raise TypeError(f'Unsupported/unrecognized sqlite type "{field.type_}"')
        type_ = FIELD_MAPPING[field.type_]

        extra = field.field_info.extra

        pk = getattr(model, "__pk__", None)

        field_is_pk = extra.get("primary") or extra.get("primary_key")

        if field_is_pk and pk and field.name != pk:
            raise ModelIntegrityError(
                f"field {field.name} is marked as pk, but __pk__ points to another field."
            )
        out = f"    {field.name} {type_}"
        if pk == field.name or field_is_pk:
            out += " PRIMARY KEY"
            if extra.get("autoincrement") or extra.get("auto"):
                out += " AUTOINCREMENT"
        if field.required and not "PRIMARY KEY" in out:
            out += " NOT NULL"
        if field.default is not None:
            out += f" DEFAULT {field.default!r}"

        fields.append(out)

    return ",\n".join(fields)


def make_schema(Model: type[BaseModel]) -> str:
    """Generates the schema from a model based on its field configuration

    Args:
        Model (type[BaseModel]): the model

    Returns:
        str: the generated schema
    """
    return SCHEMA_TEMPLATE.format(
        tablename=get_tablename(Model), fields=get_fields(Model)
    )


def get_pk(schema: str) -> str | None:
    """Gets the primary key field name from the passed schema

    Args:
        schema (str): table schema

    Returns:
        str | None: the name of the primary key if any
    """
    # Check if the schema contains a primary key definition
    if "PRIMARY KEY" in schema:
        # Use a regular expression to extract the primary key column name
        match = re.search(r"(?i)\b(\w+)\b\s+(?:\w+\s+)*PRIMARY\s+KEY", schema)
        if match:
            return match.group(1)
    return None
