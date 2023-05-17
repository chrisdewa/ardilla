"""
variables and functions here are used to generate and work with the Model's schemas
"""
import re
from sqlite3 import Binary
from datetime import datetime, date, time
from pydantic import BaseModel, Json
from .errors import ModelIntegrityError


SCHEMA_TEMPLATE: str = "CREATE TABLE IF NOT EXISTS {tablename} (\n{fields}\n);"


FIELD_MAPPING: dict[type, str] = {
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bool: "INTEGER",
    datetime: "DATETIME",
    bytes: "BLOB",
    date: "DATE",
    time: "TIME",
    Json: "TEXT",
}

AUTOFIELDS = {
    int: " AUTOINCREMENT",
    datetime: " DEFAULT CURRENT_TIMESTAMP",
    date: " DEFAULT CURRENT_DATE",
    time: " DEFAULT CURRENT_TIME"
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


def get_fields_schemas(Model: type[BaseModel]) -> list[str]:
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
    schemas = []
    pk = None
    for field in Model.__fields__.values():
        name = field.name
        T = field.type_
        default = field.default
        extra = field.field_info.extra
        auto = extra.get('auto')
        autoerror = ModelIntegrityError(f'field {name} has a type of "{T}" which does not support "auto"')
        schema = f'{name} {FIELD_MAPPING[T]}'
        for k in {'pk', 'primary', 'primary_key'}:
            if k in extra and extra[k]:
                if pk is not None:
                    raise ModelIntegrityError('Only one primary key per model is allowed')
                elif hasattr(Model, '__pk__') and Model.__pk__ != name:
                    raise ModelIntegrityError(f"field {name} is marked as pk, but __pk__ points to another field.")
                
                pk = name
                schema += ' PRIMARY KEY'

                if auto and T in AUTOFIELDS:
                    schema += AUTOFIELDS[T]
                elif auto:
                    raise autoerror
                break
        else:
            if auto and T in AUTOFIELDS.keys() - {int}:
                schema += AUTOFIELDS[T]
            elif auto:
                raise autoerror
            elif default:
                if T in {int, str, float, bool}:
                    schema += f' DEFAULT {default!r}'
                elif T in {datetime, date, time}:
                    schema += f' DEFAULT {default}'
                elif T in {bytes}:
                    schema += f" DEFAULT (X'{default.hex()}')"
            elif field.required:
                    schema += ' NOT NULL'
                    
        schemas.append(schema)

    return schemas


def make_table_schema(Model: type[BaseModel]) -> str:
    """Generates the schema from a model based on its field configuration

    Args:
        Model (type[BaseModel]): the model

    Returns:
        str: the generated schema
    """
    tablename = get_tablename(Model)
    fields = get_fields_schemas(Model)
    schema = (
        f'CREATE TABLE IF NOT EXISTS {tablename}(\n' +
        ',\n'.join(f'    {f}' for f in fields) +
        '\n);'
    )
    return schema


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
